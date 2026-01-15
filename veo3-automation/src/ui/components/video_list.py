import customtkinter as ctk
from typing import List, Dict, Any
from PIL import Image, ImageTk
import os

class VideoList(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.videos = []
    
    def update_videos(self, videos: List[Dict[str, Any]]):
        self.videos = videos
        
        for widget in self.winfo_children():
            widget.destroy()
        
        if not videos:
            label = ctk.CTkLabel(self, text="Chưa có video nào")
            label.pack(pady=20)
            return
        
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Video", width=200).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="#", width=50).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Status", width=100).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Prompt", width=400).pack(side="left", padx=5, fill="x", expand=True)
        
        for i, video in enumerate(videos):
            video_frame = ctk.CTkFrame(self)
            video_frame.pack(fill="x", padx=5, pady=2)
            
            thumbnail_label = ctk.CTkLabel(video_frame, text="[Thumbnail]", width=200, height=100)
            thumbnail_label.pack(side="left", padx=5)
            
            num_label = ctk.CTkLabel(video_frame, text=str(i + 1), width=50)
            num_label.pack(side="left", padx=5)
            
            status = video.get("status", "PENDING")
            status_color = "green" if status == "SUCCESSFUL" else "red" if status == "FAILED" else "gray"
            status_label = ctk.CTkLabel(video_frame, text=status, width=100, fg_color=status_color)
            status_label.pack(side="left", padx=5)
            
            prompt_text = video.get("prompt", "")[:100] + "..." if len(video.get("prompt", "")) > 100 else video.get("prompt", "")
            prompt_label = ctk.CTkLabel(video_frame, text=prompt_text, width=400, anchor="w", justify="left")
            prompt_label.pack(side="left", padx=5, fill="x", expand=True)

