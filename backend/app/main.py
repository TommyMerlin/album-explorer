from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db, get_db
from app.routers import albums, assets, clusters, favorites, map_view, persons, saved_searches, search, stats, tags, thumbnails, timeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保缩略图目录存在
    settings.thumbnail_dir.joinpath("sm").mkdir(parents=True, exist_ok=True)
    settings.thumbnail_dir.joinpath("md").mkdir(parents=True, exist_ok=True)
    settings.vectors_dir.joinpath("face_thumbs").mkdir(parents=True, exist_ok=True)
    # 初始化数据库连接和表结构
    await get_db()
    await albums.ensure_album_tables()
    await favorites.ensure_favorites_table()
    await persons.ensure_persons_tables()
    await saved_searches.ensure_table()
    yield
    await close_db()


app = FastAPI(
    title="Album Explorer",
    description="相册语义浏览器 API",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = os.environ.get("ALBUM_EXPLORER_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件直接挂载缩略图目录，绕过路由逻辑，速度最快
app.mount(
    "/static/thumbs",
    StaticFiles(directory=str(settings.thumbnail_dir)),
    name="thumbs",
)
app.mount(
    "/static/faces",
    StaticFiles(directory=str(settings.vectors_dir / "face_thumbs")),
    name="faces",
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
app.include_router(albums.router)
app.include_router(favorites.router)
app.include_router(persons.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
