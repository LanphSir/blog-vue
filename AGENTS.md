# AGENTS.md

Personal blog: `backend/` (FastAPI + SQLite) and `frontend/` (Vue 3 + Vite + Element Plus) are independent packages — no root workspace tooling. Frontend content is fully driven by backend data.

## Commands

- Backend: always via `uv run` (venv-local; `uvicorn` is NOT on PATH — use `uv run uvicorn app.main:app --reload --port 8000`).
  - Install: `cd backend && cp .env.example .env && uv sync`
  - Test: `uv run pytest` · Lint/format: `uv run ruff check app`, `uv run ruff format app`
- Frontend: `cd frontend && npm install`, then `npm run dev` (port 5173), `npm run build`.
- `npm run lint` / `npm run format` in package.json reference ESLint/Prettier that are **not installed** — don't run them unless you add the deps.
- Vite proxies `/api` and `/uploads` → `localhost:8000`, so no CORS setup needed for frontend dev.

## Backend architecture

- Entry `app/main.py`; layered as `core/` (config/security/logging/db) → `models/` → `crud/` → `api/v1/endpoints/`. Config is env-driven, prefix `BLOG_`.
- All responses use the envelope `{code, message, data}`. Auth: `POST /api/v1/auth/login`, `GET /api/v1/auth/me`; admin routes need `Authorization: Bearer <token>` (frontend stores it in localStorage `blog_token`).
- SQLAlchemy is async (aiosqlite). After `await db.commit()` objects are expired — `await db.refresh(post)` before serializing (see `get_post` in `posts.py`).
- Tables are auto-created + seeded on startup (admin user, default site configs). Alembic migrations live in `backend/migrations/` (`uv run alembic upgrade head`); both paths work because `create_all` is idempotent.
- On a fresh DB, startup also seeds demo content (6 categories with a parent/child hierarchy, 14 colored tags, 11 posts incl. 1 draft, 3 friend links, 2 banners) — only when the `posts` table is empty, so it's safe to re-run.
- When adding a model, import it in `app/models/__init__.py` — the class must be registered on `Base.metadata` or the table won't be created.
- Uploads: `POST /api/v1/admin/upload` saves into `backend/uploads/`, served at `/uploads` via StaticFiles (Vite proxies it in dev, nginx in Docker).
- Frontend theme: site config `site_accent_color` is applied to the CSS var `--blog-primary` via `stores/config.js`. Markdown rendering uses `md-editor-v3` (`MdEditor` in admin, `MdPreview`/`MdCatalog` on article pages), lazy-imported via `composables/useMdEditor.js`, which also registers the local `highlight.js/lib/common` + `screenfull` instances via `config()` (do NOT reintroduce `marked`).
- Frontend ordering: `useReveal.js` uses a `MutationObserver` to reveal async-rendered `.reveal` elements — don't "simplify" it back to mount-only observing or v-for sections stay invisible at `opacity: 0`.
- Post ordering (public list): `is_top` → `sort_weight` → `published_at` desc; category/tag order by `sort_order`. Categories/tags have a `visible` flag for homepage/tag-cloud display.
- Posts support **soft delete**: `deleted_at` column; admin delete moves to recycle bin (`GET /admin/posts?deleted=true`), restore = `POST /admin/posts/{id}/restore`, permanent = `DELETE /admin/posts/{id}/permanent`. Public lists, counts and stats all exclude soft-deleted posts — keep that filter when querying.
- Homepage category tabs are driven by `route.query.category_id` (single source of truth) so the nav menu and homepage stay in sync — don't reintroduce local-only tab state.
- Sidebar cards (`ProfileCard`/`HomeSidebar`), the notice bar and the search panel are all controlled by `site_*` config keys (see `seed.py` defaults); boolean configs arrive as strings ("true"/"false") — components must treat them as strings.
- Captcha: `GET /api/v1/auth/captcha` returns a PNG + `X-Captcha-Id` header; `POST /api/v1/auth/login` requires `captcha_id` + `captcha_code` fields. The backend skips captcha check when `captcha_id` is empty (backwards-compat for tests). The captcha store is an in-memory OrderedDict with a 5-minute TTL — not shared across workers.

## Gotchas (verified, do not "fix")

- `bcrypt` is pinned `<4.1` because passlib 1.7.4 crashes with bcrypt≥4.1 (72-byte password error at startup).
- `.env` sets a relative `sqlite+aiosqlite:///./data/blog.db`; `_resolve_sqlite_url()` in `core/database.py` rewrites it to an absolute path under `backend/`. Keep that rewrite — it makes the path cwd-independent.
- FastAPI/Starlette are very new (0.141/1.6): `TestClient` must be used as a context manager (`with TestClient(app)`) or the startup lifespan (table creation) never runs.
- Alembic autogenerate renders FK adds that **fail on SQLite** ("No support for ALTER of constraints"); any new-column-with-FK migration must use `with op.batch_alter_table(...)` (see `43f81752c57c_category_hierarchy_colors_banners.py`).
- `StaticFiles(directory=...)` raises at import time if the dir doesn't exist — `main.py` `mkdir`s the upload dir before mounting.

## Testing

- `tests/conftest.py` overrides `get_db` with an in-memory SQLite engine (`StaticPool`). The app lifespan still seeds the real `data/blog.db` during tests, but the test admin/config are seeded manually in the `db_session` fixture — add any new seed data there too.
- `asyncio_mode = "auto"` is set; async fixtures/tests need no decorators.
- Run tests from `backend/`: `uv run pytest`.

## Style

- Backend: Python 3.12 type hints; PEP 695 generics (`class ApiResponse[T]`) are expected — ruff enables UP046/UP047. Line length 100.
- Frontend: plain JavaScript (no TS), Vue 3 `<script setup>`, `@/` alias → `src/`.