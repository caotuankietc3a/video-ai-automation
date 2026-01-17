import asyncio
from typing import List, Dict, Any, Optional
from .browser_automation import browser_automation
from .gemini_client import GeminiClient
from ..data.config_manager import config_manager

class VEO3Flow:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.flow_url = "https://labs.google/fx/tools/flow"
    
    async def _navigate_to_project(self, project_config: Dict[str, Any]) -> bool:
        project_link = project_config.get("project_link", "")
        is_new_project = False
        
        if project_link:
            await browser_automation.navigate(project_link)
            await asyncio.sleep(3)
            await browser_automation.login_to_google()
            await asyncio.sleep(2)
        else:
            is_new_project = True
            await browser_automation.navigate(self.flow_url)
            await asyncio.sleep(2)
            
            create_with_flow_selector = 'button:has-text("Create with Flow")'
            await browser_automation.wait_for_selector(create_with_flow_selector, timeout=60000)
            await browser_automation.click(create_with_flow_selector)
            await asyncio.sleep(2)
            
            await browser_automation.login_to_google()
            await asyncio.sleep(3)
            
            new_project_selector = 'button:has-text("New project")'
            await browser_automation.wait_for_selector(new_project_selector, timeout=10000)
            await browser_automation.click(new_project_selector)
            await asyncio.sleep(2)
            
            current_url = await browser_automation.get_current_url()
            if current_url and "/project/" in current_url:
                project_id = current_url.split("/project/")[-1].split("?")[0]
                project_link = f"https://labs.google/fx/tools/flow/project/{project_id}"
                project_config["project_link"] = project_link
                from ..data.project_manager import project_manager
                project_file = project_config.get("file", "")
                if project_file:
                    project_manager.update_project(project_file, {"project_link": project_link})
        
        return is_new_project
    
    async def _click_scenebuilder(self):
        try:
            scenebuilder_button_selector = (
                'button:has-text("Scenebuilder"), '
                'button.sc-da5b7836-6:has-text("Scenebuilder"), '
                'button.kNmMDQ:has-text("Scenebuilder")'
            )
            await browser_automation.wait_for_selector(scenebuilder_button_selector, timeout=10000)
            await browser_automation.click(scenebuilder_button_selector)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"Warning: Không thể click Scenebuilder: {e}, tiếp tục bình thường")
            return False
    
    async def _configure_aspect_ratio(self, project_config: Dict[str, Any]):
        aspect_ratio = project_config.get("aspect_ratio", "Khổ ngang (16:9)")
        is_portrait = "dọc" in aspect_ratio or "Portrait" in aspect_ratio or "9:16" in aspect_ratio
        
        try:
            settings_button_selector = (
                'button[aria-haspopup="dialog"][aria-controls*="radix"]:has(i.material-icons-outlined:has-text("tune")), '
                'button[aria-label*="Settings"][aria-haspopup="dialog"], '
                'button:has(i.material-icons-outlined):has-text("Settings")'
            )
            await browser_automation.wait_for_selector(settings_button_selector, timeout=5000)
            await browser_automation.click(settings_button_selector)
            await asyncio.sleep(1.5)
            
            aspect_ratio_button_selector = (
                'button[role="combobox"][aria-controls*="radix"]:has-text("Aspect Ratio"), '
                'button[role="combobox"]:has(span:has-text("Aspect Ratio"))'
            )
            await browser_automation.wait_for_selector(aspect_ratio_button_selector, timeout=5000)
            await browser_automation.click(aspect_ratio_button_selector)
            await asyncio.sleep(1.5)
            
            if is_portrait:
                option_selector = (
                    'div[role="option"]:has-text("Portrait (9:16)"), '
                    'div[role="option"]:has-text("Portrait"), '
                    'div[role="option"][aria-labelledby*="radix"]:has(span:has-text("Portrait"))'
                )
            else:
                option_selector = (
                    'div[role="option"]:has-text("Landscape (16:9)"), '
                    'div[role="option"]:has-text("Landscape"), '
                    'div[role="option"][aria-labelledby*="radix"]:has(span:has-text("Landscape"))'
                )
            
            await browser_automation.wait_for_selector(option_selector, timeout=5000)
            await browser_automation.click(option_selector)
            await asyncio.sleep(1.5)
            
            try:
                await browser_automation.evaluate("""
                    () => {
                        const event = new KeyboardEvent('keydown', { 
                            key: 'Escape', 
                            code: 'Escape', 
                            keyCode: 27, 
                            bubbles: true,
                            cancelable: true
                        });
                        document.activeElement?.dispatchEvent(event);
                        document.dispatchEvent(event);
                        return true;
                    }
                """)
                await asyncio.sleep(0.5)
            except:
                pass
        except Exception as e:
            print(f"Warning: Không thể set aspect ratio: {e}, tiếp tục với settings mặc định")
    
    async def _fill_prompt_and_generate(self, prompt: str):
        prompt_input_selector = 'textarea[placeholder*="Generate a video"]'
        await browser_automation.wait_for_selector(prompt_input_selector, timeout=60000)
        await browser_automation.fill(prompt_input_selector, prompt)
        await asyncio.sleep(1)
        
        generate_button_selector = 'button:has-text("Generate"), button:has-text("Create"), button[type="submit"]'
        await browser_automation.click(generate_button_selector)
        await asyncio.sleep(5)
    
    async def _wait_for_video_completion(self) -> bool:
        max_wait = 600
        waited = 0
        check_interval = 3
        
        while waited < max_wait:
            result = await browser_automation.evaluate("""
                () => {
                    const html = document.documentElement.outerHTML;
                    
                    const lottieContainer = document.querySelector('[id="lottie"], .lf-player-container');
                    let loadingPercent = null;
                    let loadingText = '';
                    
                    if (!loadingPercent) {
                        const allElements = document.querySelectorAll('div');
                        for (let el of allElements) {
                            const text = el.textContent || '';
                            if (text.trim().match(/^\\d+%$/) && el.offsetParent !== null) {
                                loadingPercent = el;
                                loadingText = text.trim();
                                break;
                            }
                        }
                    }
                    
                    const hasLoading = loadingPercent !== null || lottieContainer !== null;
                    
                    const videoElement = document.querySelector('video, [data-video], .video-result');
                    const hasVideo = videoElement !== null && videoElement.src && videoElement.src.length > 0;
                    
                    const isComplete = (hasVideo && !hasLoading);
                    
                    return {
                        hasLoading: hasLoading,
                        hasVideo: hasVideo,
                        loadingText: loadingText,
                        isComplete: isComplete
                    };
                }
            """)
            
            if result.get("isComplete"):
                return True
            
            loading_text = result.get("loadingText", "")
            if loading_text and "%" in loading_text:
                print(f"Video đang được tạo: {loading_text.strip()}")
            
            await asyncio.sleep(check_interval)
            waited += check_interval
        
        return False
    
    async def _extract_video_result(self) -> Optional[str]:
        video_url = await browser_automation.evaluate("""
            () => {
                const video = document.querySelector('video, [data-video], .video-result');
                return video ? video.src || video.getAttribute('src') : null;
            }
        """)
        return video_url
    
    async def _scroll_to_last_scene(self):
        try:
            slider_thumb_selector = 'span[role="slider"][aria-orientation="horizontal"]'
            await browser_automation.wait_for_selector(slider_thumb_selector, timeout=60000)
            await asyncio.sleep(0.5)
            
            track_info = await browser_automation.evaluate("""
                () => {
                    const sliderThumb = document.querySelector('span[role="slider"][aria-orientation="horizontal"]');
                    if (!sliderThumb) return null;
                    
                    const sliderContainer = sliderThumb.closest('span[style*="transform"]');
                    if (!sliderContainer) return null;
                    
                    const sliderTrack = sliderThumb.closest('[data-radix-slider-root]') || 
                                       sliderThumb.closest('[class*="slider"]') ||
                                       sliderThumb.parentElement?.parentElement;
                    if (!sliderTrack) return null;
                    
                    const trackRect = sliderTrack.getBoundingClientRect();
                    const thumbRect = sliderThumb.getBoundingClientRect();
                    
                    return {
                        thumbX: trackRect.left + trackRect.width - thumbRect.width - 6,
                        thumbY: trackRect.top + thumbRect.height / 2,
                        trackWidth: trackRect.width,
                        trackLeft: trackRect.left
                    };
                }
            """)
            
            if not track_info:
                return False
            
            await browser_automation.evaluate("""
                () => {
                    const sliderThumb = document.querySelector('span[role="slider"][aria-orientation="horizontal"]');
                    if (!sliderThumb) return false;
                    
                    const sliderContainer = sliderThumb.closest('span[style*="transform"]');
                    if (!sliderContainer) return false;
                    
                    sliderContainer.style.left = 'calc(100% - 6px)';
                    sliderThumb.setAttribute('aria-valuenow', '100');
                    
                    const inputEvent = new Event('input', { bubbles: true });
                    sliderThumb.dispatchEvent(inputEvent);
                    
                    const changeEvent = new Event('change', { bubbles: true });
                    sliderThumb.dispatchEvent(changeEvent);
                    
                    return true;
                }
            """)
            
            await asyncio.sleep(1)
            return True
        except Exception as e:
            print(f"Warning: Không thể kéo slider đến cuối: {e}")
            return False
    
    async def _click_current_video(self):
        try:
            success = await browser_automation.evaluate("""
                () => {
                    const addClipButton = document.getElementById('PINHOLE_ADD_CLIP_CARD_ID');
                    if (!addClipButton) return false;
                    
                    const parent = addClipButton.parentElement;
                    if (!parent) return false;
                    
                    const siblings = Array.from(parent.children).filter(child => 
                        child.tagName === 'DIV' && child.id !== 'PINHOLE_ADD_CLIP_CARD_ID'
                    );
                    
                    if (siblings.length < 2) return false;
                    
                    const secondFromBottom = siblings[siblings.length - 2];
                    if (secondFromBottom) {
                        secondFromBottom.click();
                        return true;
                    }
                    
                    return false;
                }
            """)
            
            if success:
                await asyncio.sleep(1)
                return True
            
            await browser_automation.wait_for_selector('#PINHOLE_ADD_CLIP_CARD_ID', timeout=10000)
            
            await browser_automation.evaluate("""
                () => {
                    const addClipButton = document.getElementById('PINHOLE_ADD_CLIP_CARD_ID');
                    if (!addClipButton) return false;
                    
                    const parent = addClipButton.parentElement;
                    if (!parent) return false;
                    
                    const siblings = Array.from(parent.children).filter(child => 
                        child.tagName === 'DIV' && child.id !== 'PINHOLE_ADD_CLIP_CARD_ID'
                    );
                    const firstSibling = siblings[0];
                    
                    if (firstSibling.children.length < 2) return false;
                    
                    const secondFromBottom = firstSibling.children[firstSibling.children.length - 2];
                    if (secondFromBottom) {
                        secondFromBottom.click();
                        return true;
                    } else {
                        return false;
                    }
                }
            """)
            
            await asyncio.sleep(1)
            return True
        except Exception as e:
            print(f"Warning: Không thể click video: {e}")
            return False
    
    async def generate_video_via_browser(self, prompt: str, project_config: Dict[str, Any], is_first_video: bool = True) -> Optional[Dict[str, Any]]:
        try:
            if is_first_video:
                print("[Step 1/6] Khởi động browser...")
                await browser_automation.start()
                print("[Step 1/6] ✓ Browser đã khởi động")
                
                print("[Step 2/6] Điều hướng đến project...")
                is_new_project = await self._navigate_to_project(project_config)
                print(f"[Step 2/6] ✓ Đã điều hướng đến project (is_new_project: {is_new_project})")
                
                print("[Step 3/6] Click nút Scenebuilder...")
                await self._click_scenebuilder()
                print("[Step 3/6] ✓ Đã click Scenebuilder")
                
                print("[Step 4/6] Cấu hình aspect ratio...")
                await self._configure_aspect_ratio(project_config)
                print("[Step 4/6] ✓ Đã cấu hình aspect ratio")
            else:
                print("[Step 1/4] Kéo slider đến scene cuối cùng...")
                await self._scroll_to_last_scene()
                print("[Step 1/4] ✓ Đã kéo slider đến cuối")
                
                print("[Step 2/4] Click vào video hiện tại...")
                await self._click_current_video()
                await asyncio.sleep(1)
                print("[Step 2/4] ✓ Đã click video hiện tại")
            
            print("[Step 5/6] Điền prompt và tạo video..." if is_first_video else "[Step 3/4] Điền prompt và tạo video...")
            await self._fill_prompt_and_generate(prompt)
            print("[Step 5/6] ✓ Đã điền prompt và bắt đầu tạo video" if is_first_video else "[Step 3/4] ✓ Đã điền prompt và bắt đầu tạo video")
            
            print("[Step 6/6] Đang chờ video hoàn thành..." if is_first_video else "[Step 4/4] Đang chờ video hoàn thành...")
            is_complete = await self._wait_for_video_completion()
            if is_complete:
                print("[Step 6/6] ✓ Video đã hoàn thành" if is_first_video else "[Step 4/4] ✓ Video đã hoàn thành")
            else:
                print("[Step 6/6] ⚠ Video chưa hoàn thành (timeout)" if is_first_video else "[Step 4/4] ⚠ Video chưa hoàn thành (timeout)")
            
            print("Đang trích xuất video URL...")
            video_url = await self._extract_video_result()
            if video_url:
                print(f"✓ Đã trích xuất video URL: {video_url[:50]}...")
            else:
                print("⚠ Không thể trích xuất video URL")
            
            return {
                "video_url": video_url,
                "success": is_complete,
                "project_link": project_config.get("project_link", "")
            }
            
        except Exception as e:
            print(f"❌ Lỗi trong browser automation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "video_url": None,
                "success": False,
                "error": str(e),
                "project_link": project_config.get("project_link", "")
            }
    
    async def generate_video_via_api(self, prompt: str, project_config: Dict[str, Any]) -> Optional[str]:
        try:
            veo_prompt = f"""
            Generate a video with the following prompt:
            {prompt}
            
            Style: {project_config.get('style', '3d_Pixar')}
            Duration: {project_config.get('duration', 8)} seconds
            Aspect Ratio: {project_config.get('aspect_ratio', '16:9')}
            """
            
            response = await self.gemini_client.generate_text(veo_prompt)
            
            return response
            
        except Exception as e:
            print(f"Error in API generation: {e}")
            return None
    
    async def retry_video(self, prompt: str, project_config: Dict[str, Any], use_browser: bool = True) -> Dict[str, Any]:
        scene_id = f"scene_retry"
        try:
            if use_browser:
                video_result = await self.generate_video_via_browser(prompt, project_config, is_first_video=False)
                if isinstance(video_result, dict):
                    video_url = video_result.get("video_url")
                    success = video_result.get("success", False)
                    project_link = video_result.get("project_link", "")
                    
                    if project_link and not project_config.get("project_link"):
                        project_config["project_link"] = project_link
                        from ..data.project_manager import project_manager
                        project_file = project_config.get("file", "")
                        if project_file:
                            project_manager.update_project(project_file, {"project_link": project_link})
                    
                    return {
                        "scene_id": scene_id,
                        "prompt": prompt,
                        "status": "SUCCESSFUL" if success and video_url else "FAILED",
                        "video_url": video_url,
                        "video_path": None,
                        "project_link": project_link
                    }
                else:
                    return {
                        "scene_id": scene_id,
                        "prompt": prompt,
                        "status": "FAILED",
                        "video_url": None,
                        "video_path": None
                    }
            else:
                video_url = await self.generate_video_via_api(prompt, project_config)
                return {
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "SUCCESSFUL" if video_url else "FAILED",
                    "video_url": video_url,
                    "video_path": None
                }
        except Exception as e:
            return {
                "scene_id": scene_id,
                "prompt": prompt,
                "status": "FAILED",
                "error": str(e),
                "video_url": None,
                "video_path": None
            }
    
    async def generate_videos(self, prompts: List[str], project_config: Dict[str, Any], use_browser: bool = True) -> List[Dict[str, Any]]:
        results = []
        
        for i, prompt in enumerate(prompts):
            scene_id = f"scene_{i+1}"
            is_first_video = (i == 0)
            
            try:
                if use_browser:
                    video_result = await self.generate_video_via_browser(prompt, project_config, is_first_video=is_first_video)
                    if isinstance(video_result, dict):
                        video_url = video_result.get("video_url")
                        success = video_result.get("success", False)
                        project_link = video_result.get("project_link", "")
                        
                        if project_link and not project_config.get("project_link"):
                            project_config["project_link"] = project_link
                            from ..data.project_manager import project_manager
                            project_file = project_config.get("file", "")
                            if project_file:
                                project_manager.update_project(project_file, {"project_link": project_link})
                        
                        results.append({
                            "scene_id": scene_id,
                            "prompt": prompt,
                            "status": "SUCCESSFUL" if success and video_url else "FAILED",
                            "video_url": video_url,
                            "video_path": None,
                            "project_link": project_link
                        })
                    else:
                        results.append({
                            "scene_id": scene_id,
                            "prompt": prompt,
                            "status": "FAILED",
                            "video_url": None,
                            "video_path": None
                        })
                else:
                    video_url = await self.generate_video_via_api(prompt, project_config)
                results.append({
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "SUCCESSFUL" if video_url else "FAILED",
                    "video_url": video_url,
                    "video_path": None
                })
                
            except Exception as e:
                results.append({
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "FAILED",
                    "error": str(e),
                    "video_url": None,
                    "video_path": None
                })
        
        return results

veo3_flow = VEO3Flow()

