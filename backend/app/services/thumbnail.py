from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def _open_livp_zip(abs_path: Path) -> Image.Image:
    """从 livp_zip 中提取 HEIC/JPG 静态帧并打开。"""
    from pillow_heif import register_heif_opener
    register_heif_opener()

    with zipfile.ZipFile(abs_path) as zf:
        # 找到图片文件（heic/jpg/jpeg），排除视频
        image_names = [
            n for n in zf.namelist()
            if n.lower().endswith(('.heic', '.jpg', '.jpeg', '.png'))
        ]
        if not image_names:
            raise ValueError(f"zip 中无图片文件: {zf.namelist()}")

        data = zf.read(image_names[0])
        return Image.open(io.BytesIO(data))


def ensure_thumbnail(
    abs_path: Path,
    source_format: str,
    output_path: Path,
    max_size: int,
    quality: int,
) -> None:
    """生成缩略图，支持 HEIC/HEIF/livp_zip 格式。"""
    if output_path.exists():
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = source_format.lower()

    # HEIC 需要注册 opener
    if fmt in ("heic", "heif"):
        from pillow_heif import register_heif_opener
        register_heif_opener()

    try:
        if fmt == "livp_zip":
            img = _open_livp_zip(abs_path)
        else:
            img = Image.open(abs_path)

        img.thumbnail((max_size, max_size), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="WEBP", quality=quality)
    except Exception:
        placeholder = Image.new("RGB", (max_size, max_size), (200, 200, 200))
        placeholder.save(output_path, format="WEBP", quality=50)
