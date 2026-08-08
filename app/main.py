from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import get_db_connection, init_db
from .routers import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_db_connection()
    init_db(conn)
    app.state.conn = conn
    yield
    conn.close()

app = FastAPI(title="URLShortner", lifespan=lifespan)

app.include_router(router)

app.mount("/static", StaticFiles(directory="static", html=False), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse("static/index.html")
