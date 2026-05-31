"""批量 GPS 反查城市名。

用法：
    python -m tasks.reverse_geocode
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings

# 中国省份英文->中文映射
PROVINCE_ZH = {
    "Anhui": "安徽", "Beijing": "北京", "Chongqing": "重庆", "Fujian": "福建",
    "Gansu": "甘肃", "Guangdong": "广东", "Guangxi": "广西", "Guizhou": "贵州",
    "Hainan": "海南", "Hebei": "河北", "Heilongjiang": "黑龙江", "Henan": "河南",
    "Hubei": "湖北", "Hunan": "湖南", "Inner Mongolia": "内蒙古",
    "Jiangsu": "江苏", "Jiangxi": "江西", "Jilin": "吉林", "Liaoning": "辽宁",
    "Ningxia": "宁夏", "Qinghai": "青海", "Shaanxi": "陕西", "Shandong": "山东",
    "Shanghai": "上海", "Shanxi": "山西", "Sichuan": "四川", "Tianjin": "天津",
    "Tibet": "西藏", "Xinjiang": "新疆", "Yunnan": "云南", "Zhejiang": "浙江",
    "Hong Kong": "香港", "Macau": "澳门", "Taiwan": "台湾",
}


def main() -> None:
    import reverse_geocoder as rg

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    # 确保列存在
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
        "SELECT asset_id, gps_lat, gps_lng FROM assets WHERE gps_lat IS NOT NULL AND gps_lng IS NOT NULL AND status = 'done'"
    ).fetchall()

    print(f"共 {len(rows)} 张图片需要反查地理信息")

    if not rows:
        print("无需处理。")
        conn.close()
        return

    coordinates = [(r["gps_lat"], r["gps_lng"]) for r in rows]
    asset_ids = [r["asset_id"] for r in rows]

    print("正在批量反查（使用 KD-Tree，速度很快）...")
    results = rg.search(coordinates)

    print("写入数据库...")
    updates = []
    for asset_id, geo in zip(asset_ids, results):
        city = geo.get("name", "")
        admin1 = geo.get("admin1", "")
        cc = geo.get("cc", "")

        # 中国地区尝试翻译省份名
        province = PROVINCE_ZH.get(admin1, admin1) if cc == "CN" else admin1

        updates.append((city, province, asset_id))

    # 批量更新
    conn.executemany(
        "UPDATE assets SET city_name = ?, province_name = ? WHERE asset_id = ?",
        updates,
    )
    conn.commit()
    conn.close()

    print(f"完成！已更新 {len(updates)} 条记录。")


if __name__ == "__main__":
    main()
