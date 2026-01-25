from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2

logger = logging.getLogger(__name__)


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
