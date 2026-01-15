import customtkinter as ctk
import json
from typing import List, Dict, Any

class SceneView(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.scenes = []
    
    def update_scenes(self, scenes: List[Dict[str, Any]]):
        self.scenes = scenes
        
        for widget in self.winfo_children():
            widget.destroy()
        
        if not scenes:
            label = ctk.CTkLabel(self, text="Chưa có phân cảnh nào")
            label.pack(pady=20)
            return
        
        for scene in scenes:
            scene_frame = ctk.CTkFrame(self)
            scene_frame.pack(fill="x", padx=5, pady=5)
            
            scene_id = scene.get('scene_id', 'Unknown')
            title_label = ctk.CTkLabel(
                scene_frame,
                text=f"Phân cảnh: {scene_id}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            title_label.pack(anchor="w", padx=10, pady=5)
            
            visual_style = scene.get('visual_style', 'Unknown')
            style_label = ctk.CTkLabel(
                scene_frame,
                text=f"Visual Style: {visual_style}",
                justify="left"
            )
            style_label.pack(anchor="w", padx=20, pady=2)
            
            duration = scene.get('duration_sec', 8)
            duration_label = ctk.CTkLabel(
                scene_frame,
                text=f"Duration: {duration} seconds",
                justify="left"
            )
            duration_label.pack(anchor="w", padx=20, pady=2)

