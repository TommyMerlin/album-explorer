from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import MapPoint

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/points")
async def get_map_points(
    south: float | None = None,
    north: float | None = None,
    west: float | None = None,
    east: float | None = None,
    limit: int = Query(2000, ge=1, le=5000),
) -> list[MapPoint]:
    """获取地图标记点，可按视口范围筛选。"""
    db = await get_db()
    conditions = [
        "gps_lat IS NOT NULL",
        "gps_lng IS NOT NULL",
        "status = 'done'",
        "result_json IS NOT NULL",
    ]
    params: list[Any] = []

    if south is not None and north is not None:
        conditions.append("gps_lat BETWEEN ? AND ?")
        params.extend([south, north])
    if west is not None and east is not None:
        conditions.append("gps_lng BETWEEN ? AND ?")
        params.extend([west, east])

    where = " AND ".join(conditions)
    sql = f"SELECT asset_id, gps_lat, gps_lng, result_json FROM assets WHERE {where} LIMIT ?"
    params.append(limit)

    cursor = await db.execute(sql, params)
    rows = await cursor.fetchall()

    points = []
    for r in rows:
        result = json.loads(r["result_json"]) if r["result_json"] else {}
        points.append(
            MapPoint(
                asset_id=r["asset_id"],
                lat=r["gps_lat"],
                lng=r["gps_lng"],
                caption_short=result.get("caption_short"),
            )
        )
    return points
