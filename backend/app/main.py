from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db
from app.routers import assets, clusters, map_view, saved_searches, search, stats, tags, thumbnails, timeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保缩略图目录存在
    settings.thumbnail_dir.joinpath("sm").mkdir(parents=True, exist_ok=True)
    settings.thumbnail_dir.joinpath("md").mkdir(parents=True, exist_ok=True)
    yield
    await close_db()


app = FastAPI(
    title="Album Explorer",
    description="相册语义浏览器 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件直接挂载缩略图目录，绕过路由逻辑，速度最快
app.mount(
    "/static/thumbs",
    StaticFiles(directory=str(settings.thumbnail_dir)),
    name="thumbs",
)

app.include_router(assets.router)
app.include_router(thumbnails.router)
app.include_router(timeline.router)
app.include_router(map_view.router)
app.include_router(clusters.router)
app.include_router(search.router)
app.include_router(tags.router)
app.include_router(stats.router)
app.include_router(saved_searches.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
