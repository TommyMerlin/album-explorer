"""批量 GPS 反查城市名（基于地级市 Shapefile 点在面查询）。

用法：
    python -m tasks.reverse_geocode
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings

CITY_SHP = Path(__file__).resolve().parents[2] / "data" / "china_shp" / "3. City" / "city.shp"

MUNICIPALITY_NAMES = {"北京市": "北京", "上海市": "上海", "天津市": "天津", "重庆市": "重庆"}


def normalize_city(ct_name: str, pr_name: str) -> tuple[str, str]:
    """标准化城市名和省份名。"""
    province = pr_name.rstrip("省市壮族回族维吾尔自治区特别行政区")
    if pr_name in MUNICIPALITY_NAMES:
        province = MUNICIPALITY_NAMES[pr_name]
        return province, province
    city = ct_name.rstrip("市地区盟")
    if "自治州" in ct_name:
        city = ct_name
    return city, province


def main() -> None:
    if not CITY_SHP.exists():
        print(f"错误：找不到 Shapefile: {CITY_SHP}")
        print("请先运行: git clone --depth 1 https://github.com/GaryBikini/ChinaAdminDivisonSHP.git data/china_shp")
        sys.exit(1)

    # 直接操作源数据库，避免跨文件系统拷贝损坏
    db_path = settings.db_source if settings.db_source.exists() else settings.db_path
    print(f"使用数据库: {db_path}")

    print("加载地级市 Shapefile...")
    city_gdf = gpd.read_file(str(CITY_SHP))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("ALTER TABLE assets ADD COLUMN city_name TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE assets ADD COLUMN province_name TEXT")
    except Exception:
        pass
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_city_name ON assets(city_name)")
    except Exception:
        pass

    rows = conn.execute(
        "SELECT asset_id, gps_lat, gps_lng FROM assets "
        "WHERE gps_lat IS NOT NULL AND gps_lng IS NOT NULL AND status = 'done'"
    ).fetchall()

    print(f"共 {len(rows)} 张图片需要反查地理信息")

    if not rows:
        print("无需处理。")
        conn.close()
        return

    print("构建 GeoDataFrame...")
    points = [Point(r["gps_lng"], r["gps_lat"]) for r in rows]
    asset_ids = [r["asset_id"] for r in rows]
    points_gdf = gpd.GeoDataFrame(
        {"asset_id": asset_ids},
        geometry=points,
        crs="EPSG:4326",
    )

    print("执行空间连接（点在面查询）...")
    joined = gpd.sjoin(points_gdf, city_gdf, how="left", predicate="within")

    print("写入数据库...")
    updates = []
    for _, row in joined.iterrows():
        ct_name = row.get("ct_name")
        pr_name = row.get("pr_name")
        asset_id = row["asset_id"]

        if pd.isna(ct_name) or not ct_name:
            updates.append((None, None, asset_id))
        else:
            city, province = normalize_city(ct_name, pr_name)
            updates.append((city, province, asset_id))

    conn.executemany(
        "UPDATE assets SET city_name = ?, province_name = ? WHERE asset_id = ?",
        updates,
    )
    conn.commit()
    conn.close()

    matched = sum(1 for u in updates if u[0] is not None)
    print(f"完成！已更新 {len(updates)} 条记录，其中 {matched} 条匹配到城市，{len(updates) - matched} 条未匹配（可能在国外或边界外）。")


if __name__ == "__main__":
    main()
