import asyncio
import logging
from typing import Optional

from .browser_automation import browser_automation
from ..data.config_manager import config_manager

logger = logging.getLogger(__name__)


class WebContentGenerator:
    def __init__(self, gemini_project_link: Optional[str] = None) -> None:
        if gemini_project_link:
            self.url = gemini_project_link
        else:
            self.url: str = config_manager.get(
                "content_generation.url",
                "https://gemini.google.com/app",
            )

    async def generate(self, prompt: str, project_config: Optional[dict] = None) -> str:
        await browser_automation.start()
        
        gemini_link = None
        if project_config:
            gemini_link = project_config.get("gemini_project_link", "")
        
        if gemini_link:
            url_to_use = gemini_link
        else:
            url_to_use = self.url
        
        await browser_automation.navigate(url_to_use)

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
        
        if project_config and not project_config.get("gemini_project_link"):
            try:
                current_url = await browser_automation.get_current_url()
                if current_url and "/app/" in current_url:
                    project_id = current_url.split("/app/")[-1].split("?")[0].split("/")[0]
                    if project_id:
                        gemini_link = f"https://gemini.google.com/app/{project_id}"
                        project_config["gemini_project_link"] = gemini_link
                        from ..data.project_manager import project_manager
                        project_file = project_config.get("file", "")
                        if project_file:
                            project_manager.update_project(project_file, {"gemini_project_link": gemini_link})
                            logger.info(f"Đã lưu gemini_project_link: {gemini_link}")
            except Exception as e:
                logger.warning(f"Không thể lưu gemini_project_link: {e}")
        
        return text.strip()