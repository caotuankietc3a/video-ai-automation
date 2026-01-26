from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page

from ..config.config_manager import config_manager
from .gemini_browser import (
    ensure_gemini_login,
    load_gemini_cookies,
    save_gemini_cookies,
)
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


logger = logging.getLogger(__name__)

RESPONSE_FOOTER_SELECTOR = ".response-container-footer"


class GeminiIdolAnalyzer:
    def __init__(self, config: GeminiAnalysisConfig):
        self._config = config

    async def analyze(
        self,
        idol_image_path: Path,
        dance_video_path: Path,
    ) -> KlingPromptData:
        logger.info("Gemini analyze: Mở browser, vào %s", self._config.url)
        timeout = config_manager.get("browser_automation.timeout", 30000)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            storage = load_gemini_cookies()
            context = await browser.new_context(
                storage_state=storage if storage else None
            )
            context.set_default_timeout(timeout)
            page = await context.new_page()

            await page.goto(self._config.url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            logger.info("Gemini analyze: Đã load trang Gemini")

            await ensure_gemini_login(page, context, float(timeout))

            prompt_text = self._config.prompt_file.read_text(encoding="utf-8")
            logger.info("Gemini analyze: Mở menu upload...")
            await page.click('button[aria-label="Open upload file menu"]')
            await asyncio.sleep(0.5)
            logger.info("Gemini analyze: Click nút Upload files...")
            await page.click(
                'button[data-test-id="local-images-files-uploader-button"]',
            )
            await asyncio.sleep(0.5)
            logger.info("Gemini analyze: Gán file idol image + dance video...")
            await page.set_input_files(
                self._config.upload_input_selector,
                [str(idol_image_path), str(dance_video_path)],
            )
            logger.info("Gemini analyze: Đã upload idol image + dance video")

            await asyncio.sleep(2)

            logger.info("Gemini analyze: Điền prompt vào ô chat...")
            await page.fill(
                'div.ql-editor.textarea.new-input-ui[contenteditable="true"], textarea, [contenteditable="true"]',
                prompt_text,
            )
            logger.info("Gemini analyze: Bấm gửi...")
            await page.click('button[aria-label="Send message"]')
            logger.info("Gemini analyze: Đã gửi prompt, đợi phản hồi...")

            await page.wait_for_selector(self._config.response_selector, timeout=120000)
            await asyncio.sleep(2)

            await self._wait_for_response_footer(page, max_wait=60000)
            content = await self._get_text_from_last_element(
                page, self._config.response_selector
            )

            await save_gemini_cookies(context)
            await context.close()
            await browser.close()

            if not (content or "").strip():
                raise RuntimeError("Không đọc được nội dung trả về từ Gemini")

            logger.info("Gemini analyze: Đã nhận phản hồi, parse JSON...")
            parsed = self._parse_json_from_text(content)
            data = self._to_kling_data(parsed)
            logger.info("Gemini analyze: Xong, trả về KlingPromptData")
            return data

    async def _wait_for_response_footer(
        self, page: Page, max_wait: int = 60000
    ) -> None:
        waited = 0
        check_interval = 1000
        while waited < max_wait:
            try:
                footers = await page.query_selector_all(RESPONSE_FOOTER_SELECTOR)
                if len(footers) >= 2:
                    return
                await asyncio.sleep(check_interval / 1000)
                waited += check_interval
            except Exception as e:
                logger.warning("Gemini analyze: Lỗi chờ footer: %s", e)
                await asyncio.sleep(1)
                waited += 1000

    async def _get_text_from_last_element(self, page: Page, selector: str) -> str:
        elements = await page.query_selector_all(selector)
        if not elements:
            return ""
        for el in reversed(elements):
            try:
                txt = (await el.text_content()) or ""
                if "{" in txt and "}" in txt and "idol" in txt:
                    return txt
            except Exception:
                continue
        try:
            return (await elements[-1].text_content()) or ""
        except Exception:
            return ""

    def _parse_json_from_text(self, text: str) -> dict:
        raw = (text or "").strip()
        if not raw:
            raise ValueError(
                "Nội dung response trống. Kiểm tra prompt Gemini và response selector."
            )
        stripped = raw
        if "```" in stripped:
            parts = re.split(r"```(?:json)?\s*\n?", stripped)
            for part in parts:
                part = part.split("```")[0].strip()
                if part.startswith("{") and "idol" in part:
                    stripped = part
                    break
            else:
                block = re.search(r"```(?:json)?\s*\n?([\s\S]*?)```", stripped)
                if block:
                    stripped = block.group(1).strip()
        if not stripped.startswith("{"):
            match = re.search(r"\{[\s\S]*\}", stripped)
            if match:
                stripped = match.group(0)
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as e:
            snippet = (raw[:500] + "…") if len(raw) > 500 else raw
            raise ValueError(
                f"Không parse được JSON từ Gemini. Lỗi: {e}. Đoạn response: {snippet!r}"
            ) from e

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
        response_selector='[data-message-content], article, div.markdown, .response',
    )

