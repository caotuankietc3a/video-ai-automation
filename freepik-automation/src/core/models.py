from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IdolInfo:
    name: Optional[str]
    outfit_description: str
    pose_style: str
    body_type: Optional[str]


@dataclass
class DanceInfo:
    style: str
    bpm: Optional[int]
    energy_level: str


@dataclass
class BackgroundContext:
    location: str
    environment_details: str
    depth_and_space: str


@dataclass
class ColorMood:
    primary_palette: List[str]
    accent_colors: List[str]
    overall_mood: str
    lighting_style: str


@dataclass
class KlingPromptData:
    idol: IdolInfo
    dance: DanceInfo
    background: BackgroundContext
    color_mood: ColorMood
    extra_instructions: Optional[str]


@dataclass
class KlingPromptResult:
    prompt: str
    raw_data: KlingPromptData

