import customtkinter as ctk
from .components.character_view import CharacterView
from .components.scene_view import SceneView
from .components.video_list import VideoList
from .components.log_view import LogView

class ResultPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self._setup_ui()
    
    def _setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)
        
        self.characters_tab = self.tabview.add("1. Nhân vật")
        self.scenes_tab = self.tabview.add("2. Phân cảnh")
        self.prompts_tab = self.tabview.add("3. Prompts")
        self.videos_tab = self.tabview.add("4. Video by VEO3")
        self.logs_tab = self.tabview.add("5. Nhật ký hoạt động")
        
        self.character_view = CharacterView(self.characters_tab)
        self.scene_view = SceneView(self.scenes_tab)
        self.prompts_view = ctk.CTkTextbox(self.prompts_tab)
        self.prompts_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        control_frame = ctk.CTkFrame(self.videos_tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
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
        
        self.video_list = VideoList(self.videos_tab)
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

