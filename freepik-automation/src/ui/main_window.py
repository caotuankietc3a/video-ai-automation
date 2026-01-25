from __future__ import annotations

import customtkinter as ctk
from .run_tab import RunTab
from .settings_tab import SettingsTab
from ..config.constants import APP_NAME


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("1400x900")

        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=5)

        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text=f"{APP_NAME}",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.header_label.pack(pady=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.run_tab = self.tabview.add("Vận hành")
        self.settings_tab = self.tabview.add("Cài đặt")

        self.run_tab_widget = RunTab(self.run_tab)
        self.settings_tab_widget = SettingsTab(self.settings_tab)
