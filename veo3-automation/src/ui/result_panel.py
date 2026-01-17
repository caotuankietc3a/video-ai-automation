import customtkinter as ctk
from .components.character_view import CharacterView
from .components.scene_view import SceneView
from .components.video_list import VideoList
from .components.log_view import LogView

class ResultPanel(ctk.CTkFrame):
    def __init__(self, parent, on_run_step: callable = None, on_retry_video: callable = None):
        super().__init__(parent)
        self.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.on_run_step = on_run_step
        self.on_retry_video = on_retry_video
        self._setup_ui()
    
    def _setup_ui(self):
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", padx=10, pady=5)
        
        status_label = ctk.CTkLabel(self.status_frame, text="Project Links:", font=ctk.CTkFont(size=12, weight="bold"))
        status_label.pack(side="left", padx=5)
        
        self.gemini_link_label = ctk.CTkLabel(self.status_frame, text="Gemini: Chưa có", fg_color="gray", corner_radius=5)
        self.gemini_link_label.pack(side="left", padx=5)
        
        self.flow_link_label = ctk.CTkLabel(self.status_frame, text="Flow VEO3: Chưa có", fg_color="gray", corner_radius=5)
        self.flow_link_label.pack(side="left", padx=5)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)
        
        self.characters_tab = self.tabview.add("1. Nhân vật")
        self.scenes_tab = self.tabview.add("2. Phân cảnh")
        self.prompts_tab = self.tabview.add("3. Prompts")
        self.videos_tab = self.tabview.add("4. Video by VEO3")
        self.logs_tab = self.tabview.add("5. Nhật ký hoạt động")
        
        characters_control = ctk.CTkFrame(self.characters_tab)
        characters_control.pack(fill="x", padx=10, pady=5)
        if self.on_run_step:
            run_characters_btn = ctk.CTkButton(
                characters_control, 
                text="Chạy bước: Trích xuất nhân vật", 
                command=lambda: self.on_run_step("extract_characters"),
                fg_color="green"
            )
            run_characters_btn.pack(side="left", padx=5)
        
        self.character_view = CharacterView(self.characters_tab)
        
        scenes_control = ctk.CTkFrame(self.scenes_tab)
        scenes_control.pack(fill="x", padx=10, pady=5)
        if self.on_run_step:
            run_scenes_btn = ctk.CTkButton(
                scenes_control, 
                text="Chạy bước: Tạo phân cảnh", 
                command=lambda: self.on_run_step("generate_scenes"),
                fg_color="green"
            )
            run_scenes_btn.pack(side="left", padx=5)
        
        self.scene_view = SceneView(self.scenes_tab)
        
        prompts_control = ctk.CTkFrame(self.prompts_tab)
        prompts_control.pack(fill="x", padx=10, pady=5)
        if self.on_run_step:
            run_prompts_btn = ctk.CTkButton(
                prompts_control, 
                text="Chạy bước: Tạo prompts VEO3", 
                command=lambda: self.on_run_step("generate_prompts"),
                fg_color="green"
            )
            run_prompts_btn.pack(side="left", padx=5)
        
        self.prompts_view = ctk.CTkTextbox(self.prompts_tab)
        self.prompts_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        control_frame = ctk.CTkFrame(self.videos_tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        if self.on_run_step:
            run_videos_btn = ctk.CTkButton(
                control_frame, 
                text="Chạy bước: Tạo video VEO3", 
                command=lambda: self.on_run_step("generate_videos"),
                fg_color="green"
            )
            run_videos_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(control_frame, text="Refresh", width=100)
        refresh_btn.pack(side="left", padx=5)
        
        auto_update_label = ctk.CTkLabel(control_frame, text="Auto update (seconds):")
        auto_update_label.pack(side="left", padx=5)
        
        self.auto_update_entry = ctk.CTkEntry(control_frame, width=60)
        self.auto_update_entry.insert(0, "20")
        self.auto_update_entry.pack(side="left", padx=5)
        
        apply_btn = ctk.CTkButton(control_frame, text="Apply", width=80)
        apply_btn.pack(side="left", padx=5)
        
        merge_btn = ctk.CTkButton(control_frame, text="Merge video", width=100)
        merge_btn.pack(side="left", padx=5)
        
        open_btn = ctk.CTkButton(control_frame, text="Open the merged video", width=150)
        open_btn.pack(side="left", padx=5)
        
        self.video_list = VideoList(self.videos_tab, on_retry=self.on_retry_video)
        self.log_view = LogView(self.logs_tab)
    
    def update_characters(self, characters):
        self.character_view.update_characters(characters)
    
    def update_scenes(self, scenes):
        self.scene_view.update_scenes(scenes)
    
    def update_prompts(self, prompts):
        self.prompts_view.delete("1.0", "end")
        if prompts:
            self.prompts_view.insert("1.0", "\n\n".join(prompts))
    
    def update_videos(self, videos):
        self.video_list.update_videos(videos)
    
    def update_logs(self, logs):
        self.log_view.update_logs(logs)
    
    def clear_all(self):
        self.update_characters({})
        self.update_scenes([])
        self.update_prompts([])
        self.update_videos([])
        self.update_logs([])
        self.update_project_links("", "")
    
    def update_project_links(self, gemini_link: str = "", flow_link: str = ""):
        import webbrowser
        
        if gemini_link:
            project_id = gemini_link.split('/')[-1].split('?')[0]
            display_text = f"Gemini: {project_id[:15]}..." if len(project_id) > 15 else f"Gemini: {project_id}"
            self.gemini_link_label.configure(
                text=display_text,
                fg_color="green",
                cursor="hand2"
            )
            self.gemini_link_label.bind("<Button-1>", lambda e, link=gemini_link: webbrowser.open(link))
            self.gemini_link_label.bind("<Enter>", lambda e, link=gemini_link: self._show_tooltip(e, link))
            self.gemini_link_label.bind("<Leave>", lambda e: self._hide_tooltip())
        else:
            self.gemini_link_label.configure(
                text="Gemini: Chưa có",
                fg_color="gray",
                cursor=""
            )
            self.gemini_link_label.unbind("<Button-1>")
            self.gemini_link_label.unbind("<Enter>")
            self.gemini_link_label.unbind("<Leave>")
        
        if flow_link:
            project_id = flow_link.split('/')[-1].split('?')[0]
            display_text = f"Flow VEO3: {project_id[:15]}..." if len(project_id) > 15 else f"Flow VEO3: {project_id}"
            self.flow_link_label.configure(
                text=display_text,
                fg_color="blue",
                cursor="hand2"
            )
            self.flow_link_label.bind("<Button-1>", lambda e, link=flow_link: webbrowser.open(link))
            self.flow_link_label.bind("<Enter>", lambda e, link=flow_link: self._show_tooltip(e, link))
            self.flow_link_label.bind("<Leave>", lambda e: self._hide_tooltip())
        else:
            self.flow_link_label.configure(
                text="Flow VEO3: Chưa có",
                fg_color="gray",
                cursor=""
            )
            self.flow_link_label.unbind("<Button-1>")
            self.flow_link_label.unbind("<Enter>")
            self.flow_link_label.unbind("<Leave>")
    
    def _show_tooltip(self, event, link: str):
        if hasattr(self, '_tooltip'):
            self._tooltip.destroy()
        
        self._tooltip = ctk.CTkToplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = ctk.CTkLabel(
            self._tooltip,
            text=link,
            bg_color="gray20",
            fg_color="gray20",
            corner_radius=5,
            padx=10,
            pady=5
        )
        label.pack()
        self._tooltip.lift()
    
    def _hide_tooltip(self):
        if hasattr(self, '_tooltip'):
            self._tooltip.destroy()
            delattr(self, '_tooltip')

