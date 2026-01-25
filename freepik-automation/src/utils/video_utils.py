from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import cv2

logger = logging.getLogger(__name__)


def _validate_video_url(url: str) -> Tuple[bool, str]:
    url_lower = url.strip().lower()
    tiktok_pattern = r"https?://((?:vm|vt|www)\.)?tiktok\.com/.*"
    if re.match(tiktok_pattern, url_lower):
        return True, "tiktok"
    youtube_patterns = [
        r"https?://(www\.)?(youtube\.com|youtu\.be)/.*",
        r"https?://(www\.)?youtube\.com/watch\?v=.*",
        r"https?://youtu\.be/.*",
    ]
    for pattern in youtube_patterns:
        if re.match(pattern, url_lower):
            return True, "youtube"
    facebook_patterns = [
        r"https?://(www\.)?facebook\.com/.*/videos/.*",
        r"https?://(www\.)?fb\.watch/.*",
        r"https?://(www\.)?fb\.com/.*/videos/.*",
        r"https?://(www\.)?m\.facebook\.com/.*/videos/.*",
    ]
    for pattern in facebook_patterns:
        if re.match(pattern, url_lower):
            return True, "facebook"
    return False, "unknown"


def download_video_from_url(url: str, output_dir: Optional[Path] = None) -> Optional[Path]:
    is_valid, _ = _validate_video_url(url)
    if not is_valid:
        raise ValueError("URL không hợp lệ. Chỉ hỗ trợ TikTok, YouTube, Facebook.")
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("Cần cài đặt yt-dlp: pip install yt-dlp")

    from ..config.constants import VIDEO_DOWNLOADS_DIR

    out_dir = output_dir or VIDEO_DOWNLOADS_DIR
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(out_dir / "%(title)s.%(ext)s")
    final_path: Optional[Path] = None

    def progress_hook(d: dict) -> None:
        nonlocal final_path
        if d.get("status") == "finished" and "filename" in d:
            final_path = Path(d["filename"])

    opts = {
        "outtmpl": out_tmpl,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": False,
        "progress_hooks": [progress_hook],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            return None
        if final_path and final_path.exists():
            return final_path
        filename = ydl.prepare_filename(info)
        p = Path(filename) if filename else None
        return p if p and p.exists() else None


def extract_first_frame(video_path: Path, output_path: Optional[Path] = None) -> Path:
    logger.info("Video utils: Extract frame đầu từ %s", video_path.name)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Không thể mở video: {video_path}")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Không thể đọc frame đầu từ video")

    if output_path is None:
        output_dir = video_path.parent / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{video_path.stem}_first_frame.jpg"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(output_path), frame)
    logger.info("Video utils: Đã lưu frame đầu -> %s", output_path)
    return output_path
