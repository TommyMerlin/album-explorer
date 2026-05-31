from __future__ import annotations

import time

from fastapi import APIRouter

from app.database import get_db
from app.models import StatsOverview

router = APIRouter(prefix="/api/stats", tags=["stats"])

_cache: dict = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 分钟


@router.get("")
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
