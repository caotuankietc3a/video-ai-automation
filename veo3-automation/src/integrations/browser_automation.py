from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, Dict, Any, List
import asyncio
import logging
from ..data.config_manager import config_manager

logger = logging.getLogger(__name__)


class BrowserAutomation:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = config_manager.get("browser_automation.headless", False)
        self.timeout = config_manager.get("browser_automation.timeout", 30000)
        # Sử dụng Chrome (channel='chrome') nếu được cấu hình, mặc định dùng Chrome
        self.channel: str = config_manager.get("browser_automation.channel", "chrome")
    
    async def start(self):
        if self._is_page_valid():
            return
        try:
            if self.browser:
                await self.stop()
        except Exception:
            pass
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            channel=self.channel,
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
    
    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        self.context = None
        self.browser = None
        self.page = None
    
    async def navigate(self, url: str):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            await self.page.wait_for_timeout(2000)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during navigation, restarting browser...")
                await self.start()
                await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                await self.page.wait_for_timeout(2000)
            else:
                raise
    
    def _is_page_valid(self) -> bool:
        if not self.page:
            return False
        try:
            return not self.page.is_closed()
        except Exception:
            return False
    
    async def click(self, selector: str):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.click(selector)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                await self.page.click(selector)
            else:
                raise
    
    async def fill(self, selector: str, text: str):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.fill(selector, text)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                await self.page.fill(selector, text)
            else:
                raise
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                await self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
            else:
                raise
    
    async def get_text(self, selector: str) -> str:
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            return await self.page.text_content(selector) or ""
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                return await self.page.text_content(selector) or ""
            else:
                raise
    
    async def screenshot(self, path: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.screenshot(path=path)
    
    async def evaluate(self, script: str):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                return await self.page.evaluate(script)
            else:
                raise

    async def set_input_files(self, selector: str, file_paths: List[str]) -> None:
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.set_input_files(selector, file_paths)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                await self.page.set_input_files(selector, file_paths)
            else:
                raise

    async def ensure_gemini_login(self) -> None:
        """
        Đảm bảo đã đăng nhập Gemini.
        Nếu thấy nút 'Sign in' thì tự động login bằng email/password trong config.
        """
        logger.info("Bắt đầu kiểm tra đăng nhập Gemini...")
        
        if not self.page:
            await self.start()

        email = config_manager.get("gemini_account.email", "")
        password = config_manager.get("gemini_account.password", "")
        if not email or not password:
            logger.warning("Không có cấu hình email/password cho Gemini, bỏ qua đăng nhập")
            return

        logger.info(f"Đã tìm thấy cấu hình email: {email[:3]}***")

        # Kiểm tra xem còn nút Sign in không
        try:
            sign_in_link = await self.page.query_selector(
                'a[aria-label="Sign in"], a[href*="ServiceLogin"]'
            )
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during query_selector, restarting browser...")
                gemini_url = config_manager.get("video_analysis.url", "https://gemini.google.com/app")
                await self.start()
                await self.navigate(gemini_url)
                sign_in_link = await self.page.query_selector(
                    'a[aria-label="Sign in"], a[href*="ServiceLogin"]'
                )
            else:
                raise
        
        if not sign_in_link:
            logger.info("Đã đăng nhập Gemini rồi, không cần login lại")
            return

        logger.info("Tìm thấy nút Sign in, bắt đầu quá trình đăng nhập...")
        await sign_in_link.click()
        logger.info("Đã click nút Sign in")
        
        logger.info("Đang chờ form nhập email xuất hiện...")
        await self.page.wait_for_selector(
            'input[type="email"][id="identifierId"]',
            timeout=self.timeout,
        )
        logger.info("Đã tìm thấy ô nhập email, đang điền email...")
        await self.page.fill('input[type="email"][id="identifierId"]', email)
        logger.info("Đã điền email, đang click Next...")
        await self.page.click('button:has-text("Next")')

        logger.info("Đang chờ form nhập password xuất hiện...")
        await self.page.wait_for_selector(
            'input[type="password"][name="Passwd"]',
            timeout=self.timeout,
        )
        logger.info("Đã tìm thấy ô nhập password, đang điền password...")
        await self.page.fill('input[type="password"][name="Passwd"]', password)
        logger.info("Đã điền password, đang click Next...")
        await self.page.click('button:has-text("Next")')

        logger.info("Đang chờ hoàn tất đăng nhập (2 giây)...")
        await self.page.wait_for_timeout(2000)
        logger.info("Hoàn tất quá trình đăng nhập Gemini, kiểm tra hộp thoại điều khoản...")

        try:
            agree_button = await self.page.query_selector(
                'button[data-test-id="upload-image-agree-button"], '
                'button[aria-label*="Connect"][mat-dialog-close], '
                'button:has-text("Agree")'
            )
            if agree_button:
                logger.info("Tìm thấy nút đồng ý điều khoản, tiến hành click...")
                await agree_button.click()
                logger.info("Đã đồng ý điều khoản Gemini thành công")
            else:
                logger.info("Không tìm thấy hộp thoại điều khoản Gemini, bỏ qua bước đồng ý")
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during query_selector, bỏ qua bước đồng ý")
            else:
                logger.warning(f"Lỗi khi cố gắng đồng ý điều khoản Gemini: {e}")

    async def select_fast_mode(self) -> None:
        """
        Chọn Fast mode trong Gemini sau khi đã đăng nhập.
        Click vào button Pro và chọn option Fast.
        """
        logger.info("Bắt đầu chọn Fast mode...")
        
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        
        try:
            pro_button_selector = (
                'button.input-area-switch, '
                'button[class*="input-area-switch"], '
                'button.mat-mdc-button-base.input-area-switch'
            )
            
            logger.info("Đang tìm button Pro...")
            await self.page.wait_for_selector(pro_button_selector, timeout=10000)
            await asyncio.sleep(0.5)
            
            logger.info("Click vào button Pro để mở menu...")
            await self.page.click(pro_button_selector)
            await asyncio.sleep(1)
            
            fast_mode_selector = (
                'button[data-test-id="bard-mode-option-fast"], '
                'button[data-mode-id="56fdd199312815e2"], '
                'button.bard-mode-list-button[data-test-id="bard-mode-option-fast"]'
            )
            
            logger.info("Đang tìm option Fast trong menu...")
            await self.page.wait_for_selector(fast_mode_selector, timeout=10000)
            await asyncio.sleep(0.5)
            
            logger.info("Click vào option Fast...")
            await self.page.click(fast_mode_selector)
            await asyncio.sleep(1)
            
            logger.info("Đã chọn Fast mode thành công")
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during select_fast_mode, bỏ qua")
            else:
                logger.warning(f"Không thể chọn Fast mode: {e}, tiếp tục với mode mặc định")


browser_automation = BrowserAutomation()

