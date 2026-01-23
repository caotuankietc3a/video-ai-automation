from __future__ import annotations

from .models import KlingPromptData, KlingPromptResult


def build_kling_prompt(data: KlingPromptData) -> KlingPromptResult:
    idol = data.idol
    dance = data.dance
    background = data.background
    color_mood = data.color_mood

    primary_palette = ", ".join(color_mood.primary_palette)
    accent_colors = ", ".join(color_mood.accent_colors)

    idol_name_segment = f"{idol.name} " if idol.name else ""

    base_prompt = (
        f"A dynamic TikTok Vinahouse dance video of {idol_name_segment}"
        f"{idol.outfit_description}, performing a {dance.style} routine "
        f"with {dance.energy_level} energy at around {dance.bpm} BPM. "
        f"The scene takes place in {background.location}, "
        f"surrounded by {background.environment_details}, with clear depth and space: "
        f"{background.depth_and_space}. "
        f"Color palette: {primary_palette} with accent colors of {accent_colors}, "
        f"creating an overall {color_mood.overall_mood} atmosphere using "
        f"{color_mood.lighting_style} lighting. "
        "The framing keeps the idol as the clear main subject, with smooth camera motion "
        "suitable for vertical short-form video."
    )

    if data.extra_instructions:
        base_prompt = f"{base_prompt} {data.extra_instructions.strip()}"

    return KlingPromptResult(prompt=base_prompt, raw_data=data)

