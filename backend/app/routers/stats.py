from __future__ import annotations

import json
import time

from fastapi import APIRouter

from app.database import get_db
from app.models import StatsOverview
from app.services.query_builder import BRIEF_COLS
from app.routers.assets import _row_to_brief

router = APIRouter(prefix="/api", tags=["stats"])

_cache: dict = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 分钟


@router.get("/stats")
async def get_stats() -> StatsOverview:
    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]

    db = await get_db()

    # 单条 SQL 获取所有计数
    cursor = await db.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN taken_at IS NOT NULL THEN 1 ELSE 0 END) AS with_time,
            SUM(CASE WHEN gps_lat IS NOT NULL THEN 1 ELSE 0 END) AS with_gps,
            SUM(CASE WHEN city_name IS NOT NULL THEN 1 ELSE 0 END) AS with_city,
            COUNT(DISTINCT cluster_id) AS cluster_count,
            MIN(substr(taken_at, 1, 7)) AS min_month,
            MAX(substr(taken_at, 1, 7)) AS max_month
        FROM assets WHERE status = 'done'
    """)
    row = await cursor.fetchone()

    cursor = await db.execute(
        "SELECT city_name, COUNT(*) AS cnt FROM assets WHERE city_name IS NOT NULL AND status = 'done' GROUP BY city_name ORDER BY cnt DESC LIMIT 10"
    )
    city_rows = await cursor.fetchall()

    result = StatsOverview(
        total=row["total"],
        with_time=row["with_time"],
        with_gps=row["with_gps"],
        with_city=row["with_city"],
        cluster_count=row["cluster_count"],
        month_range=[row["min_month"] or "", row["max_month"] or ""],
        top_cities=[{"city": r["city_name"], "count": r["cnt"]} for r in city_rows],
    )

    _cache["data"] = result
    _cache["ts"] = now
    return result


@router.get("/stats/media-types")
async def get_media_type_stats():
    db = await get_db()
    cursor = await db.execute(
        "SELECT media_type, COUNT(*) AS count FROM asset_media_types GROUP BY media_type ORDER BY count DESC"
    )
    rows = await cursor.fetchall()
    return [{"type": r["media_type"], "count": r["count"]} for r in rows]


@router.get("/recommendations")
async def get_recommendations():
    """首页推荐：随机精选 + 热门主题聚类。"""
    db = await get_db()
    cols = BRIEF_COLS.replace("a.", "")

    # 随机精选 12 张
    cursor = await db.execute(
        f"SELECT {cols} FROM assets WHERE status='done' ORDER BY RANDOM() LIMIT 12"
    )
    random_items = [_row_to_brief(r) for r in await cursor.fetchall()]

    # 随机选一个聚类，取其图片
    cursor = await db.execute(
        "SELECT cluster_id, cluster_name FROM clusters ORDER BY RANDOM() LIMIT 1"
    )
    cluster_row = await cursor.fetchone()
    cluster_items = []
    cluster_name = None
    if cluster_row:
        cluster_name = cluster_row["cluster_name"]
        cursor = await db.execute(
            f"SELECT {cols} FROM assets WHERE status='done' AND cluster_id=? ORDER BY RANDOM() LIMIT 12",
            [cluster_row["cluster_id"]],
        )
        cluster_items = [_row_to_brief(r) for r in await cursor.fetchall()]

    return {
        "random": random_items,
        "cluster": {
            "name": cluster_name,
            "cluster_id": cluster_row["cluster_id"] if cluster_row else None,
            "items": cluster_items,
        },
    }


@router.get("/recommendations/random")
async def get_random_picks(limit: int = 12):
    """独立刷新随机精选。"""
    db = await get_db()
    cols = BRIEF_COLS.replace("a.", "")
    cursor = await db.execute(
        f"SELECT {cols} FROM assets WHERE status='done' ORDER BY RANDOM() LIMIT ?",
        [limit],
    )
    return [_row_to_brief(r) for r in await cursor.fetchall()]


@router.get("/recommendations/cluster")
async def get_cluster_pick(limit: int = 12):
    """独立刷新主题推荐。"""
    db = await get_db()
    cols = BRIEF_COLS.replace("a.", "")
    cursor = await db.execute(
        "SELECT cluster_id, cluster_name FROM clusters ORDER BY RANDOM() LIMIT 1"
    )
    cluster_row = await cursor.fetchone()
    if not cluster_row:
        return {"name": None, "cluster_id": None, "items": []}
    cursor = await db.execute(
        f"SELECT {cols} FROM assets WHERE status='done' AND cluster_id=? ORDER BY RANDOM() LIMIT ?",
        [cluster_row["cluster_id"], limit],
    )
    return {
        "name": cluster_row["cluster_name"],
        "cluster_id": cluster_row["cluster_id"],
        "items": [_row_to_brief(r) for r in await cursor.fetchall()],
    }
