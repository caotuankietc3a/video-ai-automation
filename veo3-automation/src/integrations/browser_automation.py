from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
from typing import Optional, Dict, Any, List
import asyncio
import logging
import platform
import subprocess
import json
import os
from ..data.config_manager import config_manager
from ..config.constants import COOKIES_DIR

logger = logging.getLogger(__name__)

_browser_instances: Dict[str, "BrowserAutomation"] = {}
_instance_counter = 0


class BrowserAutomation:
    def __init__(self, instance_id: Optional[str] = None):
        global _instance_counter
        if instance_id:
            self.instance_id = instance_id
        else:
            self.instance_id = f"default_{_instance_counter}"
            _instance_counter += 1
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = config_manager.get("browser_automation.headless", False)
        self.timeout = config_manager.get("browser_automation.timeout", 30000)
        self.channel: str = config_manager.get("browser_automation.channel", "chrome")
        base_x = config_manager.get("browser_automation.window_position_x", 100)
        base_y = config_manager.get("browser_automation.window_position_y", 100)
        self.window_width = config_manager.get("browser_automation.window_width", 1280)
        self.window_height = config_manager.get("browser_automation.window_height", 720)
        
        instance_num = int(self.instance_id.split("_")[-1]) if "_" in self.instance_id else 0
        self.window_position_x = base_x + (instance_num * (self.window_width + 20))
        self.window_position_y = base_y
        
        os.makedirs(COOKIES_DIR, exist_ok=True)
        logger.info(f"BrowserAutomation instance created: {self.instance_id}")
    
    async def start(self):
        if self._is_page_valid():
            return
        try:
            if self.browser:
                await self.stop()
        except Exception:
            pass
        
        self.playwright = await async_playwright().start()
        launch_args = []
        
        if not self.headless:
            launch_args.extend([
                f'--window-position={self.window_position_x},{self.window_position_y}',
                f'--window-size={self.window_width},{self.window_height}',
            ])
        
        storage_state = self._load_cookies()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            channel=self.channel,
            args=launch_args if launch_args else None,
        )
        self.context = await self.browser.new_context(
            viewport={'width': self.window_width, 'height': self.window_height} if not self.headless else None,
            storage_state=storage_state
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        logger.info(f"Browser started for instance: {self.instance_id}")
        
        if not self.headless and platform.system() == 'Darwin':
            await self._set_window_position_mac()
    
    async def stop(self):
        logger.info(f"Stopping browser instance: {self.instance_id}")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.context = None
        self.browser = None
        self.page = None
        self.playwright = None
    
    async def navigate(self, url: str):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            await self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during navigation, restarting browser...")
                await self.start()
                await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
                await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            elif "Timeout" in str(e) or "timeout" in str(e).lower():
                logger.warning(f"Navigation timeout, trying with load state...")
                try:
                    await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass
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
    
    async def query_all(self, selector: str) -> List:
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            return await self.page.query_selector_all(selector)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                return await self.page.query_selector_all(selector)
            else:
                raise
    
    async def get_text_from_last_element(self, selector: str) -> str:
        elements = await self.query_all(selector)
        if not elements:
            return ""
        last_element = elements[-1]
        try:
            return await last_element.text_content() or ""
        except Exception:
            return ""
    
    async def wait_for_thinking_to_finish(self, timeout: Optional[int] = None) -> None:
        thinking_selector = 'bard-avatar.thinking, .avatar.thinking, .bard-avatar.thinking'
        max_wait = timeout or 120000
        waited = 0
        check_interval = 1000
        
        while waited < max_wait:
            try:
                thinking_elements = await self.query_all(thinking_selector)
                if not thinking_elements:
                    logger.debug("Không còn thinking animation")
                    await asyncio.sleep(1)
                    return
                await asyncio.sleep(check_interval / 1000)
                waited += check_interval
            except Exception as e:
                logger.warning(f"Lỗi khi chờ thinking finish: {e}")
                await asyncio.sleep(1)
                waited += 1000
        
        logger.warning("Timeout khi chờ thinking animation kết thúc, tiếp tục...")
    
    async def screenshot(self, path: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.screenshot(path=path)
    
    async def evaluate(self, script: str, *args):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            return await self.page.evaluate(script, *args)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                return await self.page.evaluate(script, *args)
            else:
                raise
    
    async def get_current_url(self) -> str:
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            return self.page.url
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                return self.page.url
            else:
                raise
    
    async def drag(self, selector: str, target_x: int, target_y: int):
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            element = await self.page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                if box:
                    await self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    await self.page.mouse.down()
                    await self.page.mouse.move(target_x, target_y)
                    await self.page.mouse.up()
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed, restarting browser...")
                await self.start()
                element = await self.page.query_selector(selector)
                if element:
                    box = await element.bounding_box()
                    if box:
                        await self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        await self.page.mouse.down()
                        await self.page.mouse.move(target_x, target_y)
                        await self.page.mouse.up()
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
        Sử dụng cookies nếu có, nếu không thì login bằng email/password.
        """
        logger.info("Bắt đầu kiểm tra đăng nhập Gemini...")
        
        if not self.page:
            await self.start()

        gemini_url = config_manager.get("video_analysis.url", "https://gemini.google.com/app")
        
        is_logged_in = await self._check_login_status(gemini_url)
        
        if is_logged_in:
            logger.info("✓ Đã đăng nhập Gemini (sử dụng cookies)")
            await self._save_cookies("google")
            return

        email = config_manager.get("gemini_account.email", "")
        password = config_manager.get("gemini_account.password", "")
        if not email or not password:
            logger.warning("Không có cấu hình email/password cho Gemini, bỏ qua đăng nhập")
            return

        logger.info(f"Chưa đăng nhập, bắt đầu login với email: {email[:3]}***")

        try:
            sign_in_link = await self.page.query_selector(
                'a[aria-label="Sign in"], a[href*="ServiceLogin"]'
            )
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during query_selector, restarting browser...")
                await self.start()
                await self.navigate(gemini_url)
                sign_in_link = await self.page.query_selector(
                    'a[aria-label="Sign in"], a[href*="ServiceLogin"]'
                )
            else:
                raise
        
        if not sign_in_link:
            logger.info("Đã đăng nhập Gemini rồi, không cần login lại")
            await self._save_cookies("google")
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

        logger.info("Đang chờ hoàn tất đăng nhập (3 giây)...")
        await self.page.wait_for_timeout(3000)
        
        is_logged_in_after = await self._check_login_status(gemini_url)
        if is_logged_in_after:
            logger.info("✓ Đăng nhập Gemini thành công")
            await self._save_cookies("google")
        else:
            logger.warning("⚠ Có thể đăng nhập chưa hoàn tất")
        
        logger.info("Kiểm tra hộp thoại điều khoản...")

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
                await asyncio.sleep(1)
                await self._save_cookies("google")
            else:
                logger.info("Không tìm thấy hộp thoại điều khoản Gemini, bỏ qua bước đồng ý")
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page context destroyed during query_selector, bỏ qua bước đồng ý")
            else:
                logger.warning(f"Lỗi khi cố gắng đồng ý điều khoản Gemini: {e}")

    async def login_to_google(self) -> None:
        """
        Đăng nhập vào Google account sử dụng cookies nếu có, nếu không thì dùng email/password.
        Method này có thể tái sử dụng cho các flow khác nhau.
        """
        logger.info("Bắt đầu quá trình đăng nhập Google...")
        
        if not self._is_page_valid():
            await self.start()
        if not self.page:
            raise RuntimeError("Browser not started")
        
        current_url = await self.get_current_url()
        if current_url and "accounts.google.com" not in current_url:
            logger.info("Không phải trang đăng nhập Google, bỏ qua")
            return
        
        email_selector = 'input[type="email"][id="identifierId"], input[type="email"][name="identifier"]'
        try:
            email_input = await self.page.query_selector(email_selector)
            if not email_input:
                logger.info("Không tìm thấy form đăng nhập, có thể đã đăng nhập rồi")
                await self._save_cookies("google")
                return
        except Exception:
            pass
        
        email = config_manager.get("gemini_account.email", "")
        password = config_manager.get("gemini_account.password", "")
        if not email or not password:
            logger.warning("Không có cấu hình email/password, bỏ qua đăng nhập")
            return
        
        logger.info(f"Chưa đăng nhập, bắt đầu login với email: {email[:3]}***")
        
        try:
            logger.info("Đang chờ form nhập email xuất hiện...")
            await self.wait_for_selector(email_selector, timeout=self.timeout)
            logger.info("Đã tìm thấy ô nhập email, đang điền email...")
            await self.fill(email_selector, email)
            await asyncio.sleep(0.5)
            
            logger.info("Đã điền email, đang click Next...")
            next_button_selector = 'button:has-text("Next")'
            await self.click(next_button_selector)
            await asyncio.sleep(2)
            
            logger.info("Đang chờ form nhập password xuất hiện...")
            password_selector = 'input[type="password"][name="Passwd"]'
            await self.wait_for_selector(password_selector, timeout=self.timeout)
            logger.info("Đã tìm thấy ô nhập password, đang điền password...")
            await self.fill(password_selector, password)
            await asyncio.sleep(0.5)
            
            logger.info("Đã điền password, đang click Next...")
            await self.click(next_button_selector)
            await asyncio.sleep(3)
            
            logger.info("✓ Hoàn tất quá trình đăng nhập Google")
            await self._save_cookies("google")
        except Exception as e:
            logger.error(f"Lỗi khi đăng nhập Google: {e}")
            raise

    def _get_cookies_file_path(self, domain: str = "google") -> str:
        """Lấy đường dẫn file cookies cho domain"""
        return os.path.join(COOKIES_DIR, f"{domain}_cookies.json")
    
    def _load_cookies(self, domain: str = "google") -> Optional[Dict[str, Any]]:
        """Load cookies từ file"""
        cookies_file = self._get_cookies_file_path(domain)
        if os.path.exists(cookies_file):
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    storage_state = json.load(f)
                    logger.info(f"Đã load cookies từ {cookies_file}")
                    return storage_state
            except Exception as e:
                logger.warning(f"Không thể load cookies: {e}")
        return None
    
    async def _save_cookies(self, domain: str = "google") -> bool:
        """Lưu cookies vào file"""
        if not self.context:
            return False
        
        try:
            storage_state = await self.context.storage_state()
            cookies_file = self._get_cookies_file_path(domain)
            
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Đã lưu cookies vào {cookies_file}")
            return True
        except Exception as e:
            logger.warning(f"Không thể lưu cookies: {e}")
            return False
    
    async def _check_login_status(self, url: str, sign_in_selector: str = 'a[aria-label="Sign in"], a[href*="ServiceLogin"]') -> bool:
        """Kiểm tra xem đã đăng nhập chưa"""
        if not self.page:
            return False
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            await asyncio.sleep(2)
            
            sign_in_link = await self.page.query_selector(sign_in_selector)
            is_logged_in = sign_in_link is None
            
            if is_logged_in:
                logger.info("Đã đăng nhập (không tìm thấy nút Sign in)")
            else:
                logger.info("Chưa đăng nhập (tìm thấy nút Sign in)")
            
            return is_logged_in
        except Exception as e:
            logger.warning(f"Lỗi khi kiểm tra trạng thái đăng nhập: {e}")
            return False
    
    async def _set_window_position_mac(self) -> None:
        """
        Đặt vị trí cửa sổ browser cố định trên Mac bằng AppleScript
        """
        try:
            await asyncio.sleep(1)
            
            app_name = "Google Chrome" if self.channel == "chrome" else "Chromium"
            
            applescript = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set frontmost to true
                    delay 0.2
                    try
                        set position of window 1 to {{{self.window_position_x}, {self.window_position_y}}}
                        set size of window 1 to {{{self.window_width}, {self.window_height}}}
                    end try
                end tell
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.warning(f"Lỗi khi đặt vị trí cửa sổ: {stderr.decode() if stderr else 'Unknown error'}")
            
            await asyncio.sleep(0.3)
            
            applescript_force = f'''
            tell application "{app_name}"
                activate
            end tell
            tell application "System Events"
                tell process "{app_name}"
                    try
                        set value of attribute "AXPosition" of window 1 to {{{self.window_position_x}, {self.window_position_y}}}
                        set value of attribute "AXSize" of window 1 to {{{self.window_width}, {self.window_height}}}
                    end try
                end tell
            end tell
            '''
            
            process_force = await asyncio.create_subprocess_exec(
                'osascript', '-e', applescript_force,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process_force.communicate()
            
        except Exception as e:
            logger.warning(f"Không thể đặt vị trí cửa sổ trên Mac: {e}")
    
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


browser_automation = BrowserAutomation(instance_id="global_0")


def get_browser_instance(instance_id: str) -> BrowserAutomation:
    if instance_id not in _browser_instances:
        _browser_instances[instance_id] = BrowserAutomation(instance_id=instance_id)
    return _browser_instances[instance_id]


async def stop_browser_instance(instance_id: str) -> None:
    if instance_id in _browser_instances:
        await _browser_instances[instance_id].stop()
        del _browser_instances[instance_id]


async def stop_all_browser_instances() -> None:
    for instance_id in list(_browser_instances.keys()):
        try:
            await _browser_instances[instance_id].stop()
        except Exception:
            pass
    _browser_instances.clear()

