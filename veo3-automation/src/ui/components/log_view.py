import customtkinter as ctk
from typing import List, Dict, Any
from datetime import datetime

class LogView(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.logs = []
    
    def update_logs(self, logs: List[Dict[str, Any]]):
        self.logs = logs
        
        for widget in self.winfo_children():
            widget.destroy()
        
        if not logs:
            label = ctk.CTkLabel(self, text="Chưa có log nào")
            label.pack(pady=20)
            return
        
        for log in logs:
            log_frame = ctk.CTkFrame(self)
            log_frame.pack(fill="x", padx=5, pady=2)
            
            timestamp = log.get("timestamp", "")
            level = log.get("level", "INFO")
            message = log.get("message", "")
            
            level_color = {
                "INFO": "blue",
                "ERROR": "red",
                "WARNING": "orange"
            }.get(level, "gray")
            
            time_label = ctk.CTkLabel(log_frame, text=timestamp[:19], width=150)
            time_label.pack(side="left", padx=5)
            
            level_label = ctk.CTkLabel(log_frame, text=level, width=80, fg_color=level_color)
            level_label.pack(side="left", padx=5)
            
            msg_label = ctk.CTkLabel(log_frame, text=message, anchor="w", justify="left")
            msg_label.pack(side="left", padx=5, fill="x", expand=True)

