# URL Shortener Application Plan

## Goal

Build a complete local URL shortener with:

- **Backend:** Python 3.14, FastAPI, built-in `sqlite3`, UV for deps
- **Frontend:** Single-page static HTML/CSS/vanilla JS
- **Features:** shorten long URL → short link; lookup short URL → original; open short link in new tab; redirect when visiting `/{code}`

## Decisions (resolved)

| Topic | Choice |
|--------|--------|
| Framework | FastAPI + Uvicorn |
| DB | SQLite via stdlib `sqlite3` (no ORM) |
| Deps | UV (`pyproject.toml`) |
| Short codes | **Base62 encode/decode of integer primary key** (collision-free) |
| Duplicate long URLs | **Reuse existing mapping** (exact string match on `long_url`) |
| Timestamps | UTC ISO-8601 on first create only (`created_at` unchanged on reuse) |
| Frontend | Static files only; no build step |
| Redirect | `GET /{code}` → 302 to original URL |
| Lookup API | `POST /api/lookup` JSON body; accepts full short URL or bare code |
| Static assets | Served under `/static/*`; `GET /` returns `index.html` |

## Project structure

```
URLShortner/
├── pyproject.toml
├── README.md
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, lifespan, static, routers
│   ├── database.py      # connection, schema init, CRUD
│   ├── base62.py        # encode_id / decode_code helpers
│   ├── models.py        # Pydantic request/response schemas
│   └── routers.py       # API + redirect routes
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── data/
    └── .gitkeep         # runtime DB: data/urls.db (gitignored)
```

## Data model

Table `urls`:

| Column | Type | Notes |
|--------|------|--------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Source of short code via Base62 |
| `long_url` | TEXT NOT NULL UNIQUE | Exact string; reuse on match |
| `created_at` | TEXT NOT NULL | UTC ISO-8601 at first insert |

- **No separate `code` column:** code is always `base62_encode(id)`.
- Indexes: PK on `id`; UNIQUE on `long_url`.

### Base62

