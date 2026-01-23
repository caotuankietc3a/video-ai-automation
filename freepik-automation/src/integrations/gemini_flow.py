from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

from ..core.models import (
    IdolInfo,
    DanceInfo,
    BackgroundContext,
    ColorMood,
    KlingPromptData,
)


@dataclass
class GeminiAnalysisConfig:
    url: str
    prompt_file: Path
    textarea_selector: str
    upload_input_selector: str
    response_selector: str


class GeminiIdolAnalyzer:
    def __init__(self, config: GeminiAnalysisConfig):
        self._config = config

    async def analyze(
        self,
        idol_image_path: Path,
        dance_video_path: Path,
    ) -> KlingPromptData:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(self._config.url)

            prompt_text = self._config.prompt_file.read_text(encoding="utf-8")

            await page.set_input_files(
                self._config.upload_input_selector,
                [str(idol_image_path), str(dance_video_path)],
            )

            await page.fill(self._config.textarea_selector, prompt_text)
            await page.keyboard.press("Enter")

            await asyncio.sleep(10)

            content = await page.text_content(self._config.response_selector)

            await context.close()
            await browser.close()

            if content is None:
                raise RuntimeError("Không đọc được nội dung trả về từ Gemini")

            parsed = self._parse_json_from_text(content)
            return self._to_kling_data(parsed)

    def _parse_json_from_text(self, text: str) -> dict:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            json_lines = []
            for line in lines:
                if line.startswith("```"):
                    continue
                json_lines.append(line)
            stripped = "\n".join(json_lines).strip()
        return json.loads(stripped)

    def _to_kling_data(self, raw: dict) -> KlingPromptData:
        idol_raw = raw.get("idol") or {}
        dance_raw = raw.get("dance") or {}
        background_raw = raw.get("background") or {}
        color_raw = raw.get("color_mood") or {}

        idol = IdolInfo(
            name=self._safe_str_or_none(idol_raw.get("name")),
            outfit_description=self._safe_str(idol_raw.get("outfit_description")),
            pose_style=self._safe_str(idol_raw.get("pose_style")),
            body_type=self._safe_str_or_none(idol_raw.get("body_type")),
        )

        bpm_value = dance_raw.get("bpm")
        bpm = int(bpm_value) if isinstance(bpm_value, (int, float)) else None

        dance = DanceInfo(
            style=self._safe_str(dance_raw.get("style")),
            bpm=bpm,
            energy_level=self._safe_str(dance_raw.get("energy_level")),
        )

        background = BackgroundContext(
            location=self._safe_str(background_raw.get("location")),
            environment_details=self._safe_str(
                background_raw.get("environment_details")
            ),
            depth_and_space=self._safe_str(background_raw.get("depth_and_space")),
        )

        primary_palette_raw = color_raw.get("primary_palette") or []
        accent_colors_raw = color_raw.get("accent_colors") or []

        primary_palette = [
            str(color).strip() for color in primary_palette_raw if str(color).strip()
        ]
        accent_colors = [
            str(color).strip() for color in accent_colors_raw if str(color).strip()
        ]

        color_mood = ColorMood(
            primary_palette=primary_palette,
            accent_colors=accent_colors,
            overall_mood=self._safe_str(color_raw.get("overall_mood")),
            lighting_style=self._safe_str(color_raw.get("lighting_style")),
        )

        extra_raw = raw.get("extra_instructions")
        extra_instructions = (
            str(extra_raw).strip() if isinstance(extra_raw, str) else None
        )

        return KlingPromptData(
            idol=idol,
            dance=dance,
            background=background,
            color_mood=color_mood,
            extra_instructions=extra_instructions,
        )

    def _safe_str(self, value: Optional[object]) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _safe_str_or_none(self, value: Optional[object]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


def default_gemini_config(base_dir: Path) -> GeminiAnalysisConfig:
    prompt_file = base_dir / "prompts" / "GEMINI_IDOL_ANALYSIS.txt"
    return GeminiAnalysisConfig(
        url="https://gemini.google.com/app",
        prompt_file=prompt_file,
        textarea_selector='textarea[aria-label="Message Gemini"]',
        upload_input_selector='input[type="file"]',
        response_selector='div[data-testid="chat-response"]',
    )

