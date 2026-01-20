import asyncio
import os
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from .workflow import Workflow
from ..data.video_manager import video_manager
from ..data.project_manager import project_manager
from ..integrations.browser_automation import stop_all_browser_instances
from ..utils.logger import Logger


@dataclass
class VideoConfig:
    url: str
    name: str
    duration: int = 120
    style: str = "3d_Pixar"
    aspect_ratio: str = "Khổ dọc (9:16)"
    veo_profile: str = "VEO3 ULTRA"
    ai_model: str = "VEO3 ULTRA"
    outputs_per_prompt: int = 1


@dataclass
class BatchConfig:
    videos: List[VideoConfig]
    max_concurrent: int = 2
    default_duration: int = 120
    default_style: str = "3d_Pixar"
    default_aspect_ratio: str = "Khổ dọc (9:16)"
    default_veo_profile: str = "VEO3 ULTRA"
    default_ai_model: str = "VEO3 ULTRA"
    default_outputs_per_prompt: int = 1

    @classmethod
    def from_dict(cls, data: Dict) -> "BatchConfig":
        default_config = data.get("default_config", {})
        videos_data = data.get("videos", [])
        
        videos = []
        for v in videos_data:
            video = VideoConfig(
                url=v.get("url", ""),
                name=v.get("name", ""),
                duration=v.get("duration", default_config.get("duration", 120)),
                style=v.get("style", default_config.get("style", "3d_Pixar")),
                aspect_ratio=v.get("aspect_ratio", default_config.get("aspect_ratio", "Khổ dọc (9:16)")),
                veo_profile=v.get("veo_profile", default_config.get("veo_profile", "VEO3 ULTRA")),
                ai_model=v.get("ai_model", default_config.get("ai_model", "VEO3 ULTRA")),
                outputs_per_prompt=v.get("outputs_per_prompt", default_config.get("outputs_per_prompt", 1)),
            )
            videos.append(video)
        
        max_concurrent = data.get("max_concurrent", 2)
        
        return cls(
            videos=videos,
            max_concurrent=max_concurrent,
            default_duration=default_config.get("duration", 120),
            default_style=default_config.get("style", "3d_Pixar"),
            default_aspect_ratio=default_config.get("aspect_ratio", "Khổ dọc (9:16)"),
            default_veo_profile=default_config.get("veo_profile", "VEO3 ULTRA"),
            default_ai_model=default_config.get("ai_model", "VEO3 ULTRA"),
            default_outputs_per_prompt=default_config.get("outputs_per_prompt", 1),
        )


@dataclass
class VideoResult:
    name: str
    url: str
    success: bool
    error: Optional[str] = None
    project_file: Optional[str] = None
    videos_generated: int = 0


class BatchRunner:
    def __init__(self, config: BatchConfig, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.logger = Logger("batch_runner")
        self.results: List[VideoResult] = []
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        self.progress_callback = callback
    
    def _log(self, message: str):
        self.logger.info(message)
        print(message)
    
    async def run(self) -> List[VideoResult]:
        total = len(self.config.videos)
        self._log(f"🚀 Bắt đầu batch runner với {total} videos")
        self._log(f"📊 Max concurrent: {self.config.max_concurrent} (mỗi project có browser riêng)")
        
        if self.dry_run:
            self._log("🔍 DRY RUN MODE - Không thực hiện thay đổi thực tế")
            for i, video in enumerate(self.config.videos, 1):
                self._log(f"  [{i}/{total}] {video.name}: {video.url}")
                self._log(f"    - Duration: {video.duration}s")
                self._log(f"    - Style: {video.style}")
                self._log(f"    - Aspect Ratio: {video.aspect_ratio}")
                self._log(f"    - VEO Profile: {video.veo_profile}")
                self._log(f"    - Outputs per prompt: {video.outputs_per_prompt}")
            return []
        
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        tasks = []
        for i, video_config in enumerate(self.config.videos):
            task = self._process_video_with_semaphore(video_config, i + 1, total, semaphore, i)
            tasks.append(task)
        
        self.results = await asyncio.gather(*tasks)
        
        try:
            await stop_all_browser_instances()
        except Exception:
            pass
        
        self._print_summary()
        
        return self.results
    
    async def _process_video_with_semaphore(
        self,
        video_config: VideoConfig,
        index: int,
        total: int,
        semaphore: asyncio.Semaphore,
        browser_index: int
    ) -> VideoResult:
        async with semaphore:
            return await self._process_video(video_config, index, total, browser_index)
    
    async def _process_video(
        self, 
        video_config: VideoConfig, 
        index: int, 
        total: int,
        browser_index: int = 0
    ) -> VideoResult:
        browser_instance_id = f"batch_{browser_index}"
        self._log(f"📥 [{index}/{total}] Bắt đầu xử lý: {video_config.name} (browser: {browser_instance_id})")
        
        if self.progress_callback:
            self.progress_callback(video_config.name, index, total)
        
        try:
            video_path = video_manager.download_video_from_url(
                video_config.url, 
                video_config.name
            )
            
            if not video_path:
                raise Exception(f"Không thể tải video từ: {video_config.url}")
            
            self._log(f"✅ [{index}/{total}] Đã tải video: {video_path}")
            
            project = project_manager.create_project(video_config.name)
            project_file = project["file"]
            
            project_manager.update_project(project_file, {
                "name": video_config.name,
                "style": video_config.style,
                "duration": video_config.duration,
                "aspect_ratio": video_config.aspect_ratio,
                "veo_profile": video_config.veo_profile,
                "ai_model": video_config.ai_model,
                "outputs_per_prompt": video_config.outputs_per_prompt,
            })
            
            self._log(f"📁 [{index}/{total}] Đã tạo project: {project_file}")
            
            workflow = Workflow(video_config.name, browser_instance_id=browser_instance_id)
            
            project_config = {
                "name": video_config.name,
                "file": project_file,
                "style": video_config.style,
                "duration": video_config.duration,
                "aspect_ratio": video_config.aspect_ratio,
                "veo_profile": video_config.veo_profile,
                "ai_model": video_config.ai_model,
                "outputs_per_prompt": video_config.outputs_per_prompt,
                "use_browser_automation": True,
            }
            
            result = await workflow.run([video_path], project_config)
            
            videos_count = len(result.get("videos", [])) if result else 0
            
            self._log(f"🎉 [{index}/{total}] Hoàn thành: {video_config.name} - {videos_count} videos")
            
            return VideoResult(
                name=video_config.name,
                url=video_config.url,
                success=True,
                project_file=project_file,
                videos_generated=videos_count,
            )
            
        except Exception as e:
            error_msg = str(e)
            self._log(f"❌ [{index}/{total}] Lỗi {video_config.name}: {error_msg}")
            
            return VideoResult(
                name=video_config.name,
                url=video_config.url,
                success=False,
                error=error_msg,
            )
    
    def _print_summary(self):
        self._log("\n" + "=" * 60)
        self._log("📊 BATCH RUNNER SUMMARY")
        self._log("=" * 60)
        
        success_count = sum(1 for r in self.results if r.success)
        failed_count = len(self.results) - success_count
        total_videos = sum(r.videos_generated for r in self.results)
        
        self._log(f"✅ Thành công: {success_count}/{len(self.results)}")
        self._log(f"❌ Thất bại: {failed_count}/{len(self.results)}")
        self._log(f"🎬 Tổng videos tạo được: {total_videos}")
        
        if failed_count > 0:
            self._log("\n⚠️ Danh sách lỗi:")
            for r in self.results:
                if not r.success:
                    self._log(f"  - {r.name}: {r.error}")
        
        self._log("=" * 60)
