from __future__ import annotations

import customtkinter as ctk
from pathlib import Path
from PIL import Image


class ResultPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self._setup_ui()

    def _setup_ui(self):
        title_label = ctk.CTkLabel(
            self, text="Results", font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)

        self.kol_image_tab = self.tabview.add("KOL Image")
        self.prompt_tab = self.tabview.add("Kling Prompt")
        self.video_tab = self.tabview.add("Video Result")
        self.logs_tab = self.tabview.add("Logs")

        self._setup_kol_image_tab()
        self._setup_prompt_tab()
        self._setup_video_tab()
        self._setup_logs_tab()

    def _setup_kol_image_tab(self):
        scrollable = ctk.CTkScrollableFrame(self.kol_image_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.kol_image_label = ctk.CTkLabel(
            scrollable, text="Chưa có ảnh KOL", font=ctk.CTkFont(size=12)
        )
        self.kol_image_label.pack(pady=20)

        self.kol_image_path_label = ctk.CTkLabel(
            scrollable, text="", font=ctk.CTkFont(size=10)
        )
        self.kol_image_path_label.pack(pady=5)

    def _setup_prompt_tab(self):
        scrollable = ctk.CTkScrollableFrame(self.prompt_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.prompt_textbox = ctk.CTkTextbox(scrollable, height=400)
        self.prompt_textbox.pack(fill="both", expand=True, pady=5)

        button_frame = ctk.CTkFrame(scrollable)
        button_frame.pack(fill="x", pady=5)

        copy_btn = ctk.CTkButton(
            button_frame, text="Copy Prompt", command=self._copy_prompt
        )
        copy_btn.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(
            button_frame, text="Save to File", command=self._save_prompt
        )
        save_btn.pack(side="left", padx=5)

    def _setup_video_tab(self):
        scrollable = ctk.CTkScrollableFrame(self.video_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.video_label = ctk.CTkLabel(
            scrollable, text="Chưa có video", font=ctk.CTkFont(size=12)
        )
        self.video_label.pack(pady=20)

    def _setup_logs_tab(self):
        scrollable = ctk.CTkScrollableFrame(self.logs_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.logs_textbox = ctk.CTkTextbox(scrollable, height=400)
        self.logs_textbox.pack(fill="both", expand=True)
        self.logs_textbox.insert("1.0", "Activity logs will appear here...\n")

    def update_kol_image(self, image_path: str):
        try:
            path = Path(image_path)
            if not path.exists():
                self.kol_image_label.configure(
                    text=f"File không tồn tại: {image_path}", image=""
                )
                return
            img = Image.open(path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((400, 400))
            w, h = img.size
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))

            self.tabview.set("KOL Image")
            self.kol_image_label.configure(image=ctk_image, text="")
            self.kol_image_label.image = ctk_image
            self.kol_image_path_label.configure(text=f"Path: {image_path}")
        except Exception as e:
            self.kol_image_label.configure(
                text=f"Không thể load ảnh: {e}", image=""
            )

    def update_idol_image(self, image_path: str):
        pass

    def update_prompt(self, prompt: str):
        self.prompt_textbox.delete("1.0", "end")
        self.prompt_textbox.insert("1.0", prompt)

    def _copy_prompt(self):
        prompt_text = self.prompt_textbox.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(prompt_text)

    def _save_prompt(self):
        from tkinter import filedialog

        prompt_text = self.prompt_textbox.get("1.0", "end-1c")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file_path:
            Path(file_path).write_text(prompt_text, encoding="utf-8")

    def add_log(self, message: str) -> None:
        cur = self.logs_textbox.get("1.0", "end-1c")
        if cur.strip() == "Activity logs will appear here...":
            self.logs_textbox.delete("1.0", "end")
        self.logs_textbox.insert("end", f"{message}\n")
        self.logs_textbox.see("end")
