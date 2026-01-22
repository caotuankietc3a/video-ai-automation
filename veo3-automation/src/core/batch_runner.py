import asyncio
import os
import multiprocessing
from multiprocessing import Process, Queue
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field, asdict
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
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "VideoConfig":
        return cls(
            url=data.get("url", ""),
            name=data.get("name", ""),
            duration=data.get("duration", 120),
            style=data.get("style", "3d_Pixar"),
            aspect_ratio=data.get("aspect_ratio", "Khổ dọc (9:16)"),
            veo_profile=data.get("veo_profile", "VEO3 ULTRA"),
            ai_model=data.get("ai_model", "VEO3 ULTRA"),
            outputs_per_prompt=data.get("outputs_per_prompt", 1),
        )


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
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "VideoResult":
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            success=data.get("success", False),
            error=data.get("error"),
            project_file=data.get("project_file"),
            videos_generated=data.get("videos_generated", 0),
        )


def _run_worker_process(
    process_id: int,
    videos_data: List[Dict],
    total_videos: int,
    result_queue: Queue
):
    from .workflow import Workflow
    from ..data.video_manager import video_manager
    from ..data.project_manager import project_manager
    
    print(f"🔧 [Process {process_id}] Khởi động với {len(videos_data)} videos")
    
    results = []
    for video_data in videos_data:
        video_config = VideoConfig.from_dict(video_data["config"])
        index = video_data["index"]
        video_path = video_data.get("video_path")
        
        browser_instance_id = f"process_{process_id}"
        print(f"📥 [Process {process_id}] [{index}/{total_videos}] Bắt đầu: {video_config.name}")
        
        try:
            if not video_path:
                raise Exception(f"Không tìm thấy video path cho: {video_config.name}")
            
            if not os.path.exists(video_path):
                raise Exception(f"Video file không tồn tại: {video_path}")
            
            print(f"✅ [Process {process_id}] [{index}/{total_videos}] Sử dụng video: {video_path}")
            
            existing_project = None
            project_files = project_manager.list_projects()
            for pf in project_files:
                proj = project_manager.load_project(pf)
                if proj and proj.get("name") == video_config.name:
                    existing_project = proj
                    break
            
            if existing_project:
                project_file = existing_project["file"]
                print(f"📁 [Process {process_id}] [{index}/{total_videos}] Đã tìm thấy project: {project_file}")
                project_manager.update_project(project_file, {
                    "name": video_config.name,
                    "style": video_config.style,
                    "duration": video_config.duration,
                    "aspect_ratio": video_config.aspect_ratio,
                    "veo_profile": video_config.veo_profile,
                    "ai_model": video_config.ai_model,
                    "outputs_per_prompt": video_config.outputs_per_prompt,
                })
            else:
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
                print(f"📁 [Process {process_id}] [{index}/{total_videos}] Đã tạo project mới: {project_file}")
            
            workflow = Workflow(video_config.name, browser_instance_id=browser_instance_id)
            
            project_config_dict = {
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
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(workflow.run([video_path], project_config_dict))
            finally:
                loop.close()
            
            project_after = project_manager.load_project(project_file)
            videos_count = len(project_after.get("videos", [])) if project_after else 0
            
            print(f"🎉 [Process {process_id}] [{index}/{total_videos}] Hoàn thành: {video_config.name}")
            
            results.append(VideoResult(
                name=video_config.name,
                url=video_config.url,
                success=True,
                project_file=project_file,
                videos_generated=videos_count,
            ).to_dict())
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [Process {process_id}] [{index}/{total_videos}] Lỗi {video_config.name}: {error_msg}")
            
            results.append(VideoResult(
                name=video_config.name,
                url=video_config.url,
                success=False,
                error=error_msg,
            ).to_dict())
    
    print(f"✅ [Process {process_id}] Hoàn thành tất cả {len(videos_data)} videos")
    result_queue.put(results)


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
    
    def _split_videos_for_processes(self, videos: List[VideoConfig], num_processes: int) -> List[List[Dict]]:
        chunks: List[List[Dict]] = [[] for _ in range(num_processes)]
        
        for i, video in enumerate(videos):
            process_idx = i % num_processes
            chunks[process_idx].append({
                "config": video.to_dict(),
                "index": i + 1
            })
        
        return chunks
    
    def _download_all_videos(self) -> Dict[str, Optional[str]]:
        from ..data.video_manager import video_manager
        
        self._log("\n📥 Bắt đầu download tất cả videos...")
        video_paths: Dict[str, Optional[str]] = {}
        
        for i, video_config in enumerate(self.config.videos, 1):
            self._log(f"[{i}/{len(self.config.videos)}] Kiểm tra video: {video_config.name}")
            
            existing_video = video_manager.get_existing_video(video_config.name)
            if existing_video:
                self._log(f"  ✓ Video đã tồn tại: {existing_video}")
                video_paths[video_config.name] = existing_video
            else:
                self._log(f"  📥 Đang tải video từ: {video_config.url}")
                video_path = video_manager.download_video_from_url(
                    video_config.url,
                    video_config.name
                )
                if video_path:
                    self._log(f"  ✓ Đã tải video: {video_path}")
                    video_paths[video_config.name] = video_path
                else:
                    self._log(f"  ❌ Không thể tải video từ: {video_config.url}")
                    video_paths[video_config.name] = None
        
        self._log(f"\n✅ Hoàn thành download: {sum(1 for v in video_paths.values() if v)}/{len(video_paths)} videos")
        return video_paths
    
    def run(self) -> List[VideoResult]:
        total = len(self.config.videos)
        num_processes = min(self.config.max_concurrent, total)
        
        self._log(f"🚀 Bắt đầu batch runner với {total} videos")
        self._log(f"📊 Số processes: {num_processes} (mỗi process có browser riêng)")
        
        if self.dry_run:
            self._log("🔍 DRY RUN MODE - Không thực hiện thay đổi thực tế")
            for i, video in enumerate(self.config.videos, 1):
                process_idx = (i - 1) % num_processes
                self._log(f"  [Process {process_idx}] [{i}/{total}] {video.name}: {video.url}")
                self._log(f"    - Duration: {video.duration}s")
                self._log(f"    - Style: {video.style}")
                self._log(f"    - Aspect Ratio: {video.aspect_ratio}")
                self._log(f"    - VEO Profile: {video.veo_profile}")
                self._log(f"    - Outputs per prompt: {video.outputs_per_prompt}")
            return []
        
        video_paths = self._download_all_videos()
        
        for video_config in self.config.videos:
            if video_config.name not in video_paths or not video_paths[video_config.name]:
                self._log(f"⚠️ Bỏ qua {video_config.name} vì không có video")
        
        valid_videos = [v for v in self.config.videos if video_paths.get(v.name)]
        if not valid_videos:
            self._log("❌ Không có video nào để xử lý")
            return []
        
        video_chunks = self._split_videos_for_processes(valid_videos, num_processes)
        
        for chunk in video_chunks:
            for video_data in chunk:
                video_name = video_data["config"]["name"]
                video_data["video_path"] = video_paths.get(video_name)
        
        self._log(f"\n📦 Phân bổ videos cho {num_processes} processes:")
        for i, chunk in enumerate(video_chunks):
            video_names = [v["config"]["name"] for v in chunk]
            self._log(f"  Process {i}: {len(chunk)} videos - {video_names}")
        self._log("")
        
        result_queue: Queue = Queue()
        processes: List[Process] = []
        
        for i, chunk in enumerate(video_chunks):
            if len(chunk) == 0:
                continue
            
            p = Process(
                target=_run_worker_process,
                args=(i, chunk, len(valid_videos), result_queue)
            )
            processes.append(p)
            p.start()
            self._log(f"🔧 Đã khởi động Process {i}")
        
        for p in processes:
            p.join()
        
        all_results_dicts: List[Dict] = []
        while not result_queue.empty():
            results_from_process = result_queue.get()
            all_results_dicts.extend(results_from_process)
        
        self.results = [VideoResult.from_dict(r) for r in all_results_dicts]
        
        self._print_summary()
        
        return self.results
    
    async def run_async(self) -> List[VideoResult]:
        return self.run()
    
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
