# Plan: Display short URLs with `localhost` (not IP)

## Goal

Short links currently look like `http://127.0.0.1:8000/1` because `short_url` is built from `request.base_url`. Change display so short URLs use **`localhost`** (e.g. `http://localhost:8000/1`). Keep Base62 id codes, reuse logic, redirect, and lookup unchanged.

## Decision (resolved)

| Topic | Choice |
|--------|--------|
| Change | **Host only** in generated `short_url` |
| Codes | Unchanged (Base62 of `id`) |
| Binding | Server may still listen on `127.0.0.1`; only **displayed** public host becomes `localhost` |
| Lookup | Still accepts full URL or bare code; path extraction already works for either host |

## Root cause

In `app/routers.py`, shorten responses build:

```python
short_url = f"{req.base_url}{code}"
```

When the client hits `http://127.0.0.1:8000`, Starlette’s `base_url` is `http://127.0.0.1:8000/`.

## Implementation

### 1. Add a small public-base helper

In `app/routers.py` (or a tiny `app/urls.py` if preferred—prefer keep in `routers.py` to minimize files):

```python
def public_base_url(request: Request) -> str:
    base = str(request.base_url)  # e.g. http://127.0.0.1:8000/
    # Replace host 127.0.0.1 with localhost; keep scheme + port + trailing slash
    # Prefer urllib.parse urlsplit/urlunsplit for correctness
```

Behavior:

- `http://127.0.0.1:8000/` → `http://localhost:8000/`
- `http://localhost:8000/` → unchanged
- Any other host (future deploy) → leave as-is (only rewrite loopback IP)

Apply in **all three** places that build `short_url` in `shorten` (existing hit, IntegrityError retry, fresh insert).

### 2. Do not change

- `app/base62.py`
- DB schema / CRUD
- Redirect `GET /{code}`
- Lookup parsing
- Frontend (it already shows whatever `short_url` the API returns)
- Server bind address in run commands (optional README note: open via `http://localhost:8000` so browser and short links match)

### 3. README

- Prefer examples with `http://localhost:8000/...`
- Run instructions: open `http://localhost:8000`
- Note that short links are emitted with host `localhost`

### 4. Optional (out of scope unless trivial)

- Env `PUBLIC_BASE_URL` override — **out of scope** for this change
- Random multi-char codes — **out of scope** (user chose host-only)

## Files to touch

1. `app/routers.py` — `public_base_url()` + use it for `short_url`
2. `README.md` — localhost examples / open URL

## Validation

1. Restart or rely on `--reload`
2. `POST /api/shorten` with a URL → `short_url` starts with `http://localhost:8000/` (not `127.0.0.1`)
3. Opening that short URL in the browser still redirects (localhost → same server)
4. Lookup with `http://localhost:8000/{code}` and bare code still works
5. Lookup with old `http://127.0.0.1:8000/{code}` still works (path-only extract)

## Risks

- If user opens the app only via `127.0.0.1` and copies a `localhost` short link, both still hit the same machine on typical Windows setups.
- Cookies/CORS not involved; no extra risk for this local app.
