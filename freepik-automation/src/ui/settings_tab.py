from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from ..config.config_manager import config_manager
from ..config.constants import CONFIG_FILE


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        title_label = ctk.CTkLabel(
            self, text="Settings", font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)

        freepik_frame = ctk.CTkFrame(self.scrollable_frame)
        freepik_frame.pack(fill="x", pady=10)

        freepik_title = ctk.CTkLabel(
            freepik_frame,
            text="Freepik Account",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        freepik_title.pack(pady=5)

        email_label = ctk.CTkLabel(freepik_frame, text="Email:")
        email_label.pack(pady=5)
        self.email_entry = ctk.CTkEntry(freepik_frame, width=300)
        self.email_entry.pack(pady=5)

        password_label = ctk.CTkLabel(freepik_frame, text="Password:")
        password_label.pack(pady=5)
        self.password_entry = ctk.CTkEntry(freepik_frame, width=300, show="*")
        self.password_entry.pack(pady=5)

        gemini_frame = ctk.CTkFrame(self.scrollable_frame)
        gemini_frame.pack(fill="x", pady=10)

        gemini_title = ctk.CTkLabel(
            gemini_frame,
            text="Gemini Account (dùng cho Generate KOL Image)",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        gemini_title.pack(pady=5)

        ctk.CTkLabel(gemini_frame, text="Email:").pack(pady=5)
        self.gemini_email_entry = ctk.CTkEntry(gemini_frame, width=300)
        self.gemini_email_entry.pack(pady=5)

        ctk.CTkLabel(gemini_frame, text="Password:").pack(pady=5)
        self.gemini_password_entry = ctk.CTkEntry(gemini_frame, width=300, show="*")
        self.gemini_password_entry.pack(pady=5)

        save_btn = ctk.CTkButton(
            self.scrollable_frame, text="Save Settings", command=self._save_settings
        )
        save_btn.pack(pady=10)

    def _load_settings(self):
        self.email_entry.delete(0, "end")
        self.email_entry.insert(0, config_manager.get("freepik_account.email", ""))

        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, config_manager.get("freepik_account.password", ""))

        self.gemini_email_entry.delete(0, "end")
        self.gemini_email_entry.insert(0, config_manager.get("gemini_account.email", ""))

        self.gemini_password_entry.delete(0, "end")
        self.gemini_password_entry.insert(0, config_manager.get("gemini_account.password", ""))

    def _save_settings(self):
        config_manager.set("freepik_account.email", self.email_entry.get())
        config_manager.set("freepik_account.password", self.password_entry.get())
        config_manager.set("gemini_account.email", self.gemini_email_entry.get())
        config_manager.set("gemini_account.password", self.gemini_password_entry.get())
        config_manager.save()
        messagebox.showinfo("Thành công", "Đã lưu cài đặt")
