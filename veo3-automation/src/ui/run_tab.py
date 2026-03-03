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
        try:
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
                on_generate_content=lambda: self._run_step("generate_content"),
                on_run_all=self._run_all_steps
            )
            self.result_panel = ResultPanel(self, on_run_step=self._run_step, on_retry_video=self._retry_video)
        except Exception as e:
            import traceback
            print(f"Lỗi khi khởi tạo RunTab: {e}")
            traceback.print_exc()
            raise
    
    def _close_browser_tab(self, loop):
        try:
            # Không đóng/mở tab nữa, chỉ giữ nguyên một tab duy nhất.
            if self.logger:
                self.logger.info("Bỏ qua đóng/mở tab, giữ nguyên tab hiện tại")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Lỗi khi đóng/mở tab mới: {e}")
    
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
                videos = project_data.get("videos", [])
                has_videos = len(videos) > 0 and any(v.get("status") == "SUCCESSFUL" for v in videos)
                self.result_panel.update_project_links(gemini_link, flow_link, has_videos)
        else:
            self.result_panel.clear_all()
    
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
            if videos and len(videos) > 0:
                has_successful_video = any(v.get("status") == "SUCCESSFUL" for v in videos)
                if has_successful_video:
                    from ..data.project_manager import project_manager
                    project_file = project_config.get("file", "")
                    if project_file:
                        project = project_manager.load_project(project_file)
                        if project:
                            gemini_link = project.get("gemini_project_link", "")
                            flow_link = project.get("project_link", "")
                            has_videos = True
                            self.after(0, lambda gl=gemini_link, fl=flow_link, hv=has_videos: 
                                      self.result_panel.update_project_links(gl, fl, hv))
        
        def update_ui_logs():
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        def update_ui_project_links(gemini_link: str, flow_link: str):
            self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl, True))
            if flow_link:
                self.after(0, lambda fl=flow_link: self._update_project_link_entry(fl))
            if gemini_link:
                self.after(0, lambda gl=gemini_link: self._update_gemini_link_entry(gl))
        
        self.workflow.set_update_callbacks(
            on_characters=update_ui_characters,
            on_scenes=update_ui_scenes,
            on_prompts=update_ui_prompts,
            on_videos=update_ui_videos,
            on_logs=update_ui_logs,
            on_project_links=update_ui_project_links
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
                project_config = self.project_panel.get_project_config()
                video_analysis, gemini_link = loop.run_until_complete(
                    video_analyzer.analyze_videos(self.video_paths, project_config=project_config)
                )
                self.manual_video_analysis = video_analysis

                if gemini_link:
                    project = project_manager.load_project(project_config.get("file", ""))
                    if project:
                        project["gemini_video_analysis_link"] = gemini_link
                        project_manager.save_project(project)
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
            if videos and len(videos) > 0:
                has_successful_video = any(v.get("status") == "SUCCESSFUL" for v in videos)
                if has_successful_video:
                    from ..data.project_manager import project_manager
                    project_file = project_config.get("file", "")
                    if project_file:
                        project = project_manager.load_project(project_file)
                        if project:
                            gemini_link = project.get("gemini_project_link", "")
                            flow_link = project.get("project_link", "")
                            has_videos = True
                            self.after(0, lambda gl=gemini_link, fl=flow_link, hv=has_videos: 
                                      self.result_panel.update_project_links(gl, fl, hv))
        
        def update_ui_logs():
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        def update_ui_project_links(gemini_link: str, flow_link: str):
            self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl, True))
            if flow_link:
                self.after(0, lambda fl=flow_link: self._update_project_link_entry(fl))
            if gemini_link:
                self.after(0, lambda gl=gemini_link: self._update_gemini_link_entry(gl))
        
        self.workflow.set_update_callbacks(
            on_characters=update_ui_characters,
            on_scenes=update_ui_scenes,
            on_prompts=update_ui_prompts,
            on_videos=update_ui_videos,
            on_logs=update_ui_logs,
            on_project_links=update_ui_project_links
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
    
    def _run_all_steps(self):
        if self.workflow and self.workflow.is_running:
            messagebox.showwarning("Cảnh báo", "Workflow đang chạy!")
            return
        
        if not self.video_paths:
            messagebox.showwarning("Cảnh báo", "Vui lòng upload video trước!")
            return
        
        project_config = self.project_panel.get_project_config()
        if self.manual_video_analysis:
            project_config["video_analysis_override"] = self.manual_video_analysis
        
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
            if videos and len(videos) > 0:
                has_successful_video = any(v.get("status") == "SUCCESSFUL" for v in videos)
                if has_successful_video:
                    from ..data.project_manager import project_manager
                    project_file = project_config.get("file", "")
                    if project_file:
                        project = project_manager.load_project(project_file)
                        if project:
                            gemini_link = project.get("gemini_project_link", "")
                            flow_link = project.get("project_link", "")
                            has_videos = True
                            self.after(0, lambda gl=gemini_link, fl=flow_link, hv=has_videos: 
                                      self.result_panel.update_project_links(gl, fl, hv))
        
        def update_ui_logs():
            self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
        
        def update_ui_project_links(gemini_link: str, flow_link: str):
            self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl, True))
            if flow_link:
                self.after(0, lambda fl=flow_link: self._update_project_link_entry(fl))
            if gemini_link:
                self.after(0, lambda gl=gemini_link: self._update_gemini_link_entry(gl))
        
        self.workflow.set_update_callbacks(
            on_characters=update_ui_characters,
            on_scenes=update_ui_scenes,
            on_prompts=update_ui_prompts,
            on_videos=update_ui_videos,
            on_logs=update_ui_logs,
            on_project_links=update_ui_project_links
        )
        
        self.after(0, lambda: self.project_panel.set_workflow_running(True))
        
        def run_all_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.logger.info("🚀 Bắt đầu chạy tất cả các bước...")
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                project_file = project_config.get("file", "")
                project_data = data_loader.load_project_data(project_file) if project_file else None
                
                script_text: str = project_config.get("script", "")
                video_analysis_override = project_config.get("video_analysis_override")
                
                video_analysis = None
                if project_data and project_data.get("video_analysis"):
                    video_analysis = project_data["video_analysis"]
                    self.logger.info("⏭️ Bước 1/6: Phân tích video - Đã có sẵn, bỏ qua")
                elif script_text:
                    video_analysis = script_text
                    self.logger.info("⏭️ Bước 1/6: Phân tích video - Sử dụng script_text từ project")
                elif video_analysis_override:
                    video_analysis = video_analysis_override
                    self.logger.info("⏭️ Bước 1/6: Phân tích video - Sử dụng video_analysis_override")
                else:
                    self.logger.info("📹 Bước 1/6: Phân tích video...")
                    self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                    video_analysis = loop.run_until_complete(
                        self.workflow.run_step_analyze_video(self.video_paths, project_config)
                    )
                    self.logger.info("✓ Hoàn thành phân tích video")
                    
                    self._close_browser_tab(loop)
                
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                content = None
                if project_data and project_data.get("content"):
                    content = {"full_content": project_data["content"]}
                    self.logger.info("⏭️ Bước 2/6: Tạo nội dung - Đã có sẵn, bỏ qua")
                else:
                    self.logger.info("📝 Bước 2/6: Tạo nội dung...")
                    self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                    content = loop.run_until_complete(
                        self.workflow.run_step_generate_content(video_analysis, project_config)
                    )
                    self.logger.info("✓ Hoàn thành tạo nội dung")
                    
                    self._close_browser_tab(loop)
                
                gemini_link = project_config.get("gemini_project_link", "")
                flow_link = project_config.get("project_link", "")
                self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                self.after(0, lambda: self._on_project_change())
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                full_content = content.get("full_content", "") if isinstance(content, dict) else content
                
                characters = None
                if project_data and project_data.get("characters"):
                    characters = project_data["characters"]
                    if isinstance(characters, dict) and len(characters) > 0:
                        self.logger.info("⏭️ Bước 3/6: Trích xuất nhân vật - Đã có sẵn, bỏ qua")
                    else:
                        characters = None
                
                if not characters:
                    self.logger.info("👥 Bước 3/6: Trích xuất nhân vật...")
                    self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                    characters = loop.run_until_complete(
                        self.workflow.run_step_extract_characters(full_content, project_config)
                    )
                    self.logger.info("✓ Hoàn thành trích xuất nhân vật")
                
                gemini_link = project_config.get("gemini_project_link", "")
                flow_link = project_config.get("project_link", "")
                self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                self.after(0, lambda: self.result_panel.update_characters(characters))
                self.after(0, lambda: self._on_project_change())
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                existing_scenes = []
                if project_data and project_data.get("scenes"):
                    existing_scenes = project_data["scenes"]
                    if isinstance(existing_scenes, list) and len(existing_scenes) > 0:
                        self.logger.info(f"⏭️ Bước 4/6: Tạo phân cảnh - Đã có {len(existing_scenes)} scene(s), bỏ qua")
                        scenes = existing_scenes
                    else:
                        existing_scenes = []
                
                if not existing_scenes or len(existing_scenes) == 0:
                    self.logger.info("🎬 Bước 4/6: Tạo phân cảnh...")
                    self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                    new_scenes = loop.run_until_complete(
                        self.workflow.run_step_generate_scenes(full_content, characters, project_config)
                    )
                    scenes = new_scenes
                    self.logger.info("✓ Hoàn thành tạo phân cảnh")
                    
                    self._close_browser_tab(loop)
                
                gemini_link = project_config.get("gemini_project_link", "")
                flow_link = project_config.get("project_link", "")
                self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                self.after(0, lambda: self.result_panel.update_scenes(scenes))
                self.after(0, lambda: self._on_project_change())
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                existing_prompts = []
                if project_data and project_data.get("prompts"):
                    existing_prompts = project_data["prompts"]
                    if isinstance(existing_prompts, list) and len(existing_prompts) > 0:
                        self.logger.info(f"⏭️ Bước 5/6: Tạo prompts VEO3 - Đã có {len(existing_prompts)} prompt(s)")
                
                expected_prompts_count = len(scenes) if scenes else 0
                if not existing_prompts or len(existing_prompts) < expected_prompts_count:
                    if existing_prompts:
                        self.logger.info(f"✍️ Bước 5/6: Tiếp tục tạo prompts VEO3 ({len(existing_prompts)}/{expected_prompts_count})...")
                    else:
                        self.logger.info("✍️ Bước 5/6: Tạo prompts VEO3...")
                    self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                    new_prompts = loop.run_until_complete(
                        self.workflow.run_step_generate_prompts(scenes, characters, project_config)
                    )
                    if existing_prompts and len(existing_prompts) > 0 and len(new_prompts) >= len(existing_prompts):
                        prompts = new_prompts
                    else:
                        prompts = new_prompts
                    self.logger.info(f"✓ Hoàn thành tạo prompts VEO3 ({len(prompts)}/{expected_prompts_count})")
                else:
                    prompts = existing_prompts
                    self.logger.info(f"⏭️ Bước 5/6: Tạo prompts VEO3 - Đã có đủ {len(prompts)} prompt(s), bỏ qua")
                
                gemini_link = project_config.get("gemini_project_link", "")
                flow_link = project_config.get("project_link", "")
                self.after(0, lambda gl=gemini_link, fl=flow_link: self.result_panel.update_project_links(gl, fl))
                self.after(0, lambda: self.result_panel.update_prompts(prompts))
                self.after(0, lambda: self._on_project_change())
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                existing_videos = []
                if project_data and project_data.get("videos"):
                    existing_videos = project_data["videos"]
                    if isinstance(existing_videos, list) and len(existing_videos) > 0:
                        self.logger.info(f"⏭️ Bước 6/6: Tạo video VEO3 - Đã có {len(existing_videos)} video(s)")
                
                expected_videos_count = len(prompts) if prompts else 0
                all_successful = False
                if existing_videos and len(existing_videos) > 0:
                    all_successful = all(v.get("status") == "SUCCESSFUL" for v in existing_videos if isinstance(v, dict))
                    if all_successful and len(existing_videos) >= expected_videos_count:
                        videos = existing_videos
                        self.logger.info(f"⏭️ Bước 6/6: Tạo video VEO3 - Đã có đủ {len(videos)} video(s) và hoàn thành, bỏ qua")
                
                if not all_successful or len(existing_videos) < expected_videos_count:
                    if existing_videos:
                        self.logger.info(f"🎥 Bước 6/6: Tiếp tục tạo video VEO3 ({len(existing_videos)}/{expected_videos_count})...")
                    else:
                        self.logger.info("🎥 Bước 6/6: Tạo video VEO3...")
                    self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                    new_videos = loop.run_until_complete(
                        self.workflow.run_step_generate_videos(prompts, project_config)
                    )
                    if existing_videos and len(existing_videos) > 0 and len(new_videos) >= len(existing_videos):
                        videos = new_videos
                    else:
                        videos = new_videos
                    self.logger.info(f"✓ Hoàn thành tạo video VEO3 ({len(videos)}/{expected_videos_count})")
                    
                    self._close_browser_tab(loop)
                
                gemini_link = project_config.get("gemini_project_link", "")
                flow_link = project_config.get("project_link", "")
                has_videos = len(videos) > 0 and any(v.get("status") == "SUCCESSFUL" for v in videos)
                self.after(0, lambda gl=gemini_link, fl=flow_link, hv=has_videos: self.result_panel.update_project_links(gl, fl, hv))
                self.after(0, lambda: self.result_panel.update_videos(videos))
                self.after(0, lambda: self._on_project_change())
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                
                self.logger.info("🎉 Đã hoàn thành tất cả các bước!")
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                self.after(0, lambda: messagebox.showinfo("Thành công", "Đã hoàn thành tất cả các bước!"))
                
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"❌ Lỗi: {error_msg}")
                self.after(0, lambda: self.result_panel.update_logs(self.logger.get_logs()))
                self.after(0, lambda msg=error_msg: messagebox.showerror("Lỗi", f"Chạy tất cả các bước thất bại: {msg}"))
            finally:
                try:
                    self._close_browser_tab(loop)
                except Exception:
                    pass
                self.after(0, lambda: self.project_panel.set_workflow_running(False))
                loop.close()
        
        thread = threading.Thread(target=run_all_async, daemon=True)
        thread.start()
    
    def _update_project_link_entry(self, flow_link: str):
        self.project_panel.project_link_entry.delete(0, "end")
        self.project_panel.project_link_entry.insert(0, flow_link)
    
    def _update_gemini_link_entry(self, gemini_link: str):
        self.project_panel.gemini_project_link_entry.delete(0, "end")
        self.project_panel.gemini_project_link_entry.insert(0, gemini_link)
