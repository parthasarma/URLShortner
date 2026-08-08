# URLShortner

A minimal, self-contained URL shortener.

- Backend: Python 3.14 + FastAPI + built-in sqlite3
- Frontend: single-file static HTML + CSS + vanilla JS
- Short codes: Base62-encoded auto-increment IDs (collision-free)
- Duplicate long URLs reuse the original short code and timestamp
- No external databases, no JS frameworks, no build step

## Features

- Enter long URL → get short link (clickable, opens in new tab)
- Paste short URL or code → retrieve and display original long URL (clickable)
- Visiting `/{code}` redirects (302) to the original destination
- Clean, centered, responsive minimal UI

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (or `pip install uv`)

## Run locally

```bash
# install deps (creates .venv and installs from pyproject.toml)
uv sync

# start the server
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

The SQLite database is created automatically at `data/urls.db`.

## Usage

### Web UI

1. **Shorten**
   - Paste a full `https://...` URL
   - Click **Shorten**
   - Click the resulting short link (opens destination in new tab)

2. **Lookup**
   - Paste a short URL (e.g. `http://127.0.0.1:8000/abc12345`) or just the code
   - Click **Lookup**
   - Click the shown long URL to open it

### API

**Shorten**

```
POST /api/shorten
Content-Type: application/json

{ "url": "https://example.com/long/path?with=query" }
```

Response:

```json
{
  "code": "a1B2c3D4",
  "short_url": "http://127.0.0.1:8000/a1B2c3D4",
  "long_url": "https://example.com/long/path?with=query",
  "created_at": "2026-08-08T03:19:30.123456+00:00"
}
```

**Lookup**

```
POST /api/lookup
{ "short": "http://127.0.0.1:8000/a1B2c3D4" }
```

or

```
{ "short": "a1B2c3D4" }
```

Response same shape without `short_url`.

**Redirect**

```
GET /a1B2c3D4
```

Returns 302 redirect to the stored long URL.

## Project structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + lifespan + static + routes
│   ├── database.py      # sqlite connection, schema, CRUD
│   ├── base62.py        # encode/decode integer <-> Base62 code
│   ├── models.py        # Pydantic request/response models
│   └── routers.py       # API handlers + redirect handler
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   └── .gitkeep         # DB lives here (urls.db is gitignored)
├── pyproject.toml
├── .gitignore
└── README.md
```

## How short codes work

- Every inserted row gets an `id` (AUTOINCREMENT).
- The short code is the Base62 encoding of that `id`.
- Same long URL always returns the same code (exact string match + UNIQUE constraint).
- No custom aliases or expiration.

## Development notes

- Single-process local use only (SQLite).
- No rate limiting / auth / analytics (by design).
- To reset data: delete `data/urls.db`.

## License

MIT (or public domain — whatever you prefer).
