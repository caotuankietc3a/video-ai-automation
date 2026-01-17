import customtkinter as ctk
import asyncio
import threading
from tkinter import filedialog, messagebox
from .project_panel import ProjectPanel
from .result_panel import ResultPanel
from ..core.workflow import Workflow
from ..data.video_manager import video_manager
from ..data.project_manager import project_manager
from ..data.data_loader import data_loader
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
            on_analyze_video=self._analyze_video,
            on_generate_content=lambda: self._run_step("generate_content")
        )
        self.result_panel = ResultPanel(self, on_run_step=self._run_step, on_retry_video=self._retry_video)
    
    def _on_project_change(self):
        project_file = self.project_panel.project_file_var.get()
        if project_file:
            project_data = data_loader.load_project_data(project_file)
            if project_data:
                self.result_panel.update_characters(project_data.get("characters", {}))
                self.result_panel.update_scenes(project_data.get("scenes", []))
                self.result_panel.update_prompts(project_data.get("prompts", []))
                self.result_panel.update_videos(project_data.get("videos", []))
                
                project_name = project_data.get("project_name", "default")
                if self.logger is None or (hasattr(self.logger, 'project_name') and self.logger.project_name != project_name):
                    self.logger = Logger(project_name)
                logs = self.logger.get_logs()
                self.result_panel.update_logs(logs)
                
                if project_data.get("content"):
                    self.project_panel.script_textbox.delete("1.0", "end")
                    self.project_panel.script_textbox.insert("1.0", project_data.get("content", ""))
                
                project = project_data.get("project", {})
                gemini_link = project.get("gemini_project_link", "")
                flow_link = project.get("project_link", "")
                self.result_panel.update_project_links(gemini_link, flow_link)
    
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
        
        self.after(0, lambda: self.project_panel.set_workflow_running(True))
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.workflow.run(self.video_paths, project_config))
                gemini_link = project_config.get("gemini_project_link", "")
                flow_link = project_config.get("project_link", "")
                self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                self.after(0, lambda: self.result_panel.update_characters(result.get("characters", {})))
                self.after(0, lambda: self.result_panel.update_scenes(result.get("scenes", [])))
                self.after(0, lambda: self.result_panel.update_prompts(result.get("prompts", [])))
                if "videos" in result:
                    self.after(0, lambda: self.result_panel.update_videos(result["videos"]))
                self.after(0, lambda: messagebox.showinfo("Thành công", "Workflow hoàn thành!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi", f"Workflow thất bại: {str(e)}"))
            finally:
                self.after(0, lambda: self.project_panel.set_workflow_running(False))
                loop.close()
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def _stop_workflow(self):
        if self.workflow and self.workflow.is_running:
            self.workflow.stop()
            self.project_panel.set_workflow_running(False)
            messagebox.showinfo("Thông báo", "Workflow đã dừng")
        else:
            messagebox.showinfo("Thông báo", "Không có workflow nào đang chạy")
    
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
    
    def _run_step(self, step_name: str):
        if self.workflow and self.workflow.is_running:
            messagebox.showwarning("Cảnh báo", "Workflow đang chạy!")
            return
        
        project_config = self.project_panel.get_project_config()
        project_name = project_config.get("name", "default")
        
        if not self.workflow or self.workflow.project_name != project_name:
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
        
        self.after(0, lambda: self.project_panel.set_workflow_running(True))
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                project_file = project_config.get("file", "")
                project_data = data_loader.load_project_data(project_file) if project_file else {}
                
                if step_name == "generate_content":
                    video_analysis = project_data.get("video_analysis") or self.project_panel.script_textbox.get("1.0", "end-1c")
                    if not video_analysis:
                        messagebox.showwarning("Cảnh báo", "Vui lòng có video analysis hoặc script trước!")
                        return
                    
                    user_script = project_config.get("script", "")
                    result = loop.run_until_complete(
                        self.workflow.run_step_generate_content(video_analysis, project_config)
                    )
                    gemini_link = project_config.get("gemini_project_link", "")
                    flow_link = project_config.get("project_link", "")
                    self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                    self.after(0, lambda: self._on_project_change())
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã tạo nội dung!"))
                
                elif step_name == "extract_characters":
                    content = project_data.get("content") or self.project_panel.script_textbox.get("1.0", "end-1c")
                    if not content:
                        messagebox.showwarning("Cảnh báo", "Vui lòng có nội dung (content) trước!")
                        return
                    
                    result = loop.run_until_complete(
                        self.workflow.run_step_extract_characters(content, project_config)
                    )
                    gemini_link = project_config.get("gemini_project_link", "")
                    flow_link = project_config.get("project_link", "")
                    self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                    self.after(0, lambda: self.result_panel.update_characters(result))
                    self.after(0, lambda: self._on_project_change())
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã trích xuất nhân vật!"))
                
                elif step_name == "generate_scenes":
                    content = project_data.get("content") or self.project_panel.script_textbox.get("1.0", "end-1c")
                    characters = project_data.get("characters", {})
                    
                    if not content:
                        messagebox.showwarning("Cảnh báo", "Vui lòng có nội dung (content) trước!")
                        return
                    if not characters:
                        messagebox.showwarning("Cảnh báo", "Vui lòng trích xuất nhân vật trước!")
                        return
                    
                    result = loop.run_until_complete(
                        self.workflow.run_step_generate_scenes(content, characters, project_config)
                    )
                    gemini_link = project_config.get("gemini_project_link", "")
                    flow_link = project_config.get("project_link", "")
                    self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                    self.after(0, lambda: self.result_panel.update_scenes(result))
                    self.after(0, lambda: self._on_project_change())
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã tạo phân cảnh!"))
                
                elif step_name == "generate_prompts":
                    scenes = project_data.get("scenes", [])
                    characters = project_data.get("characters", {})
                    
                    if not scenes:
                        messagebox.showwarning("Cảnh báo", "Vui lòng tạo phân cảnh trước!")
                        return
                    if not characters:
                        messagebox.showwarning("Cảnh báo", "Vui lòng trích xuất nhân vật trước!")
                        return
                    
                    result = loop.run_until_complete(
                        self.workflow.run_step_generate_prompts(scenes, characters, project_config)
                    )
                    gemini_link = project_config.get("gemini_project_link", "")
                    flow_link = project_config.get("project_link", "")
                    self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                    self.after(0, lambda: self.result_panel.update_prompts(result))
                    self.after(0, lambda: self._on_project_change())
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã tạo prompts VEO3!"))
                
                elif step_name == "generate_videos":
                    prompts = project_data.get("prompts", [])
                    
                    if not prompts:
                        messagebox.showwarning("Cảnh báo", "Vui lòng tạo prompts VEO3 trước!")
                        return
                    
                    result = loop.run_until_complete(
                        self.workflow.run_step_generate_videos(prompts, project_config)
                    )
                    gemini_link = project_config.get("gemini_project_link", "")
                    flow_link = project_config.get("project_link", "")
                    self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                    self.after(0, lambda: self.result_panel.update_videos(result))
                    self.after(0, lambda: self._on_project_change())
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã tạo video VEO3!"))
                
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda msg=error_msg: messagebox.showerror("Lỗi", f"Step thất bại: {msg}"))
            finally:
                self.after(0, lambda: self.project_panel.set_workflow_running(False))
                loop.close()
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def _retry_video(self, index: int, prompt: str):
        if self.workflow and self.workflow.is_running:
            messagebox.showwarning("Cảnh báo", "Workflow đang chạy!")
            return
        
        project_config = self.project_panel.get_project_config()
        project_name = project_config.get("name", "default")
        
        if not self.workflow or self.workflow.project_name != project_name:
            self.workflow = Workflow(project_name)
            self.logger = Logger(project_name)
        
        def progress_callback(message: str, progress: float):
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        self.workflow.set_progress_callback(progress_callback)
        
        def update_ui_logs():
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        self.workflow.set_update_callbacks(
            on_logs=update_ui_logs
        )
        
        self.after(0, lambda: self.project_panel.set_workflow_running(True))
        
        def retry_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from ..integrations.veo3_flow import veo3_flow
                use_browser = project_config.get("use_browser_automation", True)
                result = loop.run_until_complete(
                    veo3_flow.retry_video(prompt, project_config, use_browser)
                )
                
                project_file = project_config.get("file", "")
                if project_file:
                    project_data = data_loader.load_project_data(project_file) if project_file else {}
                    videos = project_data.get("videos", [])
                    
                    if index < len(videos):
                        videos[index] = result
                    else:
                        videos.append(result)
                    
                    from ..data.project_manager import project_manager
                    project = project_manager.load_project(project_file)
                    if project:
                        project["videos"] = videos
                        project_manager.save_project(project)
                    
                    self.after(0, lambda vids=videos: self.result_panel.update_videos(vids))
                    self.after(0, lambda: self._on_project_change())
                else:
                    self.after(0, lambda vid=result: self.result_panel.update_videos([vid]))
                
                if result.get("status") == "SUCCESSFUL":
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã retry video thành công!"))
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.after(0, lambda msg=error_msg: messagebox.showerror("Lỗi", f"Retry video thất bại: {msg}"))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda msg=error_msg: messagebox.showerror("Lỗi", f"Retry video thất bại: {msg}"))
            finally:
                self.after(0, lambda: self.project_panel.set_workflow_running(False))
                loop.close()
        
        thread = threading.Thread(target=retry_async, daemon=True)
        thread.start()

