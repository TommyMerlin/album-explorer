from __future__ import annotations

import json
from collections import Counter

from fastapi import APIRouter

from app.database import get_db
from app.models import StatsOverview

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats() -> StatsOverview:
    """总览统计信息。"""
    db = await get_db()

    cursor = await db.execute(
        "SELECT COUNT(*) FROM assets WHERE status = 'done' AND result_json IS NOT NULL"
    )
    total = (await cursor.fetchone())[0]

    cursor = await db.execute(
        "SELECT COUNT(*) FROM assets WHERE taken_at IS NOT NULL AND status = 'done'"
    )
    with_time = (await cursor.fetchone())[0]

    cursor = await db.execute(
        "SELECT COUNT(*) FROM assets WHERE gps_lat IS NOT NULL AND status = 'done'"
    )
    with_gps = (await cursor.fetchone())[0]

    # 有城市名的数量
    with_city = 0
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM assets WHERE city_name IS NOT NULL AND status = 'done'"
        )
        with_city = (await cursor.fetchone())[0]
    except Exception:
        pass

    # 聚类数量
    cluster_count = 0
    try:
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT cluster_id) FROM assets WHERE cluster_id IS NOT NULL"
        )
        cluster_count = (await cursor.fetchone())[0]
    except Exception:
        pass

    # 时间范围
    cursor = await db.execute(
        "SELECT MIN(substr(taken_at,1,7)), MAX(substr(taken_at,1,7)) FROM assets WHERE taken_at IS NOT NULL"
    )
    row = await cursor.fetchone()
    month_range = [row[0] or "", row[1] or ""]

    # 热门城市
    top_cities: list[dict] = []
    try:
        cursor = await db.execute(
            "SELECT city_name, COUNT(*) AS cnt FROM assets WHERE city_name IS NOT NULL GROUP BY city_name ORDER BY cnt DESC LIMIT 10"
        )
        rows = await cursor.fetchall()
        top_cities = [{"city": r["city_name"], "count": r["cnt"]} for r in rows]
    except Exception:
        pass

    return StatsOverview(
        total=total,
        with_time=with_time,
        with_gps=with_gps,
        with_city=with_city,
        cluster_count=cluster_count,
        month_range=month_range,
        top_cities=top_cities,
    )
