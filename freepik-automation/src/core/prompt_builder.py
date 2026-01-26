from __future__ import annotations

from pathlib import Path

from .models import KlingPromptData, KlingPromptResult


def build_kling_prompt(data: KlingPromptData, template_path: Path) -> KlingPromptResult:
    template = template_path.read_text(encoding="utf-8")
    idol = data.idol
    background = data.background
    color_mood = data.color_mood

    primary_palette = ", ".join(color_mood.primary_palette) if color_mood.primary_palette else ""
    accent_colors = ", ".join(color_mood.accent_colors) if color_mood.accent_colors else ""
    extra = (data.extra_instructions or "").strip()

    prompt = template.format(
        outfit_description=idol.outfit_description or "",
        pose_style=idol.pose_style or "",
        location=background.location or "",
        environment_details=background.environment_details or "",
        depth_and_space=background.depth_and_space or "",
        primary_palette=primary_palette,
        accent_colors=accent_colors,
        overall_mood=color_mood.overall_mood or "",
        lighting_style=color_mood.lighting_style or "",
        extra_instructions=extra,
    ).strip()
    return KlingPromptResult(prompt=prompt, raw_data=data)
