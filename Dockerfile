# Factor Lens — single-service production image.
#
# Deployment shape is decided in docs/decisions/0018-phase10i-react-rebuild.md
# §2 and logged in docs/decisions/0023-phase11-railway-deployment.md: one
# process serves both the JSON API and the built React SPA. This Dockerfile
# builds the frontend in a throwaway Node stage, then installs the Python
# deps (uv) and copies the built `frontend/dist/` into the final image —
# `app/main.py` mounts it via StaticFiles + a SPA catch-all route.

# ---- Stage 1: build the frontend ----
FROM node:22-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: python runtime ----
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Python dependencies first (own layer, cached across app-code-only
# changes) — production deps only, `dev` group (pytest/httpx) excluded.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# App source (no separate `pip install`/build step: this project has no
# [build-system] table, it runs directly off the working directory the same
# way `uv run uvicorn app.main:app` already does in local dev).
COPY app ./app

# Built frontend static assets, from stage 1.
COPY --from=frontend-build /frontend/dist ./frontend/dist

# Warm OpenBB's one-time generated-package-tree build (see decision
# 0014/0023): `from openbb import obb` triggers a build of `openbb/__init__.py`
# and `openbb/package/*.py` on its *first* import, cached to disk afterward.
# Doing this here bakes the generated tree into the image layer so every
# container start is fast — without this, the first live request after each
# deploy/restart would eat that one-time cost instead.
RUN uv run python -c "from openbb import obb"

# Railway sets $PORT at runtime; never hardcode a port.
EXPOSE 8000
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
