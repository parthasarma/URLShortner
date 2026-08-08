import sqlite3
from urllib.parse import urlparse, urlsplit, urlunsplit
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import RedirectResponse, JSONResponse
from .base62 import encode, decode
from .database import get_url_by_long_url, get_url_by_id, insert_url, now_utc_iso
from .models import ShortenRequest, ShortenResponse, LookupRequest, LookupResponse

router = APIRouter()

def public_base_url(request: Request) -> str:
    return 'http://localhost:8000/'

def _extract_code(value: str) -> str:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="Empty input")
    if "://" in value or value.lower().startswith("http"):
        parsed = urlparse(value if "://" in value else "http://" + value)
        code = parsed.path.strip("/")
    else:
        code = value
    if not code:
        raise HTTPException(status_code=422, detail="Could not extract code")
    return code

@router.post("/api/shorten", response_model=ShortenResponse)
async def shorten(req: Request, body: ShortenRequest):
    long_url = str(body.url)
    conn = req.app.state.conn
    existing = get_url_by_long_url(conn, long_url)
    if existing:
        id_ = existing["id"]
        code = encode(id_)
        short_url = f"{public_base_url(req)}{code}"
        return ShortenResponse(
            code=code,
            short_url=short_url,
            long_url=existing["long_url"],
            created_at=existing["created_at"],
        )
    created_at = now_utc_iso()
    try:
        id_ = insert_url(conn, long_url, created_at)
    except sqlite3.IntegrityError:
        existing = get_url_by_long_url(conn, long_url)
        if existing:
            id_ = existing["id"]
            code = encode(id_)
            short_url = f"{public_base_url(req)}{code}"
            return ShortenResponse(
                code=code,
                short_url=short_url,
                long_url=existing["long_url"],
                created_at=existing["created_at"],
            )
        raise HTTPException(status_code=500, detail="Failed to create short URL")
    code = encode(id_)
    short_url = f"{public_base_url(req)}{code}"
    return ShortenResponse(
        code=code,
        short_url=short_url,
        long_url=long_url,
        created_at=created_at,
    )

@router.post("/api/lookup", response_model=LookupResponse)
async def lookup(req: Request, body: LookupRequest):
    code = _extract_code(body.short)
    try:
        id_ = decode(code)
    except Exception:
        raise HTTPException(status_code=404, detail="Short URL not found")
    conn = req.app.state.conn
    row = get_url_by_id(conn, id_)
    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return LookupResponse(
        code=code,
        long_url=row["long_url"],
        created_at=row["created_at"],
    )

@router.get("/{code}")
async def redirect_to_long(req: Request, code: str):
    if not code or not code.isalnum():
        raise HTTPException(status_code=404, detail="Short URL not found")
    try:
        id_ = decode(code)
    except Exception:
        raise HTTPException(status_code=404, detail="Short URL not found")
    conn = req.app.state.conn
    row = get_url_by_id(conn, id_)
    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=row["long_url"], status_code=302)
