import customtkinter as ctk
from typing import Callable, Optional
from ..data.project_manager import project_manager
from ..config.constants import VIDEO_STYLES, VEO_PROFILES, ASPECT_RATIOS

class ProjectPanel(ctk.CTkFrame):
    def __init__(self, parent, on_project_change: Optional[Callable] = None, 
                 on_start: Optional[Callable] = None, on_stop: Optional[Callable] = None,
                 on_analyze_video: Optional[Callable] = None, on_generate_content: Optional[Callable] = None,
                 on_run_all: Optional[Callable] = None):
        super().__init__(parent)
        self.on_project_change = on_project_change
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_analyze_video = on_analyze_video
        self.on_generate_content = on_generate_content
        self.on_run_all = on_run_all
        self.current_project = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.pack(side="left", fill="both", padx=10, pady=10)
        
        project_label = ctk.CTkLabel(self, text="Dự án:", font=ctk.CTkFont(size=14, weight="bold"))
        project_label.pack(pady=(10, 5))
        
        self.project_name_entry = ctk.CTkEntry(self, placeholder_text="Tên dự án")
        self.project_name_entry.pack(fill="x", padx=10, pady=5)
        self.project_name_entry.bind("<KeyRelease>", self._on_name_change)
        
        workflow_control_frame = ctk.CTkFrame(self)
        workflow_control_frame.pack(fill="x", padx=5, pady=(10, 5))
        
        workflow_label = ctk.CTkLabel(workflow_control_frame, text="Điều khiển Workflow:", font=ctk.CTkFont(size=12, weight="bold"))
        workflow_label.pack(side="left", padx=5)
        
        self.start_btn = ctk.CTkButton(workflow_control_frame, text="▶ Khởi động", fg_color="green", command=self._on_start_click, width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"))
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(workflow_control_frame, text="⏹ Dừng Workflow", fg_color="red", command=self._on_stop_click, state="disabled", width=140, height=35, font=ctk.CTkFont(size=12, weight="bold"))
        self.stop_btn.pack(side="left", padx=5)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        project_file_frame = ctk.CTkFrame(self.scrollable_frame)
        project_file_frame.pack(fill="x", pady=5)
        
        self.project_file_var = ctk.StringVar()
        self.project_file_dropdown = ctk.CTkComboBox(
            project_file_frame,
            values=project_manager.list_projects(),
            variable=self.project_file_var,
            command=self._on_file_select
        )
        self.project_file_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        copy_btn = ctk.CTkButton(project_file_frame, text="+ Copy", width=80, command=self._copy_project)
        copy_btn.pack(side="left", padx=2)
        
        new_btn = ctk.CTkButton(project_file_frame, text="+ Mới", width=80, command=self._new_project)
        new_btn.pack(side="left", padx=2)
        
        run_type_label = ctk.CTkLabel(self.scrollable_frame, text="Chọn kiểu chạy:")
        run_type_label.pack(pady=(10, 5))
        
        run_type_frame = ctk.CTkFrame(self.scrollable_frame)
        run_type_frame.pack(fill="x", pady=5)
        
        self.run_type_var = ctk.StringVar(value="Text to Video API")
        run_type_dropdown = ctk.CTkComboBox(
            run_type_frame,
            values=["Text to Video API"],
            variable=self.run_type_var
        )
        run_type_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        from tkinter import filedialog
        copy_youtube_btn = ctk.CTkButton(run_type_frame, text="Copy từ Youtube/Tiktok:", width=150, command=self._copy_from_url)
        copy_youtube_btn.pack(side="left", padx=2)
        
        project_link_label = ctk.CTkLabel(self.scrollable_frame, text="Project Link (Flow):")
        project_link_label.pack(pady=(10, 5))
        
        project_link_frame = ctk.CTkFrame(self.scrollable_frame)
        project_link_frame.pack(fill="x", pady=5)
        
        self.project_link_entry = ctk.CTkEntry(project_link_frame, placeholder_text="https://labs.google/fx/tools/flow/project/...")
        self.project_link_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        gemini_link_label = ctk.CTkLabel(self.scrollable_frame, text="Gemini Project Link:")
        gemini_link_label.pack(pady=(10, 5))
        
        gemini_link_frame = ctk.CTkFrame(self.scrollable_frame)
        gemini_link_frame.pack(fill="x", pady=5)
        
        self.gemini_project_link_entry = ctk.CTkEntry(gemini_link_frame, placeholder_text="https://gemini.google.com/app/...")
        self.gemini_project_link_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        upload_video_btn = ctk.CTkButton(self.scrollable_frame, text="Upload Video", command=self._upload_video)
        upload_video_btn.pack(fill="x", pady=5)
        
        script_frame = ctk.CTkFrame(self.scrollable_frame)
        script_frame.pack(fill="x", pady=(10, 5))
        
        script_label = ctk.CTkLabel(script_frame, text="Kịch bản / Ý tưởng:")
        script_label.pack(side="left", padx=5)
        
        analyze_btn = ctk.CTkButton(script_frame, text="Phân tích video", width=120, command=self._on_analyze_video)
        analyze_btn.pack(side="right", padx=5)
        
        generate_content_btn = ctk.CTkButton(script_frame, text="Tạo nội dung", width=120, command=self._on_generate_content, fg_color="green")
        generate_content_btn.pack(side="right", padx=5)
        
        self.script_textbox = ctk.CTkTextbox(self.scrollable_frame, height=150)
        self.script_textbox.pack(fill="x", pady=5)
        
        ai_model_frame = ctk.CTkFrame(self.scrollable_frame)
        ai_model_frame.pack(fill="x", pady=5)
        
        ai_model_label = ctk.CTkLabel(ai_model_frame, text="AI model viết prompt:")
        ai_model_label.pack(side="left", padx=5)
        
        self.ai_model_var = ctk.StringVar(value="VEO3 ULTRA")
        ai_model_dropdown = ctk.CTkComboBox(
            ai_model_frame,
            values=["VEO3", "VEO3 ULTRA", "VEO3.1", "VEO3.1 Fast"],
            variable=self.ai_model_var
        )
        ai_model_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        
        style_frame = ctk.CTkFrame(self.scrollable_frame)
        style_frame.pack(fill="x", pady=5)
        
        style_label = ctk.CTkLabel(style_frame, text="Phong cách:")
        style_label.pack(side="left", padx=5)
        
        self.style_var = ctk.StringVar(value="3d_Pixar")
        style_dropdown = ctk.CTkComboBox(
            style_frame,
            values=VIDEO_STYLES,
            variable=self.style_var
        )
        style_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        
        duration_label = ctk.CTkLabel(style_frame, text="Thời lượng:")
        duration_label.pack(side="left", padx=5)
        
        self.duration_entry = ctk.CTkEntry(style_frame, width=80)
        self.duration_entry.insert(0, "120")
        self.duration_entry.pack(side="left", padx=5)
        
        veo_frame = ctk.CTkFrame(self.scrollable_frame)
        veo_frame.pack(fill="x", pady=5)
        
        veo_label = ctk.CTkLabel(veo_frame, text="Veo Profile:")
        veo_label.pack(side="left", padx=5)
        
        self.veo_profile_var = ctk.StringVar(value="VEO3 ULTRA")
        veo_dropdown = ctk.CTkComboBox(
            veo_frame,
            values=VEO_PROFILES,
            variable=self.veo_profile_var
        )
        veo_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        
        aspect_ratio_frame = ctk.CTkFrame(self.scrollable_frame)
        aspect_ratio_frame.pack(fill="x", pady=5)
        
        aspect_ratio_label = ctk.CTkLabel(aspect_ratio_frame, text="Aspect Ratio:")
        aspect_ratio_label.pack(side="left", padx=5)
        
        self.aspect_ratio_var = ctk.StringVar(value="Khổ dọc (9:16)")
        aspect_ratio_dropdown = ctk.CTkComboBox(
            aspect_ratio_frame,
            values=ASPECT_RATIOS,
            variable=self.aspect_ratio_var
        )
        aspect_ratio_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        
        outputs_frame = ctk.CTkFrame(self.scrollable_frame)
        outputs_frame.pack(fill="x", pady=5)
        
        outputs_label = ctk.CTkLabel(outputs_frame, text="Số lượng video/prompt:")
        outputs_label.pack(side="left", padx=5)
        
        self.outputs_per_prompt_var = ctk.StringVar(value="1")
        outputs_dropdown = ctk.CTkComboBox(
            outputs_frame,
            values=["1", "2", "3", "4"],
            variable=self.outputs_per_prompt_var
        )
        outputs_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        
        button_frame = ctk.CTkFrame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=20)
        
        delete_btn = ctk.CTkButton(button_frame, text="Xóa", fg_color="red", command=self._delete_project)
        delete_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        save_btn = ctk.CTkButton(button_frame, text="Lưu", fg_color="green", command=self._save_project)
        save_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        all_btn = ctk.CTkButton(button_frame, text="🚀 Chạy tất cả", command=self._on_all_click, fg_color="blue", hover_color="darkblue")
        all_btn.grid(row=0, column=2, padx=5, sticky="ew")
        
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
    
    def _on_name_change(self, event=None):
        if self.on_project_change:
            self.on_project_change()
    
    def _on_file_select(self, value):
        if value:
            project = project_manager.load_project(value)
            if project:
                self.current_project = project
                self._load_project_data(project)
                if self.on_project_change:
                    self.on_project_change()
    
    def _load_project_data(self, project):
        self.project_name_entry.delete(0, "end")
        self.project_name_entry.insert(0, project.get("name", ""))
        self.script_textbox.delete("1.0", "end")
        self.script_textbox.insert("1.0", project.get("script", ""))
        self.style_var.set(project.get("style", "3d_Pixar"))
        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(project.get("duration", 120)))
        self.veo_profile_var.set(project.get("veo_profile", "VEO3 ULTRA"))
        self.ai_model_var.set(project.get("ai_model", "VEO3 ULTRA"))
        self.aspect_ratio_var.set(project.get("aspect_ratio", "Khổ dọc (9:16)"))
        self.outputs_per_prompt_var.set(str(project.get("outputs_per_prompt", 1)))
        self.project_link_entry.delete(0, "end")
        self.project_link_entry.insert(0, project.get("project_link", ""))
        self.gemini_project_link_entry.delete(0, "end")
        self.gemini_project_link_entry.insert(0, project.get("gemini_project_link", ""))
    
    def _new_project(self):
        name = self.project_name_entry.get() or "New Project"
        project = project_manager.create_project(name)
        self.project_file_var.set(project["file"])
        self._update_file_list()
        self._load_project_data(project)
    
    def _copy_project(self):
        from tkinter import messagebox
        
        current_file = self.project_file_var.get()
        if not current_file:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn project để copy")
            return
        
        if not self.current_project:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy project để copy")
            return
        
        original_name = self.current_project.get("name", "Project")
        new_name = f"{original_name}_Copy"
        
        new_file = project_manager.copy_project(current_file, new_name)
        if new_file:
            self._update_file_list()
            self.project_file_var.set(new_file)
            project = project_manager.load_project(new_file)
            if project:
                self.current_project = project
                self._load_project_data(project)
                if self.on_project_change:
                    self.on_project_change()
            messagebox.showinfo("Thành công", f"Đã copy project '{original_name}' thành '{new_name}'")
        else:
            messagebox.showerror("Lỗi", "Không thể copy project. Vui lòng thử lại.")
    
    def _save_project(self):
        from tkinter import messagebox
        
        if not self.current_project:
            self._new_project()
            return
        
        project_name = self.project_name_entry.get() or self.current_project.get("name", "Project")
        
        confirm = messagebox.askyesno(
            "Xác nhận lưu",
            f"Bạn có chắc chắn muốn lưu project '{project_name}'?",
            icon='question'
        )
        
        if not confirm:
            return
        
        project_data = {
            "name": self.project_name_entry.get(),
            "script": self.script_textbox.get("1.0", "end-1c"),
            "style": self.style_var.get(),
            "duration": int(self.duration_entry.get() or 120),
            "veo_profile": self.veo_profile_var.get(),
            "ai_model": self.ai_model_var.get(),
            "aspect_ratio": self.aspect_ratio_var.get(),
            "outputs_per_prompt": int(self.outputs_per_prompt_var.get() or 2),
            "project_link": self.project_link_entry.get(),
            "gemini_project_link": self.gemini_project_link_entry.get()
        }
        
        project_manager.update_project(self.current_project["file"], project_data)
        self.current_project.update(project_data)
        messagebox.showinfo("Thành công", f"Đã lưu project '{project_name}'")
    
    def _delete_project(self):
        current_file = self.project_file_var.get()
        if not current_file:
            return
        
        project = project_manager.load_project(current_file)
        if not project:
            return
        
        project_name = project.get('name', current_file)
        
        from tkinter import messagebox
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa project '{project_name}'?\n\n"
            "Hành động này sẽ xóa:\n"
            "- File project\n"
            "- Tất cả videos\n"
            "- Tất cả outputs\n"
            "- Tất cả prompts\n"
            "- Tất cả logs\n\n"
            "Hành động này không thể hoàn tác!",
            icon='warning'
        )
        
        if confirm:
            success = project_manager.delete_project(current_file)
            if success:
                self._update_file_list()
                self.project_file_var.set("")
                self.current_project = None
                self.project_name_entry.delete(0, "end")
                self.script_textbox.delete("1.0", "end")
                self.project_link_entry.delete(0, "end")
                self.gemini_project_link_entry.delete(0, "end")
                if self.on_project_change:
                    self.on_project_change()
                messagebox.showinfo("Thành công", f"Đã xóa project '{project_name}'")
            else:
                messagebox.showerror("Lỗi", "Không thể xóa project. Vui lòng thử lại.")
    
    def _update_file_list(self):
        files = project_manager.list_projects()
        self.project_file_dropdown.configure(values=files)
    
    def _on_all_click(self):
        if self.on_run_all:
            self.on_run_all()
    
    def _on_stop_click(self):
        if self.on_stop:
            self.on_stop()
    
    def _on_start_click(self):
        if self.on_start:
            self.on_start()
    
    def _copy_from_url(self):
        from tkinter import simpledialog
        url = simpledialog.askstring("URL Video", "Nhập URL video (YouTube/TikTok):")
        if url:
            if self.on_project_change:
                parent = self.master
                if hasattr(parent, 'upload_video_from_url'):
                    parent.upload_video_from_url(url)
    
    def _upload_video(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Chọn video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            if self.on_project_change:
                parent = self.master
                if hasattr(parent, 'upload_video'):
                    parent.upload_video(file_path)
    
    def _on_analyze_video(self):
        if self.on_analyze_video:
            self.on_analyze_video()
    
    def _on_generate_content(self):
        if self.on_generate_content:
            self.on_generate_content()
    
    def update_video_analysis(self, video_analysis: str):
        self.script_textbox.delete("1.0", "end")
        self.script_textbox.insert("1.0", video_analysis)
    
    def get_project_config(self):
        return {
            "name": self.project_name_entry.get(),
            "file": self.project_file_var.get(),
            "script": self.script_textbox.get("1.0", "end-1c"),
            "style": self.style_var.get(),
            "duration": int(self.duration_entry.get() or 120),
            "veo_profile": self.veo_profile_var.get(),
            "ai_model": self.ai_model_var.get(),
            "run_type": self.run_type_var.get(),
            "aspect_ratio": self.aspect_ratio_var.get(),
            "outputs_per_prompt": int(self.outputs_per_prompt_var.get() or 2),
            "project_link": self.project_link_entry.get(),
            "gemini_project_link": self.gemini_project_link_entry.get()
        }
    
    def set_workflow_running(self, is_running: bool):
        if is_running:
            self.stop_btn.configure(state="normal", text="⏹ Dừng Workflow", fg_color="red", hover_color="darkred")
            self.start_btn.configure(state="disabled", fg_color="gray")
        else:
            self.stop_btn.configure(state="disabled", text="⏹ Dừng Workflow", fg_color="gray", hover_color="gray")
            self.start_btn.configure(state="normal", fg_color="green", hover_color="darkgreen")

