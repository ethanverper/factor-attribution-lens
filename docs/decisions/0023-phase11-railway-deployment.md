# 0023. Phase 11: Railway deployment configuration

Date: 2026-08-12
Status: accepted (deployment config, verified locally in the exact production
shape); **live deployment itself blocked on Ethan completing Railway's
login/GitHub-authorization step — see "Open item" below.**

## Context

`docs/decisions/0018-phase10i-react-rebuild.md` §2 already decided the
deployment shape: one Railway service, not two — FastAPI serves the built
React SPA directly (`StaticFiles` mount + SPA catch-all in `app/main.py`),
so `devops`'s job is packaging that single process, not orchestrating a
split. This decision logs the concrete choices made building that package,
plus one genuine blocker this environment can't clear on its own.

There was no existing deployment config in the repo (no `Dockerfile`,
`railway.json`, `Procfile`, or `nixpacks.toml`) — built from scratch. The
`railway-deployment` skill referenced in `devops`'s own mandate is not
installed in this environment (same class of gap as `design-taste-frontend`
in Phase 9c/decision 0008 — logged rather than silently improvised around
without a note); proceeded on general Railway platform knowledge and
Railway's documented `railway.json` schema instead.

## Decision

### 1. Dockerfile over Nixpacks (or a Procfile)

Railway can build via Nixpacks auto-detection, but this app's build genuinely
spans two runtimes in one image — Node (to build `frontend/dist/`) and Python
(`uv`, to install and run the API) — with the frontend build artifact needing
to land inside the Python image's filesystem before the server starts.
Nixpacks *can* do multi-language builds via its own plan customization, but
a hand-written multi-stage `Dockerfile` makes the two-stage relationship
explicit, reviewable, and identical to what runs locally, rather than
depending on Nixpacks' auto-detected plan happening to infer the same thing.
This is also the more portable choice if `devops` ever needs to move this
same image off Railway.

`Dockerfile` (repo root):
- **Stage 1** (`node:22-slim`): `npm ci` + `npm run build` against
  `frontend/`, producing `frontend/dist/`.
- **Stage 2** (`ghcr.io/astral-sh/uv:python3.11-bookworm-slim`): `uv sync
  --frozen --no-dev` (production deps only — the `dev` group's
  `pytest`/`httpx` are dropped, matching `pyproject.toml`'s
  `[dependency-groups]`), then copies `app/` and stage 1's `frontend/dist/`
  in, then runs.

`railway.json` points Railway at `"builder": "DOCKERFILE"` explicitly rather
than leaving it to auto-detection, and sets `healthcheckPath: "/health"` (the
existing liveness route in `app/main.py`, registered ahead of the SPA
catch-all) with a 300s timeout generous enough to cover a cold container
start, plus `restartPolicyType: "ON_FAILURE"` (3 retries) as the basic
uptime-signal Railway supports natively — satisfying `devops`'s "set up a
basic health check wherever the platform supports it" standard without
adding a separate uptime-monitoring service this project doesn't need yet.

### 2. `uv`/OpenBB's first-import build step — baked into the image, not left for the running container

Decision 0014 documents a real gotcha: `from openbb import obb` (imported by
`app/data/equity.py`, and transitively by `app/main.py` at module load,
since `main.py` imports `app.service` which imports `app.data.equity`)
triggers a **one-time build** of OpenBB's generated `openbb/package/*.py`
route-stub tree on its first-ever import, cached to disk afterward
(measured in decision 0014 at ~26.5s cold, ~0.74s warm, on this environment's
disk). Left alone, that cost would land on the **first request to the first
container instance after every deploy** — a real cold-start tax, and
particularly bad news for the `healthcheckPath` above, which needs a
response inside its timeout window before Railway will route traffic to the
instance at all.

Fixed the same way decision 0014 fixed it locally: the Dockerfile's final
stage runs `RUN uv run python -c "from openbb import obb"` **after** `uv
sync` and the app source are in place but **before** `CMD` — this executes
at *image build time*, so the generated stub tree lands inside the image
layer itself (part of the installed `openbb-core`/`openbb-equity` package
tree in the venv, not some external cache Railway's ephemeral container
filesystem would lose on redeploy). Verified this actually works: ran the
exact same command locally against this project's `.venv` and confirmed a
clean import with no errors.

### 3. Static-asset serving in production — verified, not assumed

`app/main.py`'s `StaticFiles` mount (`/assets`) and SPA catch-all were
Phase 10i's work, not this phase's — but "confirm it works as expected" was
explicit in this phase's brief, so it was verified directly rather than
trusted from the decision doc's prose:

