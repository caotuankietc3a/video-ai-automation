from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"
OUTPUTS_DIR = DATA_DIR / "outputs"
COOKIES_DIR = DATA_DIR / "cookies"
CONFIG_FILE = DATA_DIR / "config.json"
VIDEO_DOWNLOADS_DIR = DATA_DIR / "video_downloads"
KOL_IMAGES_DIR = OUTPUTS_DIR / "kol_images"
APP_NAME = "Freepik Idol Automation"