- Alphabet: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz` (62 chars).
- `encode(id: int) -> str` — reject `id < 1`.
- `decode(code: str) -> int` — reject empty/invalid chars; raise/return error for bad input.
- No padding; short IDs produce short codes (`1` → `"1"`, etc.).
- Collision-resistant by construction (bijective with positive integers).

## Backend behavior

### Startup (lifespan)

1. Ensure `data/` exists.
2. Open `data/urls.db` with `sqlite3.connect(..., check_same_thread=False)`.
3. `CREATE TABLE IF NOT EXISTS urls (...)`.
4. Store connection on `app.state` (or module-level singleton closed on shutdown).

### Endpoints

1. **`GET /`**  
   FileResponse `static/index.html`.

2. **`POST /api/shorten`**  
   Body: `{ "url": "https://example.com/..." }`  
   - Validate absolute `http`/`https` URL (Pydantic `HttpUrl` or `urllib.parse`).  
   - Normalize to string (keep query/fragment as provided; no aggressive rewrite).  
   - `SELECT` by exact `long_url`:  
     - **Hit:** return existing row (same code/`created_at`).  
     - **Miss:** `INSERT`, read `lastrowid`, encode Base62.  
   - Response `200`:  
     `{ "code", "short_url", "long_url", "created_at" }`  
   - `short_url` = `{request.base_url}{code}` (no extra slash issues; strip trailing slash on base).

3. **`POST /api/lookup`**  
   Body: `{ "short": "http://127.0.0.1:8000/aB3" }` or `{ "short": "aB3" }`  
   - Extract code: if value looks like URL, take last path segment; else use trimmed string.  
   - `decode(code)` → `id`; invalid Base62 → `404` or `422` (prefer **404** “not found” for unknown/invalid codes to avoid leaking format details; **422** only for empty input).  
   - `SELECT` by `id`; missing → `404`.  
   - Response: `{ "code", "long_url", "created_at" }`.

4. **`GET /{code}`**  
   - Path param constrained: e.g. regex `^[0-9A-Za-z]+$`, reasonable max length (e.g. 12).  
   - Decode → id → row → **302** `RedirectResponse` to `long_url`.  
   - Unknown/invalid → `404` JSON `{"detail": "Short URL not found"}`.  
   - Registered **after** `/api/*` and static routes so it cannot shadow them.

### Errors

| Case | Status |
|------|--------|
| Empty / invalid long URL scheme | 422 |
| Empty lookup input | 422 |
| Unknown or undecodable code | 404 |
| DB failure | 500 |

### Concurrency note (reuse)

- Unique on `long_url`: on race, two inserts may conflict → catch `IntegrityError`, re-SELECT and return existing row.

## Frontend

Single page, two sections, centered minimal card UI (system fonts, no CDN/frameworks).

1. **Shorten**  
   - Input + “Shorten” button.  
   - Success: show clickable `<a href="{short_url}" target="_blank" rel="noopener noreferrer">`.  
   - Show errors inline.

2. **Lookup**  
   - Input (short URL or code) + “Lookup” button.  
   - Success: clickable original long URL (`target="_blank"`).  
   - Errors inline.

JS: `fetch` JSON to `/api/shorten` and `/api/lookup`; no build step.  
Assets: `/static/styles.css`, `/static/app.js` linked from HTML.

## UV / tooling

`pyproject.toml`:

- `name = "urlshortner"` (or `url-shortener`)
- `requires-python = ">=3.14"`
- Dependencies: `fastapi`, `uvicorn[standard]`
- No ORM, no extra Base62 package (implement in `app/base62.py`)

Run (README):

```bash
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

`.gitignore`: `.venv/`, `data/*.db`, `__pycache__/`, `*.pyc`, `.uv/` if present, `.python-version` optional.

## README

- Description of shorten / lookup / redirect  
- Prerequisites: Python 3.14+, [UV](https://github.com/astral-sh/uv)  
- Install & run  
- API summary with example JSON  
- Layout tree  
- Note: SQLite file at `data/urls.db`; single-process local use  

After implementation, satisfy **feature-readme-update** skill (README reflects shipped features; confirm in chat).

## Implementation order

1. Scaffold `pyproject.toml`, `.gitignore`, `data/.gitkeep`, `app/__init__.py`
2. Implement `app/base62.py` with small encode/decode correctness in mind (round-trip ids)
3. Implement `app/database.py` (init, get_by_long_url, get_by_id, insert)
4. Implement `app/models.py` + `app/routers.py` (shorten, lookup, redirect)
5. Wire `app/main.py` (lifespan, mount StaticFiles, routes)
6. Build `static/index.html`, `styles.css`, `app.js`
7. Rewrite `README.md`
8. Smoke-test flows below

## Validation

- `uv sync` works on the machine (if 3.14 missing: document fallback in README only after attempting 3.14)
- App starts; `data/urls.db` created with schema
- Shorten `https://example.com` → Base62 code; second shorten same URL → **same** code/`created_at`
- Different URL → different code
- Click short URL → 302 to original
- Lookup with full short URL and bare code both return original
- Invalid long URL → 422; unknown code → 404
- Frontend is HTML/CSS/JS only under `static/`

## Out of scope

- Auth, rate limits, click analytics  
- Custom aliases, expiration, QR  
- URL normalization beyond exact-string reuse (trailing slash variants = different rows)  
- Docker / multi-worker production SQLite  
- Copy-to-clipboard button (optional; skip unless trivial)

## Risks

- **Python 3.14:** if unavailable, implementer tries `uv python install 3.14` / pin; if blocked, use latest available 3.x and note in README while keeping syntax compatible.
- **Route clashes:** do not use catch-all that steals `/static` or `/api`; constrain `/{code}`.
- **Open redirects:** only redirect to `long_url` values previously validated as http(s) at insert time.
- **Base62 ambiguity:** alphabet must match encode/decode exactly; document alphabet in code module docstring only if needed (no extra comments noise per project style—keep helpers clear by naming).

## Concrete scenarios (acceptance)

| Step | Expected |
|------|----------|
| Shorten `https://example.com/a` | `code` e.g. `1`, `short_url` ends with that code |
| Shorten same again | Identical `code` and `created_at` |
| Shorten `https://example.com/b` | New id/code |
| GET `/{code}` | 302 → stored long URL |
| Lookup bare code | JSON with `long_url` |
| Lookup `http://127.0.0.1:8000/{code}` | Same |
| Lookup `@@@` or missing id | 404 |
| Shorten `ftp://x` or `not-a-url` | 422 |
