from __future__ import annotations

from pydantic import BaseModel


class AssetBrief(BaseModel):
    """列表页用的精简模型。"""

    asset_id: int
    rel_path: str
    asset_type: str
    source_format: str
    taken_at: str | None
    city_name: str | None
    province_name: str | None
    cluster_id: int | None
    cluster_name: str | None
    caption_short: str | None
    scene: str | None
    tags: list[str]
    people_count: int | None
    gps_lat: float | None
    gps_lng: float | None
    month_bucket: str | None


class AssetDetail(AssetBrief):
    """详情页完整模型。"""

    caption_long: str | None
    activities: list[str]
    main_subjects: list[str]
    style_labels: list[str]
    ocr_text: str | None
    confidence: float | None
    quality_flags: list[str]


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class TimelineBucket(BaseModel):
    month: str
    count: int
    representative_id: int | None


class ClusterInfo(BaseModel):
    cluster_id: int
    cluster_name: str
    asset_count: int
    representative_asset_id: int | None
    top_tags: list[str]


class TagNode(BaseModel):
    tag: str
    count: int


class TagEdge(BaseModel):
    source: str
    target: str
    weight: int


class TagGraph(BaseModel):
    nodes: list[TagNode]
    edges: list[TagEdge]


class MapPoint(BaseModel):
    asset_id: int
    lat: float
    lng: float
    caption_short: str | None


class StatsOverview(BaseModel):
    total: int
    with_time: int
    with_gps: int
    with_city: int
    cluster_count: int
    month_range: list[str]
    top_cities: list[dict]