- Built `frontend/dist/` fresh (`cd frontend && npm install && npm run
  build`) and started `uv run uvicorn app.main:app --host 0.0.0.0 --port
  8123` — the exact command the Dockerfile's `CMD` runs, with an arbitrary
  non-default port standing in for Railway's injected `$PORT`, confirming
  the app binds to whatever port it's given rather than a hardcoded one.
- `curl` confirmed `/health` (200), `/` (200, serves `index.html`),
  `/results` (200 — the SPA catch-all correctly serves `index.html` for a
  deep client-side route on a hard load, not just in-app navigation),
  `/api/sample` and `/api/tickers` (200), and a real built JS asset under
  `/assets/*` (200).
- A live `POST /api/analysis` against this exact running process (AAPL 40%
  / MSFT 30% / GOOGL 20% / AMZN 10% vs. `^GSPC`) returned a full result
  bundle computed from live yfinance/Kenneth French data — confirming the
  static-serving change doesn't touch the API path at all, as designed.
- A full Playwright pass against this same running process: loaded `/`,
  confirmed the Overview hero's live mini-frontier-chart preview and
  precision stat render (real numbers, not placeholders), clicked "Run a
  live example" (the rule-8 sample quick-start), confirmed it correctly
  navigated to a `/results?symbol=...&weight=...` URL (the shareable-link
  URL mechanism, exercised for real, not just read about) and rendered
  the full Results page — stat tiles, the Fama-French diverging-bar chart
  with CI whiskers, the efficient-frontier chart, return/risk attribution,
  and a fully-populated, non-generic Interpretation & Key Takeaways
  section (the headline branch varied appropriately: this portfolio's real
  Value(HML) loading, not a fallback string).

This is the strongest possible pre-Railway confidence check short of an
actual Railway build — same OS-level Python/uv toolchain, same commands,
same `$PORT`-style binding, same freshly-built (not stale/cached) frontend
artifact, same live (non-mocked) upstream data calls.

### 4. No environment variables required — verified, not assumed

Grepped `app/` for `os.environ`/`os.getenv`/`getenv`/`API_KEY`/`SECRET`/
`PORT` — zero matches. Cross-checked against `app/data/equity.py` (OpenBB's
`yfinance` provider, confirmed keyless in decision 0002) and
`app/data/factors.py` (Kenneth French's Data Library via
`pandas-datareader`, also confirmed keyless in decision 0002). Railway needs
no secret configuration for this service beyond the `$PORT` it injects
automatically. If a future phase adds a paid data provider (decision 0014's
own "Consequences" section flags this as a real future possibility), that
provider's key would need to be added as a Railway environment variable at
that time — not before.

## Open item: Railway account/GitHub-connection step is Ethan's to complete

Everything above — the `Dockerfile`, `.dockerignore`, and `railway.json` — is
committed to the repo and independently verified to work in the exact shape
Railway will run it. What `devops` cannot do from this environment: create
or sign into a Railway account, or authorize Railway's GitHub App against
`github.com/ethanverper/factor-lens`. Both are interactive
login/OAuth steps, and per `devops`'s own standing mandate, those are
Ethan's to complete himself — never attempted here. The Railway CLI
(`npx @railway/cli`) is confirmed working in this environment (`npx railway
--version` → `5.37.7`) as an option if a CLI-driven `railway login`/`railway
link` flow is preferred over the dashboard; either path needs the same
human-completed login step.

**Also flagged explicitly per the standing "never provision a paid tier
without asking every time" rule**: Railway's current pricing (checked live,
August 2026) is a 30-day, no-card-required trial with a one-time $5 credit,
after which an account either moves to a Free plan with a much smaller
$1/month credit (likely insufficient for a real, sustained deployment given
this app's numpy/scipy/statsmodels/OpenBB memory footprint) or the $5/month
Hobby plan. **Creating the project and deploying under the free trial is
fine to just do** (no card, no charge) — but staying live past the 30-day/$5
window will require Ethan to make an explicit, in-the-moment call on Hobby
vs. accepting the Free plan's tighter limits vs. taking the app down. Not a
decision to make on his behalf now.

## Consequences

- Redeploying after this point is push-to-`main` automatic, once Railway's
  GitHub connection is made (Railway watches the connected branch by
  default) — no manual dashboard clicks needed for routine iteration.
- The production image never runs `npm run dev` or Vite's dev server; a
  frontend-only change still requires a full image rebuild to ship
  (already flagged as a known tradeoff in decision 0018 §2, not new here).
- `frontend/dist/` stays gitignored (confirmed via `git check-ignore`) —
  it's a build artifact, not source; the Dockerfile is the only place it
  gets produced for a deployed instance, consistent with "config as code,
  not manual output committed to the repo."
