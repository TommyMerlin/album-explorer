from __future__ import annotations

from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def ensure_thumbnail(
    abs_path: Path,
    source_format: str,
    output_path: Path,
    max_size: int,
    quality: int,
) -> None:
    """生成缩略图，支持 HEIC/HEIF 格式。"""
    if output_path.exists():
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # HEIC 需要注册 opener
    fmt = source_format.lower()
    if fmt in ("heic", "heif", "livp_zip"):
        from pillow_heif import register_heif_opener
        register_heif_opener()

    try:
        img = Image.open(abs_path)
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        # 转为 RGB（去除 alpha 通道，WebP 支持但保持一致性）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="WEBP", quality=quality)
    except Exception:
        # 无法处理的格式，生成占位图
        placeholder = Image.new("RGB", (max_size, max_size), (200, 200, 200))
        placeholder.save(output_path, format="WEBP", quality=50)
