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

