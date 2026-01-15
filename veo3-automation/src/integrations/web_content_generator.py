import asyncio
import logging
from typing import Optional

from .browser_automation import browser_automation
from ..data.config_manager import config_manager

logger = logging.getLogger(__name__)


class WebContentGenerator:
    def __init__(self) -> None:
        self.url: str = config_manager.get(
            "content_generation.url",
            "https://gemini.google.com/app",
        )

    async def generate(self, prompt: str) -> str:
        await browser_automation.start()
        await browser_automation.navigate(self.url)

        await browser_automation.ensure_gemini_login()
        await browser_automation.select_fast_mode()

        input_selector = 'textarea, [contenteditable="true"]'
        await browser_automation.wait_for_selector(input_selector, timeout=20000)

        await browser_automation.fill(input_selector, "")
        await asyncio.sleep(0.2)
        await browser_automation.fill(input_selector, prompt)

        send_selector = (
            'button[aria-label="Send message"], '
            'button.send-button[aria-label="Send message"], '
            'button.mat-mdc-icon-button.send-button, '
            'button[aria-label*="Gửi"], '
            'button:has-text("Send")'
        )
        try:
            await asyncio.sleep(0.5)
            await browser_automation.wait_for_selector(send_selector, timeout=10000)
            await browser_automation.click(send_selector)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"Không thể click button send: {e}")
            raise RuntimeError("Không thể gửi message, không tìm thấy button send")

        await asyncio.sleep(0.2)
        response_selector = (
            '[data-message-content], article, div.markdown, .response'
        )
        await browser_automation.wait_for_selector(
            response_selector,
            timeout=120000,
        )

        await browser_automation.wait_for_selector(
            '.response-container-footer',
            timeout=60000,
        )

        text = await browser_automation.get_text(response_selector)
        if not text:
            raise RuntimeError("Không lấy được nội dung từ web UI")
        return text.strip()