# 0014. Phase 10e: trim OpenBB dependency to only the packages actually used

Date: 2026-08-11
Status: accepted

## Context

Ethan reported the app taking many minutes to start locally — both `uv sync`
and `uv run uvicorn`/`uv run pytest`. `pyproject.toml` declared the full
"batteries included" `openbb>=4.7,<5` meta-package (decision 0002), which
pulls in all 25+ OpenBB provider extensions (SEC, FRED, IMF, crypto, news,
congress.gov, economy, fixed income, benzinga, tiingo, intrinio, fmp, etc.)
— 62 OpenBB-namespaced packages total. OpenBB builds its `obb.*` API surface
dynamically by scanning every installed extension's entry points at import
time, so this bloat cost was paid on *every* fresh process start (every
`uv run uvicorn`/`uv run pytest`), not just the one-time `uv sync`.
Confirmed by re-reading `app/data/equity.py` and `app/data/benchmark.py`
(the only two call sites touching `obb.*`, per a full `grep -rn "obb\."` /
`grep -rln "openbb"` across `app/` and `tests/`): the entire OpenBB surface
this app touches is `obb.equity.price.historical(...)` against the
`yfinance` provider — nothing else.

## Decision

Replaced `openbb>=4.7,<5` in `pyproject.toml` with three targeted packages,
pinned the same way the old meta-package was (`>=1.6,<2`, tracking its
installed major version, avoiding an unplanned major bump):

```
openbb-core>=1.6,<2
openbb-equity>=1.6,<2
openbb-yfinance>=1.6,<2
```

`openbb-core` is the runtime/router itself. `openbb-equity` is the extension
that defines the `equity.price.historical` route (it depends only on
`openbb-core`, not on any provider). `openbb-yfinance` is the provider
extension that actually serves that route's data (depends on `openbb-core`
and `yfinance` itself). All three were already present as transitive
dependencies of the old `openbb` meta-package, confirmed via `uv.lock`
before the change (`openbb-core==1.6.13`, `openbb-equity==1.6.2`,
`openbb-yfinance==1.6.3`) — no version was chosen blind.

No other provider extension was added. `openbb>=4.7,<5` itself was dropped
entirely (it was a pure meta-package with no functional code of its own,
only a dependency list).

## A real bug found and fixed along the way: stale generated package tree

`uv sync` applying this change in place (uninstall old openbb packages,
keep the rest) left the app broken: `from openbb import obb` raised
`ImportError: cannot import name 'obb' from 'openbb' (unknown location)`.
Root-caused (via `systematic-debugging`) to OpenBB's own architecture:
`openbb-core` ships a build step (`openbb-build` console script /
`openbb_core.build:main`) that generates `openbb/__init__.py` and
`openbb/package/*.py` as static files reflecting whichever extensions are
installed, cached to disk after the first import. The in-place `uv sync`
uninstall of the old `openbb` meta-package removed those generated files
(they were tracked under its installed-file record from the original
build) but left an orphaned `openbb/package/` directory of stale stubs
from the old 62-package build, with no valid `openbb/__init__.py` left to
bootstrap a rebuild — `openbb-build` itself depends on `import openbb`
already working, so it couldn't self-heal. Fixed by deleting `.venv`
entirely and running `uv sync` fresh: a clean install lets `openbb-core`'s
shipped bootstrap `__init__.py` install correctly and its first-import
auto-build regenerate the package tree scoped only to what's actually
installed (`openbb/package/` went from ~39 provider-spanning stub files to
9 equity-only files). This is a one-time cost, not a recurring one — the
generated tree persists on disk across subsequent process starts.

## Measured before/after

Absolute numbers below are specific to this sandboxed dev environment
(file I/O on this machine's `~/Documents`-rooted path is unusually slow —
even deleting the 44 removed packages' files during the in-place `uv sync`
took 11m43s of pure disk I/O), so they won't transfer 1:1 to Ethan's own
machine, but the *relative* improvement (package count, and the resulting
process-start behavior) is the real, portable result:

- **Package count**: 62 OpenBB-namespaced packages / 25+ provider
  extensions → 3 packages (`openbb-core`, `openbb-equity`,
  `openbb-yfinance`) / 1 provider extension (`yfinance`).
- **Fresh `uv sync` (clean `.venv`, cold `uv` cache hits)**: ~18s total,
  vs. the original bloated install (which this same environment's
  in-place uninstall step alone took 11m43s to walk — the original full
  install was of comparable or greater order, consistent with Ethan's
  "many minutes" report).
- **`uv run uvicorn app.main:app` reaching a ready `/health` response,
  measured end-to-end in one self-contained timed script (no cross-call
  timing contamination)**: **4.02s**, post-warm (generated OpenBB package
  tree already built once).
- **`from openbb import obb` import time, steady state (post-build)**:
  0.74s; a live `obb.equity.price.historical(...)` fetch on top of that:
  0.88s. The one-time first-ever cold-build import (this environment's
  disk, equity+yfinance-only): 26.5s — a single one-time cost, not paid on
  every subsequent process start.
- Not independently re-measured: a live "before" run of the original
  62-package install's `uv run uvicorn` startup time. Reinstalling the
  full bloat just to re-time it would take another 10+ minutes on this
  environment and re-demonstrate what the uninstall timing and package
  count already show; the original multi-minute startup is the reported
  and now-fixed problem, not a number this fix needed to reproduce.

## Verification

- Confirmed `uv.lock` now lists exactly `openbb-core`, `openbb-equity`,
  `openbb-yfinance` under the `openbb-*` namespace (`grep '^name = "openbb'
  uv.lock`) — no SEC/FRED/IMF/crypto/news/etc. packages remain.
- Full 57-test suite passes (`uv run pytest -v`, live network calls
  included, no mocking — same convention as every prior phase), `ruff
  check .` clean.
- Manual end-to-end verification in the in-app Browser tools: started the
  real server, ran the sample-portfolio quick-start
  (`GET /dashboard/sample`, AAPL/MSFT/GOOGL/AMZN), confirmed the full
  Results tab (CAPM beta, Fama-French loadings, efficient frontier,
  return/risk attribution) renders correctly against live yfinance/Kenneth
  French data through the trimmed install — no regressions.

## Consequences

- `app/data/equity.py`'s existing `provider: str = "yfinance"` parameter
  is now the *only* provider actually installed — passing any other
  provider string (`fmp`, `intrinio`, etc.) will now fail immediately with
  a clear "provider not found" error instead of silently working, since
  those extensions are no longer installed. This matches actual usage
  (decision 0002 already committed to yfinance-only) but is worth knowing
  if a future phase ever wants to add a second equity data provider —
  that would need its own `openbb-<provider>` package added deliberately,
  not assumed already present.
- `docs/roadmap.md` and `README.md`'s "openbb's first import is slow...
  can take several minutes on a cold run" note (written when the full
  62-package meta-package was in use) is now materially inaccurate and
  updated alongside this change.
