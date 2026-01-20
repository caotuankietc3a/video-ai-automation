import asyncio
from typing import List, Dict, Any, Optional, Callable, TYPE_CHECKING
from .browser_automation import browser_automation, BrowserAutomation
from .gemini_client import GeminiClient
from ..data.config_manager import config_manager

if TYPE_CHECKING:
    from .browser_automation import BrowserAutomation

class VEO3Flow:
    def __init__(self, browser: Optional[BrowserAutomation] = None):
        self.browser = browser or browser_automation
        self.gemini_client = GeminiClient()
        self.flow_url = "https://labs.google/fx/tools/flow"
    
    async def _navigate_to_project(self, project_config: Dict[str, Any]) -> bool:
        browser = self.browser
        project_link = project_config.get("project_link", "")
        is_new_project = False
        
        if project_link:
            await browser.navigate(project_link)
            await asyncio.sleep(3)
            await browser.login_to_google()
            await asyncio.sleep(2)
        else:
            is_new_project = True
            await browser.navigate(self.flow_url)
            await asyncio.sleep(2)
            
            create_with_flow_selector = 'button:has-text("Create with Flow")'
            await browser.wait_for_selector(create_with_flow_selector, timeout=60000)
            await browser.click(create_with_flow_selector)
            await asyncio.sleep(2)
            
            await browser.login_to_google()
            await asyncio.sleep(3)
            
            new_project_selector = 'button:has-text("New project")'
            await browser.wait_for_selector(new_project_selector, timeout=10000)
            await browser.click(new_project_selector)
            await asyncio.sleep(2)
            
            current_url = await browser.get_current_url()
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
            await self.browser.wait_for_selector(scenebuilder_button_selector, timeout=10000)
            await self.browser.click(scenebuilder_button_selector)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"Warning: Không thể click Scenebuilder: {e}, tiếp tục bình thường")
            return False
    
    async def _configure_outputs_per_prompt(self, project_config: Dict[str, Any]):
        outputs_per_prompt = project_config.get("outputs_per_prompt", 2)
        
        try:
            settings_button_selector = (
                'button[aria-haspopup="dialog"][aria-controls*="radix"]:has(i.material-icons-outlined:has-text("tune")), '
                'button[aria-label*="Settings"][aria-haspopup="dialog"], '
                'button:has(i.material-icons-outlined):has-text("Settings")'
            )
            await self.browser.wait_for_selector(settings_button_selector, timeout=5000)
            await self.browser.click(settings_button_selector)
            await asyncio.sleep(1.5)

            outputs_button_selector = (
                'button[type="button"][role="combobox"][aria-controls*="radix"]:has(span:has-text("Outputs per prompt")), '
                'button[role="combobox"][aria-controls*="radix"]:has-text("Outputs per prompt"), '
                'button[role="combobox"]:has(span:has-text("Outputs per prompt")), '
                'button[type="button"][role="combobox"]:has(div:has-text("Outputs per prompt"))'
            )
            await self.browser.wait_for_selector(outputs_button_selector, timeout=10000)
            await self.browser.click(outputs_button_selector)
            await asyncio.sleep(1.5)
            
            option_value = str(outputs_per_prompt)
            option_selector = (
                f'div[role="option"][aria-labelledby*="radix"]:has(span:has-text("{option_value}")), '
                f'div[role="option"]:has-text("{option_value}"), '
                f'div[role="option"][data-state]:has(span:has-text("{option_value}"))'
            )
            await self.browser.wait_for_selector(option_selector, timeout=5000)
            await self.browser.click(option_selector)
            await asyncio.sleep(1.5)
            
            try:
                await self.browser.evaluate("""
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
            print(f"Warning: Không thể set outputs per prompt: {e}, tiếp tục với settings mặc định")
    
    async def _configure_aspect_ratio(self, project_config: Dict[str, Any]):
        aspect_ratio = project_config.get("aspect_ratio", "Khổ ngang (16:9)")
        is_portrait = "dọc" in aspect_ratio or "Portrait" in aspect_ratio or "9:16" in aspect_ratio
        
        try:
            settings_button_selector = (
                'button[aria-haspopup="dialog"][aria-controls*="radix"]:has(i.material-icons-outlined:has-text("tune")), '
                'button[aria-label*="Settings"][aria-haspopup="dialog"], '
                'button:has(i.material-icons-outlined):has-text("Settings")'
            )
            await self.browser.wait_for_selector(settings_button_selector, timeout=5000)
            await self.browser.click(settings_button_selector)
            await asyncio.sleep(1.5)
            
            aspect_ratio_button_selector = (
                'button[role="combobox"][aria-controls*="radix"]:has-text("Aspect Ratio"), '
                'button[role="combobox"]:has(span:has-text("Aspect Ratio"))'
            )
            await self.browser.wait_for_selector(aspect_ratio_button_selector, timeout=5000)
            await self.browser.click(aspect_ratio_button_selector)
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
            
            await self.browser.wait_for_selector(option_selector, timeout=5000)
            await self.browser.click(option_selector)
            await asyncio.sleep(1.5)
            
            try:
                await self.browser.evaluate("""
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
        await self.browser.wait_for_selector(prompt_input_selector, timeout=60000)
        await self.browser.fill(prompt_input_selector, prompt)
        await asyncio.sleep(1)
        
        generate_button_selector = 'button:has-text("Generate"), button:has-text("Create"), button[type="submit"]'
        await self.browser.click(generate_button_selector)
        await asyncio.sleep(5)
    
    async def _wait_for_video_completion(self) -> bool:
        max_wait = 600
        waited = 0
        check_interval = 3
        
        while waited < max_wait:
            result = await self.browser.evaluate("""
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
        video_url = await self.browser.evaluate("""
            () => {
                const video = document.querySelector('video, [data-video], .video-result');
                return video ? video.src || video.getAttribute('src') : null;
            }
        """)
        return video_url
    
    async def _download_videos_from_blob(self, project_config: Dict[str, Any], scene_id: str) -> Optional[str]:
        try:
            project_name = project_config.get("name", "default")
            outputs_per_prompt = project_config.get("outputs_per_prompt", 2)
            
            print(f"Đang tìm và download {outputs_per_prompt} video(s) từ blob URL...")
            await asyncio.sleep(2)
            
            video_data = await self.browser.evaluate("""
                (maxCount) => {
                    const videos = Array.from(document.querySelectorAll('video[src^="blob:"]'));
                    const videoData = [];
                    
                    for (let i = 0; i < videos.length; i++) {
                        const video = videos[i];
                        const blobUrl = video.src || video.getAttribute('src');
                        if (blobUrl && blobUrl.startsWith('blob:')) {
                            videoData.push({
                                index: i,
                                blobUrl: blobUrl
                            });
                        }
                    }
                    
                    return videoData.slice(0, maxCount);
                }
            """, outputs_per_prompt)
            
            if not video_data or len(video_data) == 0:
                print("⚠ Không tìm thấy video với blob URL")
                return None
            
            from ..config.constants import OUTPUTS_DIR
            import os
            project_output_dir = os.path.join(OUTPUTS_DIR, project_name)
            os.makedirs(project_output_dir, exist_ok=True)
            
            downloaded_paths = []
            
            for i, video_info in enumerate(video_data):
                try:
                    blob_url = video_info.get("blobUrl")
                    if not blob_url:
                        continue
                    
                    print(f"Đang download video {i+1}/{len(video_data)} từ blob URL...")
                    
                    video_bytes = await self.browser.evaluate("""
                        async (blobUrl) => {
                            try {
                                const response = await fetch(blobUrl);
                                const blob = await response.blob();
                                const arrayBuffer = await blob.arrayBuffer();
                                const uint8Array = new Uint8Array(arrayBuffer);
                                return Array.from(uint8Array);
                            } catch (e) {
                                console.error('Error fetching blob:', e);
                                return null;
                            }
                        }
                    """, blob_url)
                    
                    if video_bytes:
                        filename = f"{scene_id}_{i+1}.mp4" if len(video_data) > 1 else f"{scene_id}.mp4"
                        file_path = os.path.join(project_output_dir, filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(bytes(video_bytes))
                        
                        downloaded_paths.append(file_path)
                        print(f"✓ Đã download video {i+1}/{len(video_data)}: {file_path}")
                    else:
                        print(f"⚠ Không thể download video {i+1}")
                    
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"⚠ Lỗi khi download video {i+1}: {e}")
            
            if downloaded_paths:
                return downloaded_paths[0] if len(downloaded_paths) == 1 else downloaded_paths[0]
            else:
                return None
                
        except Exception as e:
            print(f"Warning: Không thể download video từ blob URL: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _scroll_to_last_scene(self):
        try:
            slider_thumb_selector = 'span[role="slider"][aria-orientation="horizontal"]'
            await self.browser.wait_for_selector(slider_thumb_selector, timeout=60000)
            await asyncio.sleep(0.5)
            
            track_info = await self.browser.evaluate("""
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
            
            await self.browser.evaluate("""
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
            success = await self.browser.evaluate("""
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
            
            await self.browser.wait_for_selector('#PINHOLE_ADD_CLIP_CARD_ID', timeout=10000)
            
            await self.browser.evaluate("""
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
    
    async def generate_video_via_browser(self, prompt: str, project_config: Dict[str, Any], is_first_video: bool = True, on_project_link_updated: Optional[Callable[[str, str], None]] = None) -> Optional[Dict[str, Any]]:
        try:
            if is_first_video:
                print("[Step 1/6] Khởi động browser...")
                await self.browser.start()
                print("[Step 1/6] ✓ Browser đã khởi động")
                
                print("[Step 2/6] Điều hướng đến project...")
                is_new_project = await self._navigate_to_project(project_config)
                print(f"[Step 2/6] ✓ Đã điều hướng đến project (is_new_project: {is_new_project})")
                
                project_link = project_config.get("project_link", "")
                if project_link and on_project_link_updated:
                    try:
                        on_project_link_updated("", project_link)
                    except Exception as e:
                        print(f"Warning: Không thể gọi callback on_project_link_updated: {e}")
                
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
            
            print("[Step 4.5/6] Cấu hình số lượng outputs per prompt..." if is_first_video else "[Step 2.5/4] Cấu hình số lượng outputs per prompt...")
            await self._configure_outputs_per_prompt(project_config)
            print("[Step 4.5/6] ✓ Đã cấu hình outputs per prompt" if is_first_video else "[Step 2.5/4] ✓ Đã cấu hình outputs per prompt")

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
                "video_path": None,
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
        project_config["current_scene_index"] = "retry"
        try:
            if use_browser:
                video_result = await self.generate_video_via_browser(prompt, project_config, is_first_video=False)
                if isinstance(video_result, dict):
                    video_url = video_result.get("video_url")
                    video_path = video_result.get("video_path")
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
                        "video_path": video_path,
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
    
    async def generate_videos(self, prompts: List[str], project_config: Dict[str, Any], use_browser: bool = True, on_video_generated: Optional[Callable[[List[Dict[str, Any]]], None]] = None, on_project_link_updated: Optional[Callable[[str, str], None]] = None) -> List[Dict[str, Any]]:
        results = []
        total_prompts = len(prompts)
        
        for i, prompt in enumerate(prompts):
            scene_id = f"scene_{i+1}"
            is_first_video = (i == 0)
            is_last_video = (i == total_prompts - 1)
            project_config["current_scene_index"] = i + 1
            
            try:
                if use_browser:
                    video_result = await self.generate_video_via_browser(prompt, project_config, is_first_video=is_first_video, on_project_link_updated=on_project_link_updated)
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
                        
                        video_path = video_result.get("video_path")
                        video_data = {
                            "scene_id": scene_id,
                            "prompt": prompt,
                            "status": "SUCCESSFUL" if success and video_url else "FAILED",
                            "video_url": video_url,
                            "video_path": video_path,
                            "project_link": project_link
                        }
                        results.append(video_data)
                        
                        if on_video_generated:
                            try:
                                on_video_generated(results.copy())
                            except Exception as e:
                                print(f"Lỗi khi gọi callback on_video_generated: {e}")
                    else:
                        video_data = {
                            "scene_id": scene_id,
                            "prompt": prompt,
                            "status": "FAILED",
                            "video_url": None,
                            "video_path": None
                        }
                        results.append(video_data)
                        
                        if on_video_generated:
                            try:
                                on_video_generated(results.copy())
                            except Exception as e:
                                print(f"Lỗi khi gọi callback on_video_generated: {e}")
                else:
                    video_url = await self.generate_video_via_api(prompt, project_config)
                    video_data = {
                        "scene_id": scene_id,
                        "prompt": prompt,
                        "status": "SUCCESSFUL" if video_url else "FAILED",
                        "video_url": video_url,
                        "video_path": None
                    }
                    results.append(video_data)
                    
                    if on_video_generated:
                        try:
                            on_video_generated(results.copy())
                        except Exception as e:
                            print(f"Lỗi khi gọi callback on_video_generated: {e}")
                
            except Exception as e:
                video_data = {
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "FAILED",
                    "error": str(e),
                    "video_url": None,
                    "video_path": None
                }
                results.append(video_data)
                
                if on_video_generated:
                    try:
                        on_video_generated(results.copy())
                    except Exception as e:
                        print(f"Lỗi khi gọi callback on_video_generated: {e}")
        
        if use_browser and len(results) > 0:
            last_result = results[-1]
            if last_result.get("status") == "SUCCESSFUL":
                print(f"\n📥 Đang download video scene cuối cùng...")
                last_scene_id = last_result.get("scene_id", f"scene_{len(results)}")
                video_path = await self._download_videos_from_blob(project_config, last_scene_id)
                if video_path:
                    results[-1]["video_path"] = video_path
                    print(f"✅ Đã download video scene cuối: {video_path}")
                    
                    if on_video_generated:
                        try:
                            on_video_generated(results.copy())
                        except Exception as e:
                            print(f"Lỗi khi gọi callback: {e}")
        
        return results

veo3_flow = VEO3Flow()

