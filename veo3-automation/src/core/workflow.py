import asyncio
from typing import List, Dict, Any, Optional, Callable
from .video_analyzer import VideoAnalyzer
from .content_generator import ContentGenerator
from .character_extractor import CharacterExtractor
from .scene_generator import SceneGenerator
from .veo3_prompt_generator import VEO3PromptGenerator
from ..integrations.veo3_flow import veo3_flow
from ..data.project_manager import project_manager
from ..data.video_manager import video_manager
from ..utils.logger import Logger

class Workflow:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.logger = Logger(project_name)
        self.video_analyzer = VideoAnalyzer(project_name)
        self.content_generator = ContentGenerator(project_name)
        self.character_extractor = CharacterExtractor(project_name)
        self.scene_generator = SceneGenerator(project_name)
        self.veo3_prompt_generator = VEO3PromptGenerator(project_name)
        self.is_running = False
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        self.update_callbacks: Dict[str, Callable] = {}
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        self.progress_callback = callback
    
    def set_update_callbacks(self, on_characters: Optional[Callable] = None,
                            on_scenes: Optional[Callable] = None,
                            on_prompts: Optional[Callable] = None,
                            on_videos: Optional[Callable] = None,
                            on_logs: Optional[Callable] = None):
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
    
    def _update_progress(self, message: str, progress: float):
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    async def run(self, video_paths: List[str], project_config: Dict[str, Any]):
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        self.is_running = True
        self.logger.info(
            "Khởi chạy workflow mới",
            {
                "num_videos": len(video_paths),
                "project_name": self.project_name,
                "duration": project_config.get("duration"),
                "style": project_config.get("style"),
            },
        )

        try:
            script_text: str = project_config.get("script", "")
            video_analysis_override = project_config.get("video_analysis_override")
            if script_text:
                self.logger.info(
                    "Dùng script_text từ project làm VIDEO_ANALYSIS",
                    {"script_length": len(script_text)},
                )
                video_analysis = script_text
            elif video_analysis_override:
                self.logger.info(
                    "Dùng video_analysis_override từ ô Kịch bản/Ý tưởng",
                    {"override_length": len(video_analysis_override)},
                )
                video_analysis = video_analysis_override
            else:
                self.logger.info(
                    "Không có sẵn VIDEO_ANALYSIS, bắt đầu phân tích video tự động",
                    {"video_paths": video_paths},
                )
                video_analysis, gemini_link = await self.video_analyzer.analyze_videos(video_paths, self.project_name)
                self.logger.info(
                    "Hoàn thành phân tích video",
                    {"analysis_length": len(video_analysis), "gemini_link": gemini_link},
                )
                
                if gemini_link:
                    project = project_manager.load_project(project_config.get("file", ""))
                    if project:
                        project["gemini_video_analysis_link"] = gemini_link
                        project_manager.save_project(project)
                        self.logger.info(f"Đã lưu Gemini link vào project: {gemini_link}")
            
            user_script = project_config.get("script", "")
            content = await self.content_generator.generate_content(video_analysis, user_script, self.project_name)
            self.logger.info(
                "Đã tạo nội dung từ VIDEO_ANALYSIS",
                {
                    "full_content_length": len(content.get("full_content", "")),
                    "has_characters_section": bool(content.get("characters_section")),
                    "has_story_section": bool(content.get("story_section")),
                    "has_storyboard_section": bool(content.get("storyboard_section")),
                },
            )
            
            characters = await self.character_extractor.extract_characters(content["full_content"], self.project_name, project_config)
            self.logger.info(
                "Đã trích xuất nhân vật",
                {"num_characters": len(characters) if isinstance(characters, dict) else None},
            )
            if "characters" in self.update_callbacks:
                self.update_callbacks["characters"](characters)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            scenes = await self.scene_generator.generate_scenes(
                content["full_content"], 
                characters,
                self.project_name,
                project_config
            )
            self.logger.info(
                "Đã tạo scenes từ nội dung và nhân vật",
                {"num_scenes": len(scenes)},
            )
            if "scenes" in self.update_callbacks:
                self.update_callbacks["scenes"](scenes)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            veo3_prompts = await self.veo3_prompt_generator.generate_prompts(scenes, characters, self.project_name)
            self.logger.info(
                "Đã tạo VEO3 prompts từ scenes",
                {"num_prompts": len(veo3_prompts)},
            )
            if "prompts" in self.update_callbacks:
                self.update_callbacks["prompts"](veo3_prompts)
            if "logs" in self.update_callbacks:
                self.update_callbacks["logs"]()
            
            use_browser = project_config.get("use_browser_automation", True)
            video_results = await veo3_flow.generate_videos(veo3_prompts, project_config, use_browser)
            self.logger.info(
                "Đã gọi generate_videos cho VEO3",
                {
                    "num_requests": len(veo3_prompts),
                    "use_browser": use_browser,
                    "num_results": len(video_results),
                },
            )
            
            project = project_manager.load_project(project_config.get("file", ""))
            if project:
                project["characters"] = characters
                project["scenes"] = scenes
                project["prompts"] = veo3_prompts
                project["videos"] = video_results
                project_manager.save_project(project)
                self.logger.info(
                    "Đã lưu kết quả workflow vào project",
                    {
                        "project_file": project.get("file"),
                        "num_characters": len(characters) if isinstance(characters, dict) else None,
                        "num_scenes": len(scenes),
                        "num_prompts": len(veo3_prompts),
                        "num_videos": len(video_results),
                    },
                )
            
            self.logger.info("Workflow hoàn thành thành công")
            
            return {
                "characters": characters,
                "scenes": scenes,
                "prompts": veo3_prompts,
                # "videos": video_results
            }
            
        except Exception as e:
            self.logger.error("Workflow error", {"error": str(e)})
            raise
        finally:
            self.is_running = False
            from ..integrations.browser_automation import browser_automation
            try:
                await browser_automation.stop()
            except Exception:
                pass
    
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
            
            use_browser = project_config.get("use_browser_automation", True)
            video_results = await veo3_flow.generate_videos(veo3_prompts, project_config, use_browser, on_video_generated)
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
            from ..integrations.browser_automation import browser_automation
            try:
                await browser_automation.stop()
            except Exception:
                pass

