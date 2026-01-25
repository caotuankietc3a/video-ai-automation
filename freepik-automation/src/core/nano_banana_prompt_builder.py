from __future__ import annotations

from pathlib import Path
from typing import Optional

from .models import IdolInfo


def build_nano_banana_prompt(
    idol_info: IdolInfo,
    pose_style: str,
    background_location: str = "modern minimalist studio",
    aspect_ratio: str = "9:16",
    framing: str = "full body",
) -> str:
    idol_name_segment = f"{idol_info.name} " if idol_info.name else ""

    primary_palette = "white, soft gray, elegant black"
    accent_colors = "subtle highlights"
    overall_mood = "elegant and modern"
    lighting_style = "soft studio lighting"

    prompt = (
        f"{idol_name_segment}"
        f"{idol_info.outfit_description}, "
        f"{pose_style}, "
        f"in {background_location}, "
        f"color palette: {primary_palette} with {accent_colors}, "
        f"creating an {overall_mood} atmosphere using {lighting_style}, "
        f"{framing} framing, "
        f"aspect ratio {aspect_ratio}, "
        f"high quality, professional photography, sharp focus, detailed"
    )

    if idol_info.body_type:
        prompt = f"{prompt}, {idol_info.body_type} body type"

    return prompt


