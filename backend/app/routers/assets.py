from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.models import AssetBrief, AssetDetail, PaginatedResponse
from app.services.query_builder import BRIEF_COLS, QueryBuilder

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _row_to_brief(row: Any) -> AssetBrief:
    taken_at = row["taken_at"]
    tags_text = row["tags_text"] or ""
    return AssetBrief(
        asset_id=row["asset_id"],
        rel_path=row["rel_path"],
        asset_type=row["asset_type"],
        source_format=row["source_format"],
        taken_at=taken_at,
        city_name=row["city_name"],
        province_name=row["province_name"],
        cluster_id=row["cluster_id"],
        cluster_name=row["cluster_name"],
        caption_short=row["caption_short"],
        scene=row["scene"],
        tags=tags_text.split("|") if tags_text else [],
        people_count=None,
        gps_lat=row["gps_lat"],
        gps_lng=row["gps_lng"],
        month_bucket=taken_at[:7] if taken_at else None,
    )


def _row_to_detail(row: Any) -> AssetDetail:
    result = json.loads(row["result_json"]) if row["result_json"] else {}
    taken_at = row["taken_at"]
    return AssetDetail(
        asset_id=row["asset_id"],
        rel_path=row["rel_path"],
        asset_type=row["asset_type"],
        source_format=row["source_format"],
        taken_at=taken_at,
        city_name=row["city_name"] if "city_name" in row.keys() else None,
        province_name=row["province_name"] if "province_name" in row.keys() else None,
        cluster_id=row["cluster_id"] if "cluster_id" in row.keys() else None,
        cluster_name=row["cluster_name"] if "cluster_name" in row.keys() else None,
        caption_short=result.get("caption_short"),
        scene=result.get("scene"),
        tags=result.get("tags", []),
        people_count=result.get("people_count"),
        gps_lat=row["gps_lat"],
        gps_lng=row["gps_lng"],
        month_bucket=taken_at[:7] if taken_at else None,
        caption_long=result.get("caption_long"),
        activities=result.get("activities", []),
        main_subjects=result.get("main_subjects", []),
        style_labels=result.get("style_labels", []),
        ocr_text=result.get("ocr_text"),
        confidence=result.get("confidence"),
        quality_flags=result.get("quality_flags", []),
    )


@router.get("")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: str | None = None,
    cluster_id: int | None = None,
    city: str | None = None,
    province: str | None = None,
    month: str | None = None,
    tag: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    has_gps: bool | None = None,
    sort_by: str = Query("taken_at", pattern="^(taken_at|asset_id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse:
    db = await get_db()
    qb = (
        QueryBuilder()
        .filter_text(q)
        .filter_cluster(cluster_id)
        .filter_city(city)
        .filter_province(province)
        .filter_month(month)
        .filter_tag(tag)
        .filter_date_range(date_from, date_to)
        .filter_has_gps(has_gps)
    )

    count_sql, count_params = qb.build_count()
    cursor = await db.execute(count_sql, count_params)
    total = (await cursor.fetchone())[0]

    total_pages = max(1, (total + page_size - 1) // page_size)

    data_sql, data_params = qb.build_select(sort_by, order, page, page_size)
    cursor = await db.execute(data_sql, data_params)
    rows = await cursor.fetchall()

    items = [_row_to_brief(r) for r in rows]
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=total_pages,
    )


@router.get("/{asset_id}")
async def get_asset(asset_id: int) -> AssetDetail:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM assets WHERE asset_id = ?", [asset_id])
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    return _row_to_detail(row)
