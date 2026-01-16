import customtkinter as ctk
from typing import List, Dict, Any, Optional, Callable
from PIL import Image, ImageTk
import os
import webbrowser

class VideoList(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_retry: Optional[Callable[[int, str], None]] = None):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.videos = []
        self.on_retry = on_retry
    
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
        ctk.CTkLabel(header_frame, text="Prompt", width=300).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(header_frame, text="Actions", width=150).pack(side="left", padx=5)
        
        for i, video in enumerate(videos):
            video_frame = ctk.CTkFrame(self)
            video_frame.pack(fill="x", padx=5, pady=2)
            
            video_url = video.get("video_url")
            project_link = video.get("project_link", "")
            
            if video_url:
                thumbnail_btn = ctk.CTkButton(
                    video_frame, 
                    text="[Video]", 
                    width=200, 
                    height=100,
                    command=lambda url=video_url: self._open_video(url),
                    fg_color="blue"
                )
            else:
                thumbnail_btn = ctk.CTkLabel(video_frame, text="[No Video]", width=200, height=100)
            thumbnail_btn.pack(side="left", padx=5)
            
            num_label = ctk.CTkLabel(video_frame, text=str(i + 1), width=50)
            num_label.pack(side="left", padx=5)
            
            status = video.get("status", "PENDING")
            status_color = "green" if status == "SUCCESSFUL" else "red" if status == "FAILED" else "gray"
            status_label = ctk.CTkLabel(video_frame, text=status, width=100, fg_color=status_color)
            status_label.pack(side="left", padx=5)
            
            prompt_text = video.get("prompt", "")[:100] + "..." if len(video.get("prompt", "")) > 100 else video.get("prompt", "")
            prompt_btn = ctk.CTkButton(
                video_frame, 
                text=prompt_text, 
                width=300, 
                anchor="w",
                command=lambda idx=i, vid=video: self._show_detail(idx, vid),
                fg_color="transparent",
                hover_color=("gray70", "gray30")
            )
            prompt_btn.pack(side="left", padx=5, fill="x", expand=True)
            
            actions_frame = ctk.CTkFrame(video_frame)
            actions_frame.pack(side="left", padx=5)
            
            if project_link:
                view_btn = ctk.CTkButton(
                    actions_frame,
                    text="View",
                    width=60,
                    height=30,
                    command=lambda link=project_link: webbrowser.open(link),
                    fg_color="blue"
                )
                view_btn.pack(side="left", padx=2)
            
            if status == "FAILED" and self.on_retry:
                retry_btn = ctk.CTkButton(
                    actions_frame,
                    text="Retry",
                    width=60,
                    height=30,
                    command=lambda idx=i, prompt=video.get("prompt", ""): self.on_retry(idx, prompt),
                    fg_color="orange"
                )
                retry_btn.pack(side="left", padx=2)
    
    def _open_video(self, url: str):
        if url:
            webbrowser.open(url)
    
    def _show_detail(self, index: int, video: Dict[str, Any]):
        detail_window = ctk.CTk()
        detail_window.title(f"Video Detail - Scene {index + 1}")
        detail_window.geometry("800x600")
        
        scrollable = ctk.CTkScrollableFrame(detail_window)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        scene_id = video.get("scene_id", f"scene_{index + 1}")
        ctk.CTkLabel(scrollable, text=f"Scene ID: {scene_id}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5, anchor="w")
        
        status = video.get("status", "PENDING")
        status_color = "green" if status == "SUCCESSFUL" else "red" if status == "FAILED" else "gray"
        ctk.CTkLabel(scrollable, text=f"Status: {status}", fg_color=status_color, font=ctk.CTkFont(size=14)).pack(pady=5, anchor="w")
        
        prompt_label = ctk.CTkLabel(scrollable, text="Prompt:", font=ctk.CTkFont(size=14, weight="bold"))
        prompt_label.pack(pady=(10, 5), anchor="w")
        
        prompt_textbox = ctk.CTkTextbox(scrollable, height=200)
        prompt_textbox.pack(fill="x", pady=5)
        prompt_textbox.insert("1.0", video.get("prompt", ""))
        prompt_textbox.configure(state="disabled")
        
        video_url = video.get("video_url")
        if video_url:
            url_label = ctk.CTkLabel(scrollable, text="Video URL:", font=ctk.CTkFont(size=14, weight="bold"))
            url_label.pack(pady=(10, 5), anchor="w")
            
            url_textbox = ctk.CTkTextbox(scrollable, height=50)
            url_textbox.pack(fill="x", pady=5)
            url_textbox.insert("1.0", video_url)
            url_textbox.configure(state="disabled")
            
            open_btn = ctk.CTkButton(
                scrollable,
                text="Open Video",
                command=lambda: webbrowser.open(video_url),
                fg_color="blue"
            )
            open_btn.pack(pady=5, anchor="w")
        
        project_link = video.get("project_link")
        if project_link:
            project_label = ctk.CTkLabel(scrollable, text="Project Link:", font=ctk.CTkFont(size=14, weight="bold"))
            project_label.pack(pady=(10, 5), anchor="w")
            
            project_textbox = ctk.CTkTextbox(scrollable, height=50)
            project_textbox.pack(fill="x", pady=5)
            project_textbox.insert("1.0", project_link)
            project_textbox.configure(state="disabled")
            
            open_project_btn = ctk.CTkButton(
                scrollable,
                text="Open Project",
                command=lambda: webbrowser.open(project_link),
                fg_color="green"
            )
            open_project_btn.pack(pady=5, anchor="w")
        
        error = video.get("error")
        if error:
            error_label = ctk.CTkLabel(scrollable, text="Error:", font=ctk.CTkFont(size=14, weight="bold"), text_color="red")
            error_label.pack(pady=(10, 5), anchor="w")
            
            error_textbox = ctk.CTkTextbox(scrollable, height=100)
            error_textbox.pack(fill="x", pady=5)
            error_textbox.insert("1.0", error)
            error_textbox.configure(state="disabled")
        
        close_btn = ctk.CTkButton(scrollable, text="Close", command=detail_window.destroy)
        close_btn.pack(pady=20)

