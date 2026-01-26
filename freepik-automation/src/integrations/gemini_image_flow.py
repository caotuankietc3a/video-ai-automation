from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page

from ..config.config_manager import config_manager
from .gemini_browser import ensure_gemini_login, load_gemini_cookies

logger = logging.getLogger(__name__)


@dataclass
class GeminiImageConfig:
    url: str
    prompt_file: Path
    textarea_selector: str
    upload_input_selector: str
    image_selector: str
    download_timeout: int


class GeminiImageGenerator:
    def __init__(self, config: GeminiImageConfig):
        self._config = config

    async def generate_kol_image(
        self,
        idol_image_path: Path,
        first_frame_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        logger.info("Gemini KOL: Mở browser...")
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
            logger.info("Gemini KOL: Đã load trang Gemini")

            await ensure_gemini_login(page, context, float(timeout))

            await self._select_pro_mode(page)

            await self._select_create_images_tool(page)

            logger.info("Gemini KOL: Mở menu upload...")
            await page.click('button[aria-label="Open upload file menu"]')
            await asyncio.sleep(0.5)
            logger.info("Gemini KOL: Click nút Upload files...")
            await page.click(
                'button[data-test-id="local-images-files-uploader-button"]',
            )
            await asyncio.sleep(0.5)
            logger.info("Gemini KOL: Gán file idol image + first frame...")
            await page.set_input_files(
                self._config.upload_input_selector,
                [str(idol_image_path), str(first_frame_path)],
            )
            logger.info("Gemini KOL: Đã upload idol image + first frame")

            await asyncio.sleep(2)

            prompt_text = self._config.prompt_file.read_text(encoding="utf-8")
            logger.info("Gemini KOL: Đã đọc prompt từ %s", self._config.prompt_file)

            logger.info("Gemini KOL: Điền prompt vào ô chat...")
            await page.fill(
                'div.ql-editor.textarea.new-input-ui[contenteditable="true"], textarea, [contenteditable="true"]',
                prompt_text,
            )

            logger.info("Gemini KOL: Bấm nút gửi...")
            await page.click('button[aria-label="Send message"]')

            logger.info("Gemini KOL: Đã gửi prompt, chờ response (div.actions-container-v2)...")
            await page.wait_for_selector("div.actions-container-v2", timeout=120000)

            generated_image_path = await self._download_generated_image(
                page, output_path
            )
            logger.info("Gemini KOL: Đã lưu ảnh -> %s", generated_image_path)

            await context.close()
            await browser.close()

            return generated_image_path

    async def _select_pro_mode(self, page: Page) -> None:
        logger.info("Gemini KOL: Bấm chọn mode (Pro)...")
        mode_btn = page.locator(
            'button:has([data-test-id="logo-pill-label-container"])'
        )
        await mode_btn.click()
        await asyncio.sleep(0.5)
        logger.info("Gemini KOL: Chọn Pro trong menu...")
        pro_option = page.locator('button[data-test-id="bard-mode-option-pro"]')
        await pro_option.click()
        await asyncio.sleep(0.5)

    async def _select_create_images_tool(self, page: Page) -> None:
        logger.info("Gemini KOL: Bấm chọn tool Tools...")
        tools_btn = page.locator("button.toolbox-drawer-button").filter(
            has_text="Tools"
        )
        await tools_btn.click()
        await asyncio.sleep(0.5)
        logger.info("Gemini KOL: Bấm Create images...")
        create_images_btn = page.get_by_role("button", name="Create images")
        await create_images_btn.click()
        await asyncio.sleep(0.5)

    async def _download_generated_image(
        self, page: Page, output_path: Optional[Path] = None
    ) -> Path:
        if output_path is None:
            from ..config.constants import KOL_IMAGES_DIR

            KOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            output_path = KOL_IMAGES_DIR / "kol_generated.jpg"

        try:
            logger.info("Gemini KOL: Chờ button.image-button (ảnh generate) tồn tại...")
            await page.wait_for_selector(
                "button.image-button", timeout=self._config.download_timeout
            )
            await page.wait_for_selector(
                self._config.image_selector, timeout=self._config.download_timeout
            )

            image_element = await page.query_selector(self._config.image_selector)
            if image_element:
                image_src = await image_element.get_attribute("src")
                if image_src and image_src.startswith("data:image"):
                    image_data = base64.b64decode(
                        image_src.split(",")[1] if "," in image_src else image_src
                    )
                    output_path.write_bytes(image_data)
                    return output_path
                elif image_src and (
                    image_src.startswith("http://") or image_src.startswith("https://")
                ):
                    response = await page.request.get(image_src)
                    if response.ok:
                        output_path.write_bytes(await response.body())
                        return output_path

            screenshot_path = output_path.with_suffix(".png")
            await page.screenshot(path=str(screenshot_path), full_page=False)
            return screenshot_path

        except Exception as e:
            screenshot_path = output_path.with_suffix(".png")
            await page.screenshot(path=str(screenshot_path), full_page=True)
            raise RuntimeError(
                f"Không thể download ảnh từ Gemini, đã lưu screenshot: {screenshot_path}. Lỗi: {e}"
            )


def default_gemini_image_config(base_dir: Path) -> GeminiImageConfig:
    prompt_file = base_dir / "prompts" / "IDOL_KOL_GENERATION_PROMPT.txt"
    return GeminiImageConfig(
        url="https://gemini.google.com/app",
        prompt_file=prompt_file,
        textarea_selector='textarea[aria-label="Message Gemini"]',
        upload_input_selector='input[type="file"]',
        image_selector="button.image-button img",
        download_timeout=60000,
    )
