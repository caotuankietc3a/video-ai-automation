from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import BrowserContext, Page

from ..config.config_manager import config_manager
from ..config.constants import COOKIES_DIR

logger = logging.getLogger(__name__)

SIGN_IN_SELECTOR = 'a[aria-label="Sign in"], a[href*="ServiceLogin"]'
GEMINI_COOKIES_PATH = COOKIES_DIR / "google_cookies.json"


def load_gemini_cookies() -> Optional[Dict[str, Any]]:
    if not GEMINI_COOKIES_PATH.exists():
        return None
    try:
        data = json.loads(GEMINI_COOKIES_PATH.read_text(encoding="utf-8"))
        logger.info("Gemini: Đã load cookies từ %s", GEMINI_COOKIES_PATH)
        return data
    except Exception as e:
        logger.warning("Gemini: Không đọc được cookies: %s", e)
        return None


async def save_gemini_cookies(context: BrowserContext) -> None:
    try:
        state = await context.storage_state()
        COOKIES_DIR.mkdir(parents=True, exist_ok=True)
        GEMINI_COOKIES_PATH.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Gemini: Đã lưu cookies -> %s", GEMINI_COOKIES_PATH)
    except Exception as e:
        logger.warning("Gemini: Không lưu được cookies: %s", e)


async def check_gemini_logged_in(page: Page) -> bool:
    try:
        link = await page.query_selector(SIGN_IN_SELECTOR)
        if link is None:
            logger.info("Gemini: Đã đăng nhập (không thấy Sign in)")
            return True
        logger.info("Gemini: Chưa đăng nhập (có nút Sign in)")
        return False
    except Exception as e:
        logger.warning("Gemini: Lỗi kiểm tra login: %s", e)
        return False


async def ensure_gemini_login(
    page: Page, context: BrowserContext, timeout: float
) -> None:
    logged_in = await check_gemini_logged_in(page)
    if logged_in:
        await save_gemini_cookies(context)
        return

    email = config_manager.get("gemini_account.email", "")
    password = config_manager.get("gemini_account.password", "")
    if not email or not password:
        logger.warning(
            "Gemini: Chưa cấu hình gemini_account.email/password trong data/config.json"
        )
        return

    logger.info(
        "Gemini: Bắt đầu login với email %s***",
        email[:3] if len(email) >= 3 else "",
    )

    try:
        sign_in = await page.query_selector(SIGN_IN_SELECTOR)
        if not sign_in:
            await save_gemini_cookies(context)
            return

        await sign_in.click()
        logger.info("Gemini: Đã click Sign in")

        await page.wait_for_selector(
            'input[type="email"][id="identifierId"]', timeout=timeout
        )
        await page.fill('input[type="email"][id="identifierId"]', email)
        await page.click('button:has-text("Next")')
        logger.info("Gemini: Đã nhập email, Next")

        await page.wait_for_selector(
            'input[type="password"][name="Passwd"]', timeout=timeout
        )
        await page.fill('input[type="password"][name="Passwd"]', password)
        await page.click('button:has-text("Next")')
        logger.info("Gemini: Đã nhập password, Next")

        await asyncio.sleep(3)

        if await check_gemini_logged_in(page):
            logger.info("Gemini: Đăng nhập thành công")
            await save_gemini_cookies(context)

        try:
            agree = await page.query_selector(
                'button[data-test-id="upload-image-agree-button"], '
                'button:has-text("Agree"), button[aria-label*="Connect"]'
            )
            if agree:
                await agree.click()
                await asyncio.sleep(1)
                await save_gemini_cookies(context)
        except Exception:
            pass
    except Exception as e:
        logger.warning("Gemini: Lỗi khi login: %s", e)
