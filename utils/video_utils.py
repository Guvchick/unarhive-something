import json
import shutil
import subprocess


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def convert_video(src_path: str, dst_path: str, target_format: str) -> str:
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg не установлен на сервере")

    codec_map = {
        "mp4":  ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-movflags", "+faststart"],
        "webm": ["-c:v", "libvpx-vp9", "-c:a", "libopus"],
        "mkv":  ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"],
        "avi":  ["-c:v", "mpeg4", "-c:a", "mp3"],
        "mov":  ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"],
        "flv":  ["-c:v", "flv1", "-c:a", "mp3"],
        "gif":  ["-vf", "fps=10,scale=480:-1:flags=lanczos", "-loop", "0"],
    }

    extra = codec_map.get(target_format, [])
    cmd   = ["ffmpeg", "-y", "-i", src_path] + extra + [dst_path]

    # No hard timeout: a 1 GB video can take many minutes to encode.
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error:\n{result.stderr[-1500:]}")

    return dst_path


def get_video_info(path: str) -> dict:
    if not ffmpeg_available():
        return {}
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return {}
    data = json.loads(result.stdout)
    fmt          = data.get("format", {})
    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    return {
        "duration": float(fmt.get("duration", 0)),
        "size":     int(fmt.get("size", 0)),
        "width":    video_stream.get("width"),
        "height":   video_stream.get("height"),
        "codec":    video_stream.get("codec_name"),
    }
