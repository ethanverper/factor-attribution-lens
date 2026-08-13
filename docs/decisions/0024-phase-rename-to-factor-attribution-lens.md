# 0024. Rename project from "Factor Lens" to "Factor Attribution Lens"

Date: 2026-08-12
Status: accepted

## Context

Ethan requested this rename directly: "Factor Lens" read as too generic and
didn't communicate what the product actually does. The team's naming
standard calls for names descriptive of the actual mechanism, and this
project's real mechanism — CAPM beta, Fama-French factor loadings, and
Markowitz efficient-frontier positioning, computed live and attributed back
to the user's own portfolio — is specifically a **factor attribution**
exercise. "Factor Attribution Lens" names that mechanism directly instead of
leaning on the generic "Lens" framing alone.

The mechanical parts of the rename (GitHub repo renamed to
`github.com/ethanverper/factor-attribution-lens`, GitHub keeps the old URL
as a redirect; local project folder moved from
`projects/finance/factor-lens/` to `projects/finance/factor-attribution-lens/`;
`git remote origin` updated; a handful of team-level root docs updated) were
done directly by the orchestrating session before this task. This decision
covers the forward-facing work inside the project itself.

## Decision

Updated everywhere the product name renders as visible text or is used as a
live identifier, across the app, its docs, and its deploy config:

- `README.md` and `frontend/README.md` titles and body mentions.
- Frontend branding: `frontend/index.html` (`<title>`, OG/Twitter meta
  tags), `AppSidebar.tsx` (masthead + GitHub link), `AppLayout.tsx` (mobile
  header), `ApertureMark.tsx` (doc comment + `aria-label`), `Overview.tsx`
  (hero h1/h2/body copy), `real-world.ts` (two inline product-name
  mentions), `index.css` (design-tokens comment).
- `scripts/generate_og_image.py`: the rendered OG image's headline text, its
  "FL" monogram badge (now "FAL"), and the embedded GitHub URL. Not re-run
  here (it fetches Google Fonts over the network to render); the last
  generated `og-image.png` was never committed (`app/static/` is empty in
  git), so there's no stale artifact — `devops`/whoever next serves the app
  should run it once before relying on the social-preview image.
- Deploy/package identity: `pyproject.toml`'s `[project].name` (was
  `factor-lens`, now `factor-attribution-lens`) and the regenerated
  `uv.lock` entry that mirrors it (`uv lock`, minimal one-line diff — no
  dependency changes). `Dockerfile`'s header comment. `railway.json` has no
  name/identifier field, so nothing to change there.
- Backend docstrings (`app/main.py`, `app/schemas.py`, `app/api/__init__.py`,
  `app/api/routes.py`) that name the product in their module-level
  description — these describe current functionality, not a past event, so
  updating them isn't revisionist the way editing historical decision prose
  would be.
- `docs/glossary.md`'s title.
- `docs/roadmap.md`: **only** the `Path:` metadata line at the top, updated
  to `projects/finance/factor-attribution-lens/`. The roadmap's title line
  and its phase-by-phase narrative body are deliberately left untouched —
  see below.

**Local `.venv` was rebuilt from scratch** (`rm -rf .venv && uv sync`).
`uv`-generated venvs bake the absolute creation-time path into console-script
shebangs (`.venv/bin/pytest` etc.); after the folder move those pointed at
the now-nonexistent `.../factor-lens/.venv/bin/python3` and every `pytest`
invocation failed with "No such file or directory" until the venv was
recreated. `.venv/` is gitignored, so this required no repo change, just a
local rebuild — flagging it here because it's the kind of folder-rename
breakage that's easy to miss (tests "pass" in CI/a fresh clone but silently
fail in the one already-existing local checkout).

## What was deliberately left untouched, and why

**All 23 existing decision docs (`0001`–`0023`) and the entire narrative
body of `docs/roadmap.md`** (including its own `# Factor Lens — Roadmap`
title line, and the QA sign-off report at
`docs/status/2026-08-12-phase10j-qa-signoff.md`) still refer to the project
as "Factor Lens," including `github.com/ethanverper/factor-lens` links and
absolute paths under `projects/finance/factor-lens/`. This is intentional:
those documents are an honest record of what the project was actually called
at the time each phase happened and each decision was made. Rewriting them
to say "Factor Attribution Lens" would misrepresent the project's own
history — the same principle the roadmap-body/decision-doc scope boundary in
this task was given under. Anyone following an old `factor-lens` GitHub link
in that historical prose lands on the renamed repo anyway, since GitHub
preserves the old URL as a redirect.

## Verification

- `uv run pytest -q`: 76 passed (unchanged from the pre-rename count, after
  the `.venv` rebuild above).
- `cd frontend && npx tsc -b && npm run build`: both clean; `vite build`
  succeeds (pre-existing >500kB main-chunk size warning is unrelated to this
  change).
- Full-project grep for `factor-lens` / `Factor Lens` after all edits: only
  hits remaining are inside `docs/decisions/0001`–`0023` and
  `docs/roadmap.md`'s narrative body / `docs/status/`, all deliberately left
  per the above.
