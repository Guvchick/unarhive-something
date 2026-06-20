from PIL import Image
import os


def convert_image(src_path: str, dst_path: str, target_format: str) -> str:
    fmt = target_format.upper()
    if fmt == "JPG":
        fmt = "JPEG"

    with Image.open(src_path) as img:
        # JPEG doesn't support transparency — flatten to white background
        if fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif fmt != "JPEG" and img.mode == "P":
            img = img.convert("RGBA")

        save_kwargs = {}
        if fmt == "JPEG":
            save_kwargs["quality"] = 95
        elif fmt == "WEBP":
            save_kwargs["quality"] = 90

        img.save(dst_path, format=fmt, **save_kwargs)

    return dst_path


def get_image_info(path: str) -> dict:
    with Image.open(path) as img:
        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format or os.path.splitext(path)[1].lstrip(".").upper(),
        }
