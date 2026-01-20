import asyncio
import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

from ..integrations import get_ai_provider
from ..data.video_manager import video_manager
from ..config.prompts import prompt_templates
from ..data.config_manager import config_manager
from ..integrations.browser_automation import browser_automation, BrowserAutomation

if TYPE_CHECKING:
    from ..integrations.browser_automation import BrowserAutomation


logger = logging.getLogger(__name__)


class VideoAnalyzer:
    def __init__(self, project_name: str = "default") -> None:
        self.project_name = project_name
        self.provider_name: str = config_manager.get("default_model", "gemini")
        self.provider = get_ai_provider(self.provider_name)
        self.use_browser: bool = bool(
            config_manager.get("video_analysis.use_browser", True),
        )
        self.web_url: str = config_manager.get(
            "video_analysis.url",
            "https://gemini.google.com/app",
        )
    
    async def _analyze_with_api(self, video_paths: List[str]) -> str:
        all_frames: List[str] = []
        for video_path in video_paths:
            frames = video_manager.extract_frames(video_path, num_frames=10)
            all_frames.extend(frames)

        prompt = prompt_templates.get_video_analysis()

        if not self.provider.is_available():
            raise RuntimeError(f"AI provider {self.provider_name} is not available")

        analysis = await self.provider.generate_with_images(prompt, all_frames)
        return analysis

    async def _analyze_with_browser(self, video_paths: List[str], browser: Optional[BrowserAutomation] = None) -> Tuple[str, str]:
        browser = browser or browser_automation
        logger.info(f"Bắt đầu phân tích video qua Gemini Web (browser instance: {browser.instance_id})...")
        video_path = video_paths[0]
        logger.info(f"Video đầu vào: {video_path}")

        await browser.start()
        logger.info(f"Đi tới URL Gemini: {self.web_url}")
        await browser.navigate(self.web_url)
        await asyncio.sleep(5)

        logger.info("Gọi ensure_gemini_login để đảm bảo đã đăng nhập...")
        await browser.ensure_gemini_login()
        await browser.select_fast_mode()

        logger.info("Mở menu upload của Gemini...")
        await browser.click('button[aria-label="Open upload file menu"]')
        await asyncio.sleep(0.5)

        logger.info("Click nút 'Upload files'...")
        await browser.click(
            'button[data-test-id="local-images-files-uploader-button"]',
        )
        await asyncio.sleep(0.5)

        logger.info("Gán file video cho input[type=\"file\"]...")
        await browser.set_input_files('input[type="file"]', [video_path])

        logger.info("Lấy prompt VIDEO_ANALYSIS và điền vào ô chat...")
        prompt = prompt_templates.get_video_analysis()
        await browser.fill(
            'div.ql-editor.textarea.new-input-ui[contenteditable="true"], textarea, [contenteditable="true"]',
            prompt,
        )

        logger.info("Bấm nút gửi để yêu cầu Gemini phân tích video...")
        await browser.click('button[aria-label="Send message"]')

        logger.info("Chờ Gemini trả lời và lấy kết quả phân tích...")
        await browser.wait_for_selector(
            '[data-message-content], article, div.markdown, .response',
            timeout=120000,
        )
        await browser.wait_for_selector(
            '.response-container-footer',
            timeout=60000,
        )
        analysis = await browser.get_text(
            '[data-message-content], article, div.markdown, .response',
        )
        if not analysis:
            raise RuntimeError("Không lấy được kết quả phân tích video từ web UI")
        logger.info(f"Đã lấy được kết quả phân tích video, độ dài: {len(analysis)} ký tự")
        
        gemini_link = await browser.get_current_url()
        logger.info(f"Lưu Gemini link: {gemini_link}")
        
        return analysis.strip(), gemini_link
    
    async def analyze_videos(self, video_paths: List[str], project_name: Optional[str] = None, browser: Optional[BrowserAutomation] = None) -> Tuple[str, Optional[str]]:
        if not video_paths:
            raise ValueError("No video paths provided")
        
        project_name = project_name or self.project_name
        gemini_link = None

        if self.use_browser:
            analysis, gemini_link = await self._analyze_with_browser(video_paths, browser)
        else:
            analysis = await self._analyze_with_api(video_paths)
        
        from ..utils.response_saver import save_gemini_response
        save_gemini_response(project_name, "video_analysis", analysis)
        
        return analysis, gemini_link

