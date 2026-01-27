import asyncio
from typing import List, Dict, Any, Optional, Callable, TypeVar, Coroutine
from .video_analyzer import VideoAnalyzer
from .content_generator import ContentGenerator
from .character_extractor import CharacterExtractor
from .scene_generator import SceneGenerator
from .veo3_prompt_generator import VEO3PromptGenerator
from ..integrations.veo3_flow import VEO3Flow
from ..integrations.browser_automation import get_browser_instance, stop_browser_instance, BrowserAutomation
from ..data.project_manager import project_manager
from ..data.video_manager import video_manager
from ..utils.logger import Logger

T = TypeVar('T')

RETRY_DELAY_SECONDS = 3
MAX_RETRIES = 3


class Workflow:
    def __init__(self, project_name: str, browser_instance_id: Optional[str] = None):
        self.project_name = project_name
        self.browser_instance_id = browser_instance_id or f"workflow_{project_name}"
        self.logger = Logger(project_name)
        
        self.browser: Optional[BrowserAutomation] = None
        
        self.video_analyzer = VideoAnalyzer(project_name)
        self.content_generator = ContentGenerator(project_name)
        self.character_extractor = CharacterExtractor(project_name)
        self.scene_generator = SceneGenerator(project_name)
        self.veo3_prompt_generator = VEO3PromptGenerator(project_name)
        self.veo3_flow: Optional[VEO3Flow] = None
        
        self.is_running = False
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        self.update_callbacks: Dict[str, Callable] = {}
    
    def _get_browser(self) -> BrowserAutomation:
        if self.browser is None:
            self.browser = get_browser_instance(self.browser_instance_id)
        return self.browser
    
    def _get_veo3_flow(self) -> VEO3Flow:
        if self.veo3_flow is None:
            self.veo3_flow = VEO3Flow(browser=self._get_browser())
        return self.veo3_flow
    
    async def _close_and_new_tab(self):
        try:
            if self.browser:
                await self.browser.close_current_tab()
                await self.browser.new_tab()
                self.logger.info("Đã đóng tab cũ và mở tab mới sau step")
        except Exception as e:
            self.logger.warning(f"Lỗi khi đóng/mở tab mới: {e}")
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        self.progress_callback = callback
    
    def set_update_callbacks(self, on_characters: Optional[Callable] = None,
                            on_scenes: Optional[Callable] = None,
                            on_prompts: Optional[Callable] = None,
                            on_videos: Optional[Callable] = None,
                            on_logs: Optional[Callable] = None,
                            on_project_links: Optional[Callable] = None):
        if on_characters:
            self.update_callbacks["characters"] = on_characters
        if on_scenes:
            self.update_callbacks["scenes"] = on_scenes
        if on_prompts:
            self.update_callbacks["prompts"] = on_prompts
        if on_videos:
            self.update_callbacks["videos"] = on_videos
        if on_logs:
            self.update_callbacks["logs"] = on_logs
        if on_project_links:
            self.update_callbacks["project_links"] = on_project_links
    
    def _update_progress(self, message: str, progress: float):
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    async def _retry_step(
        self,
        step_name: str,
        step_func: Callable[[], Coroutine[Any, Any, T]],
        max_retries: int = MAX_RETRIES,
        delay_seconds: float = RETRY_DELAY_SECONDS
    ) -> T:
        last_error: Optional[Exception] = None
        
        for attempt in range(1, max_retries + 1):
            try:
                return await step_func()
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"[{step_name}] Lỗi lần {attempt}/{max_retries}: {str(e)}"
                )
                
                if attempt < max_retries:
                    self.logger.info(f"[{step_name}] Retry sau {delay_seconds}s...")
                    await asyncio.sleep(delay_seconds)
                    
                    try:
                        if self.browser:
                            await self.browser.close_current_tab()
                            await self.browser.new_tab()
                            self.logger.info(f"[{step_name}] Đã đóng tab cũ và mở tab mới để retry")
                    except Exception as e:
                        self.logger.warning(f"[{step_name}] Lỗi khi đóng/mở tab mới: {e}")
                else:
                    self.logger.error(f"[{step_name}] Đã thử {max_retries} lần, vẫn thất bại")
        
        raise last_error if last_error else RuntimeError(f"Step {step_name} failed")
    
    def _update_workflow_step(self, project_file: str, step: str):
        project = project_manager.load_project(project_file)
        if project:
            project["workflow_step"] = step
            project_manager.save_project(project)
    
    def _get_workflow_step(self, project_file: str) -> str:
        project = project_manager.load_project(project_file)
        if project:
            return project.get("workflow_step", "start")
        return "start"
    
    async def run(self, video_paths: List[str], project_config: Dict[str, Any]):
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        project_file = project_config.get("file", "")
        current_step = self._get_workflow_step(project_file)
        
        self.logger.info(
            "Khởi chạy workflow",
            {
                "num_videos": len(video_paths),
                "project_name": self.project_name,
                "duration": project_config.get("duration"),
                "style": project_config.get("style"),
                "resume_from_step": current_step,
            },
        )

        try:
            project = project_manager.load_project(project_file) if project_file else None
            
            if current_step == "complete":
                videos = project.get("videos", []) if project else []
                failed = [v for v in videos if isinstance(v, dict) and v.get("status") == "FAILED"]
                if failed:
                    self.logger.info(f"Workflow đã complete nhưng có {len(failed)} video(s) FAILED, đang retry từng video...")
                    use_browser = project_config.get("use_browser_automation", True)
                    veo = self._get_veo3_flow()
                    for i, v in enumerate(videos):
                        if not isinstance(v, dict) or v.get("status") == "SUCCESSFUL":
                            continue
                        prompt = v.get("prompt", "")
                        if not prompt:
                            continue
                        scene_id = v.get("scene_id", f"scene_{i + 1}")
                        result = await veo.retry_video(prompt, project_config, use_browser)
                        result = dict(result)
                        result["scene_id"] = scene_id
                        if project:
                            project["videos"] = project.get("videos", []) or []
                            if i < len(project["videos"]):
                                project["videos"][i] = result
                            else:
                                project["videos"].append(result)
                            project_manager.save_project(project)
                    return {
                        "characters": project.get("characters", {}) if project else {},
                        "scenes": project.get("scenes", []) if project else [],
                        "prompts": project.get("prompts", []) if project else [],
                        "videos": project.get("videos", []) if project else [],
                    }
                self.logger.info("Workflow đã hoàn thành, không cần chạy lại")
                return {
                    "characters": project.get("characters", {}) if project else {},
                    "scenes": project.get("scenes", []) if project else [],
                    "prompts": project.get("prompts", []) if project else [],
                    "videos": videos,
                }
            
            script_text: str = project_config.get("script", "")
            video_analysis_override = project_config.get("video_analysis_override")
            gemini_link = None
            video_analysis = None
            
            if current_step == "start":
                if script_text:
                    self.logger.info(
                        "Dùng script_text từ project làm VIDEO_ANALYSIS",
                        {"script_length": len(script_text)},
                    )
                    video_analysis = script_text
                    if project:
                        project["script"] = script_text
                        project_manager.save_project(project)
                    self._update_workflow_step(project_file, "content")
                    current_step = "content"
                elif video_analysis_override:
                    self.logger.info(
                        "Dùng video_analysis_override từ ô Kịch bản/Ý tưởng",
                        {"override_length": len(video_analysis_override)},
                    )
                    video_analysis = video_analysis_override
                    if project:
                        project["script"] = video_analysis_override
                        project_manager.save_project(project)
                    self._update_workflow_step(project_file, "content")
                    current_step = "content"
                elif project and project.get("script"):
                    self.logger.info("Dùng script từ project đã lưu làm VIDEO_ANALYSIS")
                    video_analysis = project.get("script")
                    self._update_workflow_step(project_file, "content")
                    current_step = "content"
                else:
                    self.logger.info(
                        "Không có sẵn VIDEO_ANALYSIS, bắt đầu phân tích video tự động",
                        {"video_paths": video_paths},
                    )
                    
                    async def _analyze_video():
                        return await self.video_analyzer.analyze_videos(
                            video_paths, self.project_name, browser=self._get_browser()
                        )
                    
                    video_analysis, gemini_link = await self._retry_step(
                        "Video Analysis", _analyze_video
                    )
                    self.logger.info(
                        "Hoàn thành phân tích video",
                        {"analysis_length": len(video_analysis), "gemini_link": gemini_link},
                    )
                    
                    if gemini_link and project:
                        project["gemini_video_analysis_link"] = gemini_link
                        project_manager.save_project(project)
                        self.logger.info(f"Đã lưu Gemini link vào project: {gemini_link}")
                    
                    if project:
                        project["script"] = video_analysis
                        project_manager.save_project(project)
                    
                    await self._close_and_new_tab()
                    
                    self._update_workflow_step(project_file, "content")
                    current_step = "content"
            else:
                if project and project.get("script"):
                    video_analysis = project.get("script")
                    self.logger.info(f"Resume từ step {current_step}, sử dụng video_analysis đã có")
                else:
                    self.logger.warning("Không tìm thấy video_analysis, bắt đầu lại từ đầu")
                    current_step = "start"
            
            user_script = project_config.get("script", "")
            content = None
            
            if current_step == "content":
                async def _generate_content():
                    return await self.content_generator.generate_content(
                        video_analysis, user_script, self.project_name, project_config, browser=self._get_browser()
                    )
                
                content = await self._retry_step("Content Generation", _generate_content)
                self.logger.info(
                    "Đã tạo nội dung từ VIDEO_ANALYSIS",
                    {
                        "full_content_length": len(content.get("full_content", "")),
                        "has_characters_section": bool(content.get("characters_section")),
                        "has_story_section": bool(content.get("story_section")),
                        "has_storyboard_section": bool(content.get("storyboard_section")),
                    },
                )
                
                if project:
                    project["script"] = content.get("full_content", "") if content else ""
                    project_manager.save_project(project)
                
                await self._close_and_new_tab()
                
                self._update_workflow_step(project_file, "characters")
                current_step = "characters"
            else:
                if project and project.get("script"):
                    content = {"full_content": project.get("script")}
                    self.logger.info(f"Resume từ step {current_step}, sử dụng content đã có")
                    if current_step not in ["characters", "scenes", "prompts", "videos"]:
                        current_step = "characters"
                else:
                    self.logger.warning("Không tìm thấy content, bắt đầu lại từ đầu")
                    current_step = "content"
            
            characters = None
            
            if current_step == "characters":
                async def _extract_characters():
                    return await self.character_extractor.extract_characters(
                        content["full_content"], self.project_name, project_config, browser=self._get_browser()
                    )
                
                characters = await self._retry_step("Character Extraction", _extract_characters)
                self.logger.info(
                    "Đã trích xuất nhân vật",
                    {"num_characters": len(characters) if isinstance(characters, dict) else None},
                )
                if "characters" in self.update_callbacks:
                    self.update_callbacks["characters"](characters)
                if "logs" in self.update_callbacks:
                    self.update_callbacks["logs"]()
                
                if project:
                    project["characters"] = characters
                    project_manager.save_project(project)
                
                await self._close_and_new_tab()
                
                self._update_workflow_step(project_file, "scenes")
                current_step = "scenes"
            else:
                if project and project.get("characters"):
                    characters = project.get("characters")
                    self.logger.info(f"Resume từ step {current_step}, sử dụng characters đã có")
                    if current_step not in ["scenes", "prompts", "videos"]:
                        current_step = "scenes"
                else:
                    self.logger.warning("Không tìm thấy characters, bắt đầu lại từ đầu")
                    current_step = "characters"
            
            scenes = None
            
            if current_step == "scenes":
                async def _generate_scenes():
                    return await self.scene_generator.generate_scenes(
                        content["full_content"], 
                        characters,
                        self.project_name,
                        project_config,
                        browser=self._get_browser()
                    )
                
                scenes = await self._retry_step("Scene Generation", _generate_scenes)
                self.logger.info(
                    "Đã tạo scenes từ nội dung và nhân vật",
                    {"num_scenes": len(scenes)},
                )
                if "scenes" in self.update_callbacks:
                    self.update_callbacks["scenes"](scenes)
                if "logs" in self.update_callbacks:
                    self.update_callbacks["logs"]()
                
                if project:
                    project["scenes"] = scenes
                    project_manager.save_project(project)
                
                await self._close_and_new_tab()
                
                self._update_workflow_step(project_file, "prompts")
                current_step = "prompts"
            else:
                if project and project.get("scenes"):
                    scenes = project.get("scenes")
                    self.logger.info(f"Resume từ step {current_step}, sử dụng scenes đã có")
                    if current_step not in ["prompts", "videos"]:
                        current_step = "prompts"
                else:
                    self.logger.warning("Không tìm thấy scenes, bắt đầu lại từ đầu")
                    current_step = "scenes"
            
            veo3_prompts = None
            
            if current_step == "prompts":
                async def _generate_prompts():
                    return await self.veo3_prompt_generator.generate_prompts(
                        scenes, characters, self.project_name, project_config, browser=self._get_browser()
                    )
                
                veo3_prompts = await self._retry_step("VEO3 Prompt Generation", _generate_prompts)
                self.logger.info(
                    "Đã tạo VEO3 prompts từ scenes",
                    {"num_prompts": len(veo3_prompts)},
                )
                if "prompts" in self.update_callbacks:
                    self.update_callbacks["prompts"](veo3_prompts)
                if "logs" in self.update_callbacks:
                    self.update_callbacks["logs"]()
                
                if project:
                    project["prompts"] = veo3_prompts
                    project_manager.save_project(project)
                
                await self._close_and_new_tab()
                
                self._update_workflow_step(project_file, "videos")
                current_step = "videos"
            else:
                if project and project.get("prompts"):
                    veo3_prompts = project.get("prompts")
                    self.logger.info(f"Resume từ step {current_step}, sử dụng prompts đã có")
                    if current_step != "videos":
                        current_step = "videos"
                else:
                    self.logger.warning("Không tìm thấy prompts, bắt đầu lại từ đầu")
                    current_step = "prompts"
            
            use_browser = project_config.get("use_browser_automation", True)
            video_results = None
            
            if current_step == "videos":
                async def _generate_videos():
                    return await self._get_veo3_flow().generate_videos(veo3_prompts, project_config, use_browser)
                
                video_results = await self._retry_step("Video Generation", _generate_videos)
                self.logger.info(
                    "Đã gọi generate_videos cho VEO3",
                    {
                        "num_requests": len(veo3_prompts),
                        "use_browser": use_browser,
                        "num_results": len(video_results),
                    },
                )
                
                if project:
                    existing_videos = project.get("videos", [])
                    if isinstance(existing_videos, list) and isinstance(video_results, list):
                        existing_videos.extend(video_results)
                        project["videos"] = existing_videos
                    else:
                        project["videos"] = video_results
                    project_manager.save_project(project)
                
                self._update_workflow_step(project_file, "complete")
            else:
                if project and project.get("videos"):
                    video_results = project.get("videos")
                    self.logger.info(f"Resume từ step {current_step}, sử dụng videos đã có")
                else:
                    self.logger.warning("Không tìm thấy videos, bắt đầu lại từ đầu")
                    current_step = "videos"
            
            final_step = self._get_workflow_step(project_file)
            if final_step != "complete":
                error_msg = f"Workflow chưa hoàn thành, dừng ở step: {final_step}"
                self.logger.error(error_msg)
                self.is_running = False
                raise RuntimeError(error_msg)
            
            self.logger.info("Workflow hoàn thành thành công")
            
            return {
                "characters": characters,
                "scenes": scenes,
                "prompts": veo3_prompts,
                "videos": video_results,
            }
            
        except Exception as e:
            self.logger.error("Workflow error", {"error": str(e)})
            self.is_running = False
            final_step = self._get_workflow_step(project_file) if project_file else None
            self.logger.error(f"Workflow dừng ở step: {final_step}, không stop browser để có thể resume sau")
            raise
        finally:
            final_step = self._get_workflow_step(project_file) if project_file else None
            self.logger.info(f"Workflow finally block - current step: {final_step}, is_running: {self.is_running}")
            if final_step == "complete" and not self.is_running:
                try:
                    self.logger.info(f"Workflow đã hoàn thành, đang close tab cho browser instance: {self.browser_instance_id}")
                    await stop_browser_instance(self.browser_instance_id, close_tab_only=True)
                    self.logger.info("Đã close tab sau khi workflow hoàn thành")
                except Exception as e:
                    self.logger.warning(f"Lỗi khi close tab: {e}")
            else:
                if final_step != "complete":
                    self.logger.warning(f"Workflow chưa hoàn thành (step: {final_step}), KHÔNG stop browser để có thể resume sau")
                if self.is_running:
                    self.logger.warning(f"Workflow vẫn đang chạy (is_running=True), KHÔNG stop browser")
    
    def stop(self):
        self.is_running = False
        self.logger.info("Workflow stopped by user")
    
    async def run_step_analyze_video(self, video_paths: List[str], project_config: Dict[str, Any]) -> str:
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        try:
            script_text: str = project_config.get("script", "")
            video_analysis_override = project_config.get("video_analysis_override")
            if script_text:
                self.logger.info("Dùng script_text từ project làm VIDEO_ANALYSIS")
                video_analysis = script_text
            elif video_analysis_override:
                self.logger.info("Dùng video_analysis_override từ ô Kịch bản/Ý tưởng")
                video_analysis = video_analysis_override
            else:
                self.logger.info("Bắt đầu phân tích video tự động")
                video_analysis, gemini_link = await self.video_analyzer.analyze_videos(video_paths, self.project_name)
                self.logger.info("Hoàn thành phân tích video")
                
                if gemini_link:
                    project = project_manager.load_project(project_config.get("file", ""))
                    if project:
                        project["gemini_video_analysis_link"] = gemini_link
                        project_manager.save_project(project)
                        self.logger.info(f"Đã lưu Gemini link vào project: {gemini_link}")
            
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            return video_analysis
        finally:
            self.is_running = False
    
    async def run_step_generate_content(self, video_analysis: str, project_config: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        try:
            user_script = project_config.get("script", "")
            content = await self.content_generator.generate_content(video_analysis, user_script, self.project_name, project_config)
            
            if content is None:
                raise RuntimeError("Không thể tạo nội dung, generate_content trả về None")
            
            self.logger.info("Đã tạo nội dung từ VIDEO_ANALYSIS")
            
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            project_file = project_config.get("file", "")
            if project_file:
                project = project_manager.load_project(project_file)
                if project:
                    project["script"] = content.get("full_content", "") if content else ""
                    project_manager.save_project(project)
            
            return content
        finally:
            self.is_running = False
    
    async def run_step_extract_characters(self, content: str, project_config: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        try:
            full_content = content if isinstance(content, str) else content.get("full_content", "")
            characters = await self.character_extractor.extract_characters(full_content, self.project_name, project_config)
            self.logger.info("Đã trích xuất nhân vật")
            
            if "characters" in self.update_callbacks:
                self.update_callbacks["characters"](characters)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            project_file = project_config.get("file", "")
            if project_file:
                project = project_manager.load_project(project_file)
                if project:
                    project["characters"] = characters
                    project_manager.save_project(project)
            
            return characters
        finally:
            self.is_running = False
    
    async def run_step_generate_scenes(self, content: str, characters: Dict[str, Any], project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        try:
            full_content = content if isinstance(content, str) else content.get("full_content", "")
            scenes = await self.scene_generator.generate_scenes(full_content, characters, self.project_name, project_config)
            self.logger.info("Đã tạo scenes từ nội dung và nhân vật")
            
            if "scenes" in self.update_callbacks:
                self.update_callbacks["scenes"](scenes)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            project_file = project_config.get("file", "")
            if project_file:
                project = project_manager.load_project(project_file)
                if project:
                    project["scenes"] = scenes
                    project_manager.save_project(project)
            
            return scenes
        finally:
            self.is_running = False
    
    async def run_step_generate_prompts(self, scenes: List[Dict[str, Any]], characters: Dict[str, Any], project_config: Dict[str, Any]) -> List[str]:
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        try:
            def on_prompt_generated(prompts):
                if "prompts" in self.update_callbacks:
                    self.update_callbacks["prompts"](prompts)
                if "logs" in self.update_callbacks:
                    self.update_callbacks["logs"]()
            
            veo3_prompts = await self.veo3_prompt_generator.generate_prompts(scenes, characters, self.project_name, project_config, on_prompt_generated)
            self.logger.info("Đã tạo VEO3 prompts từ scenes")
            
            if "prompts" in self.update_callbacks:
                self.update_callbacks["prompts"](veo3_prompts)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            project_file = project_config.get("file", "")
            if project_file:
                project = project_manager.load_project(project_file)
                if project:
                    project["prompts"] = veo3_prompts
                    project_manager.save_project(project)
            
            return veo3_prompts
        finally:
            self.is_running = False
    
    async def run_step_generate_videos(self, veo3_prompts: List[str], project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        try:
            def on_video_generated(videos):
                if "videos" in self.update_callbacks:
                    self.update_callbacks["videos"](videos)
                if "logs" in self.update_callbacks:
                    self.update_callbacks["logs"]()
            
            def on_project_link_updated(gemini_link: str, flow_link: str):
                if flow_link:
                    project_config["project_link"] = flow_link
                if gemini_link:
                    project_config["gemini_project_link"] = gemini_link
                if "project_links" in self.update_callbacks:
                    self.update_callbacks["project_links"](gemini_link, flow_link)
                if "logs" in self.update_callbacks:
                    self.update_callbacks["logs"]()
            
            use_browser = project_config.get("use_browser_automation", True)
            video_results = await self._get_veo3_flow().generate_videos(veo3_prompts, project_config, use_browser, on_video_generated, on_project_link_updated)
            self.logger.info("Đã gọi generate_videos cho VEO3")
            
            if "videos" in self.update_callbacks:
                self.update_callbacks["videos"](video_results)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            project_file = project_config.get("file", "")
            if project_file:
                project = project_manager.load_project(project_file)
                if project:
                    project["videos"] = video_results
                    project_manager.save_project(project)
            
            return video_results
        finally:
            self.is_running = False
            try:
                if self.browser:
                    await self.browser.close_current_tab()
                    await self.browser.new_tab()
                    self.logger.info("Đã đóng tab và mở tab mới sau khi generate videos")
            except Exception as e:
                self.logger.warning(f"Lỗi khi đóng/mở tab mới: {e}")

