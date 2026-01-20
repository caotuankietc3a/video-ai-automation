import asyncio
import logging
from typing import Optional, TYPE_CHECKING

from .browser_automation import browser_automation, BrowserAutomation
from ..data.config_manager import config_manager

if TYPE_CHECKING:
    from .browser_automation import BrowserAutomation

logger = logging.getLogger(__name__)


class WebContentGenerator:
    def __init__(self, gemini_project_link: Optional[str] = None, browser: Optional[BrowserAutomation] = None) -> None:
        self.browser = browser or browser_automation
        if gemini_project_link:
            self.url = gemini_project_link
        else:
            self.url: str = config_manager.get(
                "content_generation.url",
                "https://gemini.google.com/app",
            )

    async def generate(self, prompt: str, project_config: Optional[dict] = None) -> str:
        browser = self.browser
        logger.info(f"Bắt đầu generate content qua Gemini Web (browser instance: {browser.instance_id})")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        await browser.start()
        logger.debug("Browser automation đã khởi động")
        
        gemini_link = None
        if project_config:
            gemini_link = project_config.get("gemini_project_link", "")
        
        if gemini_link:
            url_to_use = gemini_link
            logger.info(f"Sử dụng gemini_project_link: {gemini_link}")
        else:
            url_to_use = self.url
            logger.info(f"Sử dụng URL mặc định: {url_to_use}")
        
        logger.info(f"Điều hướng đến URL: {url_to_use}")
        await browser.navigate(url_to_use)

        logger.info("Đảm bảo đã đăng nhập vào Gemini")
        await browser.ensure_gemini_login()
        logger.info("Chọn chế độ Fast mode")
        await browser.select_fast_mode()

        input_selector = 'textarea, [contenteditable="true"]'
        logger.debug(f"Chờ input selector: {input_selector}")
        await browser.wait_for_selector(input_selector, timeout=20000)

        logger.info("Điền prompt vào input field")
        await browser.fill(input_selector, "")
        await asyncio.sleep(0.2)
        await browser.fill(input_selector, prompt)
        logger.debug("Đã điền prompt thành công")

        send_selector = (
            'button[aria-label="Send message"], '
            'button.send-button[aria-label="Send message"], '
            'button.mat-mdc-icon-button.send-button, '
            'button[aria-label*="Gửi"], '
            'button:has-text("Send")'
        )
        try:
            await asyncio.sleep(0.5)
            logger.debug("Chờ button send xuất hiện")
            await browser.wait_for_selector(send_selector, timeout=10000)
            logger.info("Click button send để gửi message")
            await browser.click(send_selector)
            await asyncio.sleep(0.5)
            logger.debug("Đã gửi message thành công")
        except Exception as e:
            logger.error(f"Không thể click button send: {e}")
            raise RuntimeError("Không thể gửi message, không tìm thấy button send")

        await asyncio.sleep(1)
        
        logger.info("Chờ avatar thinking animation kết thúc...")
        await browser.wait_for_thinking_to_finish(timeout=120000)
        logger.debug("Thinking animation đã kết thúc")
        
        response_selector = (
            '[data-message-content], article, div.markdown, .response'
        )
        logger.info("Chờ response từ Gemini xuất hiện (timeout: 120s)")
        await browser.wait_for_selector(
            response_selector,
            timeout=120000,
        )
        logger.debug("Response container đã xuất hiện")
        
        await asyncio.sleep(2)

        logger.info("Chờ response hoàn tất bằng cách kiểm tra footer...")
        footer_selector = '.response-container-footer'
        max_wait = 60000
        waited = 0
        check_interval = 1000
        
        while waited < max_wait:
            try:
                footer_elements = await browser.query_all(footer_selector)
                if len(footer_elements) >= 2:
                    logger.debug(f"Tìm thấy {len(footer_elements)} footer elements, response cuối cùng đã hoàn tất")
                    break
                elif len(footer_elements) == 1:
                    await asyncio.sleep(check_interval / 1000)
                    waited += check_interval
                    continue
                else:
                    await asyncio.sleep(check_interval / 1000)
                    waited += check_interval
            except Exception as e:
                logger.warning(f"Lỗi khi chờ footer: {e}")
                await asyncio.sleep(1)
                waited += 1000
        
        logger.debug("Response đã hoàn tất")

        logger.info("Lấy nội dung response cuối cùng từ web UI")
        text = await browser.get_text_from_last_element(response_selector)
        if not text:
            logger.error("Không lấy được nội dung từ web UI")
            raise RuntimeError("Không lấy được nội dung từ web UI")
        
        logger.info(f"Đã lấy được response, độ dài: {len(text)} characters")
        
        if project_config and not project_config.get("gemini_project_link"):
            try:
                logger.debug("Kiểm tra và lưu gemini_project_link")
                current_url = await browser.get_current_url()
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
        
        logger.info("Hoàn thành generate content")
        return text.strip()