from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from ..config.config_manager import config_manager
from ..config.constants import COOKIES_DIR

logger = logging.getLogger(__name__)


@dataclass
class FreepikCredentials:
    email: str
    password: str

class FreepikVideoGeneratorFlow:
    def __init__(self, email: str, password: str, base_url: Optional[str] = None) -> None:
        self._credentials = FreepikCredentials(email=email, password=password)
        self._base_url = base_url or "https://www.freepik.com/"

    async def generate_video(
        self,
        start_image: Path,
        video_file: Path,
        kling_prompt: Optional[str] = None,
    ) -> None:
        logger.info("Freepik: Khởi tạo browser...")
        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(headless=False)

            COOKIES_DIR.mkdir(parents=True, exist_ok=True)
            cookies_file = COOKIES_DIR / "freepik_cookies.json"

            storage_state = None
            if cookies_file.exists():
                try:
                    with cookies_file.open("r", encoding="utf-8") as file:
                        storage_state = json.load(file)
                except Exception:
                    storage_state = None

            if storage_state is not None:
                context: BrowserContext = await browser.new_context(storage_state=storage_state)
                logger.info("Freepik: Dùng cookies đã lưu")
            else:
                context = await browser.new_context()

            page: Page = await context.new_page()

            await page.goto(self._base_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            logger.info("Freepik: Đã mở trang chủ")

            signin = await page.query_selector('a[data-cy="signin-button"]')
            need_login = signin is not None and await signin.is_visible()

            if need_login:
                await page.click('a[data-cy="signin-button"]')
                await page.wait_for_timeout(500)
                await page.click('button:has-text("Continue with email")')

                await page.wait_for_selector('input[name="email"]', state="visible")
                await page.fill('input[name="email"]', self._credentials.email)

                await page.wait_for_selector('input[name="password"]', state="visible")
                await page.fill('input[name="password"]', self._credentials.password)

                logger.info("Freepik: Nếu trang hiện reCAPTCHA, vui lòng giải trên trình duyệt (tối đa 90 giây).")
                await self._click_login_button(page)

                deadline = asyncio.get_running_loop().time() + 90
                while asyncio.get_running_loop().time() < deadline:
                    await asyncio.sleep(2)
                    if "log-in" not in page.url:
                        break
                await page.wait_for_timeout(2000)
            else:
                logger.info("Freepik: Đã đăng nhập (dùng cookies), bỏ qua form login.")

            await page.click('a[href*="ai-video-generator"]')
            logger.info("Freepik: Đã mở Video Generator")

            await page.wait_for_timeout(2000)

            await page.click('button#aiModelApi')
            await page.wait_for_timeout(500)
            await page.click('button[data-cy="ai-model-item-slim-kling-motion-control"]')
            logger.info("Freepik: Đã chọn model Kling Motion Control")

            await self._upload_start_image(page, start_image)
            logger.info("Freepik: Đã upload start image")

            await self._upload_video(page, video_file)
            logger.info("Freepik: Đã upload video")

            await page.wait_for_timeout(500)

            if kling_prompt:
                prompt_sel = 'textarea[data-cy="form-textarea"]'
                try:
                    await page.wait_for_selector(prompt_sel, state="visible", timeout=5000)
                    await page.fill(prompt_sel, kling_prompt)
                    logger.info("Freepik: Đã điền kling_prompt vào ô Describe your video")
                except Exception as e:
                    logger.warning("Freepik: Không điền được kling_prompt: %s", e)

            await page.wait_for_timeout(500)

            await page.click('button[data-cy="generate-button"]')
            logger.info("Freepik: Đã bấm Generate")

            await page.wait_for_timeout(10000)

            try:
                await context.storage_state(path=str(cookies_file))
            except Exception:
                pass

            await context.close()
            await browser.close()
            logger.info("Freepik: Đóng browser, xong.")

    async def _click_login_button(self, page: Page) -> None:
        try:
            await page.click("button#submit")
            return
        except Exception:
            pass
        await page.click('button:has-text("Log in")')

    async def _upload_start_image(self, page: Page, start_image: Path) -> None:
        input_selector = 'div[data-cy="video-start-frame-input"] input[type="file"]'
        await page.set_input_files(input_selector, str(start_image))

    async def _upload_video(self, page: Page, video_file: Path) -> None:
        input_selector = 'div[data-cy="video-video-input"] input[type="file"]'
        await page.set_input_files(input_selector, str(video_file))


async def generate_video_from_config(
    start_image: Path,
    video_file: Path,
    kling_prompt: Optional[str] = None,
) -> None:
    email = config_manager.get("freepik_account.email", "")
    password = config_manager.get("freepik_account.password", "")
    if not email or not password:
        raise RuntimeError("Chưa cấu hình freepik_account.email/password trong data/config.json")
    flow = FreepikVideoGeneratorFlow(email=email, password=password)
    await flow.generate_video(
        start_image=start_image,
        video_file=video_file,
        kling_prompt=kling_prompt,
    )

