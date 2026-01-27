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
    
    async def start(self, clear_cookies: bool = False):
        """
        KHÔNG restart browser nếu đã launch.
        - Lần đầu: launch playwright + browser + context + page.
        - Các lần sau:
          - clear_cookies=True: chỉ recreate context/page (trong cùng browser) để reset session.
          - clear_cookies=False: đảm bảo context/page còn sống; nếu page chết thì recreate page.
        """
        await self._ensure_browser_launched()

        if clear_cookies:
            await self._recreate_context(storage_state=None)
        else:
            await self._ensure_context()

        await self._ensure_page()

        if clear_cookies:
            logger.info(f"Browser started (context recreated, cookies cleared) for instance: {self.instance_id}")
        else:
            logger.info(f"Browser started (ensure page) for instance: {self.instance_id}")

        if not self.headless and platform.system() == 'Darwin':
            await self._set_window_position_mac()

    async def _ensure_browser_launched(self) -> None:
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        if self.browser is not None:
            return

        launch_args: list[str] = []
        if not self.headless:
            launch_args.extend([
                f'--window-position={self.window_position_x},{self.window_position_y}',
                f'--window-size={self.window_width},{self.window_height}',
            ])

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            channel=self.channel,
            args=launch_args if launch_args else None,
        )

    async def _ensure_context(self) -> None:
        if self.context is None:
            storage_state = self._load_cookies()
            self.context = await self.browser.new_context(
                viewport={'width': self.window_width, 'height': self.window_height} if not self.headless else None,
                storage_state=storage_state,
            )
            return

        # context có thể đã bị close -> thao tác thử để phát hiện
        try:
            _ = self.context.pages
        except Exception:
            self.context = None
            await self._ensure_context()

    async def _recreate_context(self, storage_state: Optional[Dict[str, Any]] = None) -> None:
        # chỉ đóng context cũ, KHÔNG đóng browser
        try:
            if self.context is not None:
                await self.context.close()
        except Exception:
            pass
        self.context = await self.browser.new_context(
            viewport={'width': self.window_width, 'height': self.window_height} if not self.headless else None,
            storage_state=storage_state,
        )
        self.page = None

    async def _ensure_page(self) -> None:
        if self.browser is None:
            await self._ensure_browser_launched()
        await self._ensure_context()

        if self.page is not None:
            try:
                if not self.page.is_closed():
                    return
            except Exception:
                pass

        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
    
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
    
    async def _human_delay(self, min_seconds: float = 0.3, max_seconds: float = 0.8):
        import random
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def _human_mouse_move(self, x: int, y: int):
        if not self.page:
            return
        try:
            current_pos = await self.page.evaluate("""
                () => {
                    return {
                        x: window.mouseX || 0,
                        y: window.mouseY || 0
                    };
                }
            """)
            current_x = current_pos.get("x", 0) or 0
            current_y = current_pos.get("y", 0) or 0
            
            import random
            steps = random.randint(5, 10)
            for i in range(steps):
                step_x = current_x + (x - current_x) * (i + 1) / steps
                step_y = current_y + (y - current_y) * (i + 1) / steps
                await self.page.mouse.move(step_x, step_y)
                await asyncio.sleep(random.uniform(0.01, 0.03))
        except Exception:
            if self.page:
                await self.page.mouse.move(x, y)
    
    async def close_current_tab(self):
        import random
        if self.page and not self.page.is_closed():
            try:
                await self._human_delay(0.2, 0.5)
                await self.page.close()
                await self._human_delay(0.3, 0.6)
                logger.info(f"Đã đóng tab hiện tại cho instance: {self.instance_id}")
            except Exception as e:
                logger.warning(f"Lỗi khi đóng tab: {e}")
        self.page = None
    
    async def new_tab(self):
        import random
        await self._ensure_page()
        
        await self._human_delay(0.4, 0.8)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        await self._human_delay(0.3, 0.6)
        logger.info(f"Đã tạo tab mới cho instance: {self.instance_id}")
        return self.page
    
    async def navigate(self, url: str):
        await self._ensure_page()
        try:
            await self._human_delay(0.3, 0.7)
            await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            await self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
            await self._human_delay(0.5, 1.0)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during navigation, recreating page...")
                await self._ensure_page()
                await self._human_delay(0.3, 0.7)
                await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
                await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
                await self._human_delay(0.5, 1.0)
            elif "Timeout" in str(e) or "timeout" in str(e).lower():
                logger.warning(f"Navigation timeout, trying with load state...")
                try:
                    await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                    await self._human_delay(0.3, 0.6)
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
        await self._ensure_page()
        try:
            loc = self.page.locator(selector).first
            try:
                box = await loc.bounding_box()
                if box:
                    await self._human_mouse_move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await self._human_delay(0.2, 0.5)
            except Exception:
                pass

            await loc.click(timeout=self.timeout)
            await self._human_delay(0.3, 0.7)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during click, recreating page...")
                await self._ensure_page()
                await self._human_delay(0.2, 0.4)
                await self.page.locator(selector).first.click(timeout=self.timeout)
                await self._human_delay(0.3, 0.7)
            else:
                raise
    
    async def fill(self, selector: str, text: str):
        await self._ensure_page()
        try:
            await self.page.fill(selector, text)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during fill, recreating page...")
                await self._ensure_page()
                await self.page.fill(selector, text)
            else:
                raise
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        await self._ensure_page()
        try:
            await self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during wait_for_selector, recreating page...")
                await self._ensure_page()
                await self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
            else:
                raise
    
    async def get_text(self, selector: str) -> str:
        await self._ensure_page()
        try:
            return await self.page.text_content(selector) or ""
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during get_text, recreating page...")
                await self._ensure_page()
                return await self.page.text_content(selector) or ""
            else:
                raise
    
    async def query_all(self, selector: str) -> List:
        await self._ensure_page()
        try:
            return await self.page.query_selector_all(selector)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during query_all, recreating page...")
                await self._ensure_page()
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
        await self._ensure_page()
        try:
            return await self.page.evaluate(script, *args)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during evaluate, recreating page...")
                await self._ensure_page()
                return await self.page.evaluate(script, *args)
            else:
                raise
    
    async def get_current_url(self) -> str:
        await self._ensure_page()
        try:
            return self.page.url
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during get_current_url, recreating page...")
                await self._ensure_page()
                return self.page.url
            else:
                raise
    
    async def drag(self, selector: str, target_x: int, target_y: int):
        await self._ensure_page()
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
                logger.warning("Page/context destroyed during drag, recreating page...")
                await self._ensure_page()
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
        await self._ensure_page()
        try:
            await self.page.set_input_files(selector, file_paths)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                logger.warning("Page/context destroyed during set_input_files, recreating page...")
                await self._ensure_page()
                await self.page.set_input_files(selector, file_paths)
            else:
                raise

    async def ensure_gemini_login(self) -> None:
        """
        Đảm bảo đã đăng nhập Gemini.
        Sử dụng cookies nếu có, nếu không thì login bằng email/password.
        """
        logger.info("Bắt đầu kiểm tra đăng nhập Gemini...")
        
        await self._ensure_page()

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
                logger.warning("Page/context destroyed during query_selector (ensure_gemini_login), recreating page...")
                await self._ensure_page()
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
        
        await self._ensure_page()
        
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
        await self.clear_cookies()
        
        try:
            logger.info("Đang chờ form nhập email xuất hiện...")
            await self.wait_for_selector(email_selector, timeout=self.timeout)
            logger.info("Đã tìm thấy ô nhập email, đang điền email...")
            await self.fill(email_selector, email)
            await self._human_delay(0.4, 0.8)
            
            logger.info("Đã điền email, đang click Next...")
            next_button_selector = 'button:has-text("Next")'
            await self.click(next_button_selector)
            await self._human_delay(1.2, 2.2)

            for _ in range(2):
                restarted = await self._handle_google_something_went_wrong_restart()
                if not restarted:
                    break
                logger.info("Đã gặp lỗi 'Something went wrong', đang retry lần 2...")
                await self.wait_for_selector(email_selector, timeout=self.timeout)
                await self.fill(email_selector, email)
                await self._human_delay(0.4, 0.8)
                logger.info("Đang click Next...")
                await self.click(next_button_selector)
                await self._human_delay(1.2, 2.2)
            
            logger.info("Đang chờ form nhập password xuất hiện...")
            password_selector = 'input[type="password"][name="Passwd"]'
            await self.wait_for_selector(password_selector, timeout=self.timeout)
            logger.info("Đã tìm thấy ô nhập password, đang điền password...")
            await self.fill(password_selector, password)
            await self._human_delay(0.4, 0.8)
            
            logger.info("Đã điền password, đang click Next...")
            await self.click(next_button_selector)
            await self._human_delay(2.2, 3.5)
            
            logger.info("✓ Hoàn tất quá trình đăng nhập Google")
            await self._save_cookies("google")
        except Exception as e:
            logger.error(f"Lỗi khi đăng nhập Google: {e}")
            raise

    async def _handle_google_something_went_wrong_restart(self) -> bool:
        await self._ensure_page()
        try:
            has_error = False
            try:
                err_text = self.page.get_by_text("Something went wrong", exact=False)
                if await err_text.is_visible():
                    has_error = True
            except Exception:
                pass

            restart_btn = self.page.get_by_text("Restart", exact=False).first
            if has_error or await restart_btn.is_visible():
                logger.warning("Google login gặp lỗi 'Something went wrong', đang bấm Restart...")
                await restart_btn.click(timeout=10000)
                await self._human_delay(1.0, 2.0)
                return True
            return False
        except Exception:
            return False

    def _get_cookies_file_path(self, domain: str = "google") -> str:
        return os.path.join(COOKIES_DIR, f"{domain}_cookies.json")

    async def clear_cookies(self, domain: str = "google") -> None:
        if self.context:
            await self.context.clear_cookies()
        cookies_file = self._get_cookies_file_path(domain)
        if os.path.exists(cookies_file):
            try:
                os.remove(cookies_file)
                logger.info(f"Đã xóa file cookies: {cookies_file}")
            except OSError as e:
                logger.warning(f"Không thể xóa file cookies: {e}")
    
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
    
    async def simulate_human_behavior(self, duration_seconds: int = 30):
        import random
        
        if not self.page:
            return
        
        print(f"Đang mô phỏng hành vi người dùng trong {duration_seconds}s...")
        elapsed = 0
        check_interval = 2
        
        while elapsed < duration_seconds:
            try:
                viewport_size = await self.page.evaluate("""
                    () => {
                        return {
                            width: window.innerWidth,
                            height: window.innerHeight
                        };
                    }
                """)
                
                width = viewport_size.get("width", 1280)
                height = viewport_size.get("height", 720)
                
                action_type = random.randint(0, 2)
                
                if action_type == 0:
                    x = random.randint(100, max(200, width - 100))
                    y = random.randint(100, max(200, height - 100))
                    await self.page.mouse.move(x, y)
                elif action_type == 1:
                    scroll_amount = random.randint(-100, 100)
                    await self.page.evaluate(f"""
                        () => {{
                            window.scrollBy(0, {scroll_amount});
                        }}
                    """)
                else:
                    x = random.randint(100, max(200, width - 100))
                    y = random.randint(100, max(200, height - 100))
                    await self.page.mouse.move(x, y)
                
                delay = random.uniform(1.5, 3.0)
                await asyncio.sleep(delay)
                elapsed += delay
                
                if int(elapsed) % 5 < check_interval and int(elapsed) > 0:
                    print(f"  Đã mô phỏng {int(elapsed)}/{duration_seconds}s...")
                    
            except Exception as e:
                logger.warning(f"Lỗi khi mô phỏng hành vi người dùng: {e}")
                await asyncio.sleep(check_interval)
                elapsed += check_interval
        
        print(f"✓ Đã hoàn thành mô phỏng hành vi người dùng ({duration_seconds}s)")
    
    async def select_fast_mode(self) -> None:
        """
        Chọn Fast mode trong Gemini sau khi đã đăng nhập.
        Click vào button Pro và chọn option Fast.
        """
        logger.info("Bắt đầu chọn Fast mode...")
        
        await self._ensure_page()
        
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


async def stop_browser_instance(instance_id: str, close_tab_only: bool = True) -> None:
    if instance_id in _browser_instances:
        browser = _browser_instances[instance_id]
        if close_tab_only:
            try:
                await browser.close_current_tab()
                await browser.new_tab()
                logger.info(f"Đã đóng tab và mở tab mới cho instance: {instance_id}")
            except Exception as e:
                logger.warning(f"Lỗi khi đóng/mở tab cho instance {instance_id}: {e}")
        else:
            await browser.stop()
            del _browser_instances[instance_id]
            logger.info(f"Đã stop browser instance: {instance_id}")


async def stop_all_browser_instances() -> None:
    for instance_id in list(_browser_instances.keys()):
        try:
            await _browser_instances[instance_id].stop()
        except Exception:
            pass
    _browser_instances.clear()

