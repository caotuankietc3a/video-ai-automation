import customtkinter as ctk
import asyncio
import threading
from tkinter import filedialog, messagebox
from .project_panel import ProjectPanel
from .result_panel import ResultPanel
from ..core.workflow import Workflow
from ..data.video_manager import video_manager
from ..data.project_manager import project_manager
from ..utils.logger import Logger

class RunTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        
        self.workflow = None
        self.video_paths = []
        self.logger = None
        self.manual_video_analysis: str | None = None
        
        self.project_panel = ProjectPanel(
            self, 
            on_project_change=self._on_project_change, 
            on_start=self._start_workflow, 
            on_stop=self._stop_workflow,
            on_analyze_video=self._analyze_video
        )
        self.result_panel = ResultPanel(self)
    
    def _on_project_change(self):
        project_file = self.project_panel.project_file_var.get()
        if project_file:
            project = project_manager.load_project(project_file)
            if project:
                self.result_panel.update_characters(project.get("characters", {}))
                self.result_panel.update_scenes(project.get("scenes", []))
                self.result_panel.update_prompts(project.get("prompts", []))
                self.result_panel.update_videos(project.get("videos", []))
                
                if self.logger is None:
                    self.logger = Logger(project.get("name", "default"))
                logs = self.logger.get_logs()
                self.result_panel.update_logs(logs)
    
    def _start_workflow(self):
        if self.workflow and self.workflow.is_running:
            messagebox.showwarning("Cảnh báo", "Workflow đang chạy!")
            return
        
        project_config = self.project_panel.get_project_config()
        if self.manual_video_analysis:
            project_config["video_analysis_override"] = self.manual_video_analysis
        if not self.video_paths:
            messagebox.showwarning("Cảnh báo", "Vui lòng upload video trước!")
            return
        
        project_name = project_config.get("name", "default")
        self.workflow = Workflow(project_name)
        self.logger = Logger(project_name)
        
        def progress_callback(message: str, progress: float):
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        self.workflow.set_progress_callback(progress_callback)
        
        def update_ui_characters(characters):
            self.after(0, lambda: self.result_panel.update_characters(characters))
        
        def update_ui_scenes(scenes):
            self.after(0, lambda: self.result_panel.update_scenes(scenes))
        
        def update_ui_prompts(prompts):
            self.after(0, lambda: self.result_panel.update_prompts(prompts))
        
        def update_ui_videos(videos):
            self.after(0, lambda: self.result_panel.update_videos(videos))
        
        def update_ui_logs():
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        self.workflow.set_update_callbacks(
            on_characters=update_ui_characters,
            on_scenes=update_ui_scenes,
            on_prompts=update_ui_prompts,
            on_videos=update_ui_videos,
            on_logs=update_ui_logs
        )
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.workflow.run(self.video_paths, project_config))
                self.after(0, lambda: self.result_panel.update_characters(result.get("characters", {})))
                self.after(0, lambda: self.result_panel.update_scenes(result.get("scenes", [])))
                self.after(0, lambda: self.result_panel.update_prompts(result.get("prompts", [])))
                if "videos" in result:
                    self.after(0, lambda: self.result_panel.update_videos(result["videos"]))
                self.after(0, lambda: messagebox.showinfo("Thành công", "Workflow hoàn thành!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi", f"Workflow thất bại: {str(e)}"))
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def _stop_workflow(self):
        if self.workflow:
            self.workflow.stop()
            messagebox.showinfo("Thông báo", "Workflow đã dừng")
    
    def upload_video(self, file_path: str = None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Chọn video",
                filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
            )
        
        if file_path:
            project_name = self.project_panel.project_name_entry.get() or "default"
            saved_path = video_manager.upload_video(file_path, project_name)
            self.video_paths.append(saved_path)
            messagebox.showinfo("Thành công", f"Đã upload video: {saved_path}")
    
    def upload_video_from_url(self, url: str):
        project_name = self.project_panel.project_name_entry.get() or "default"
        messagebox.showinfo("Thông báo", "Đang tải video từ URL...")
        
        def download_async():
            saved_path = video_manager.download_video_from_url(url, project_name)
            if saved_path:
                self.video_paths.append(saved_path)
                messagebox.showinfo("Thành công", f"Đã tải video: {saved_path}")
            else:
                messagebox.showerror("Lỗi", "Không thể tải video từ URL")
        
        thread = threading.Thread(target=download_async, daemon=True)
        thread.start()
    
    def _analyze_video(self):
        if not self.video_paths:
            messagebox.showwarning("Cảnh báo", "Vui lòng upload video trước!")
            return
        
        from ..core.video_analyzer import VideoAnalyzer
        
        project_name = self.project_panel.project_name_entry.get() or "default"
        video_analyzer = VideoAnalyzer()
        
        def analyze_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                messagebox.showinfo("Thông báo", "Đang phân tích video...")
                video_analysis = loop.run_until_complete(video_analyzer.analyze_videos(self.video_paths))
                self.manual_video_analysis = video_analysis
                self.project_panel.update_video_analysis(video_analysis)
                messagebox.showinfo("Thành công", "Đã phân tích video xong!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Phân tích video thất bại: {str(e)}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=analyze_async, daemon=True)
        thread.start()

