import customtkinter as ctk
import json
from typing import Dict, Any

class CharacterView(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.characters = {}
    
    def update_characters(self, characters: Dict[str, Any]):
        self.characters = characters
        
        for widget in self.winfo_children():
            widget.destroy()
        
        if not characters:
            label = ctk.CTkLabel(self, text="Chưa có nhân vật nào")
            label.pack(pady=20)
            return
        
        for char_id, char_data in characters.items():
            char_frame = ctk.CTkFrame(self)
            char_frame.pack(fill="x", padx=5, pady=5)
            
            name_label = ctk.CTkLabel(
                char_frame,
                text=f"{char_id}: {char_data.get('name', 'Unknown')}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            name_label.pack(anchor="w", padx=10, pady=5)
            
            info_text = f"Species: {char_data.get('species', 'Unknown')}\n"
            info_text += f"Gender: {char_data.get('gender', 'Unknown')}\n"
            info_text += f"Age: {char_data.get('age', 'Unknown')}"
            
            info_label = ctk.CTkLabel(char_frame, text=info_text, justify="left")
            info_label.pack(anchor="w", padx=20, pady=5)

