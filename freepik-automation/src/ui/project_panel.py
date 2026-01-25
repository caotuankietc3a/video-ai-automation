from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk
from tkinter import filedialog


class ProjectPanel(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_idol_image_select: Optional[Callable[[str | None], None]] = None,
        on_dance_video_select: Optional[Callable[[str | None], None]] = None,
        on_first_frame_select: Optional[Callable[[str | None], None]] = None,
        on_generate_kol: Optional[Callable[[], None]] = None,
        on_generate_prompt: Optional[Callable[[], None]] = None,
        on_generate_video: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.on_idol_image_select = on_idol_image_select
        self.on_dance_video_select = on_dance_video_select
        self.on_first_frame_select = on_first_frame_select
        self.on_generate_kol = on_generate_kol
        self.on_generate_prompt = on_generate_prompt
        self.on_generate_video = on_generate_video

        self.idol_image_path: str | None = None
        self.dance_video_path: str | None = None
        self.first_frame_path: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        self.pack(side="left", fill="both", padx=10, pady=10)

        title_label = ctk.CTkLabel(
            self, text="Input Files", font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))

        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=400)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)

        idol_image_frame = ctk.CTkFrame(self.scrollable_frame)
        idol_image_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(idol_image_frame, text="Idol Image:").pack(side="left", padx=5)
        self.idol_image_label = ctk.CTkLabel(
            idol_image_frame, text="Chưa chọn", fg_color="gray", corner_radius=5
        )
        self.idol_image_label.pack(side="left", padx=5, fill="x", expand=True)

        idol_image_btn = ctk.CTkButton(
            idol_image_frame, text="Chọn", width=80, command=self._select_idol_image
        )
        idol_image_btn.pack(side="left", padx=5)

        dance_video_frame = ctk.CTkFrame(self.scrollable_frame)
        dance_video_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(dance_video_frame, text="Dance Video:").pack(side="left", padx=5)
        self.dance_video_label = ctk.CTkLabel(
            dance_video_frame, text="Chưa chọn", fg_color="gray", corner_radius=5
        )
        self.dance_video_label.pack(side="left", padx=5, fill="x", expand=True)

        dance_video_btn = ctk.CTkButton(
            dance_video_frame, text="Chọn", width=80, command=self._select_dance_video
        )
        dance_video_btn.pack(side="left", padx=5)

        self.generate_kol_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="Generate KOL Image"
        )
        self.generate_kol_checkbox.pack(pady=10)

        first_frame_frame = ctk.CTkFrame(self.scrollable_frame)
        first_frame_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(first_frame_frame, text="First Frame (optional):").pack(
            side="left", padx=5
        )
        self.first_frame_label = ctk.CTkLabel(
            first_frame_frame, text="Chưa chọn", fg_color="gray", corner_radius=5
        )
        self.first_frame_label.pack(side="left", padx=5, fill="x", expand=True)

        first_frame_btn = ctk.CTkButton(
            first_frame_frame,
            text="Chọn",
            width=80,
            command=self._select_first_frame,
        )
        first_frame_btn.pack(side="left", padx=5)

        button_frame = ctk.CTkFrame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=20)

        generate_kol_btn = ctk.CTkButton(
            button_frame,
            text="Generate KOL Image",
            command=self._on_generate_kol,
            fg_color="blue",
        )
        generate_kol_btn.pack(fill="x", pady=5)

        generate_prompt_btn = ctk.CTkButton(
            button_frame,
            text="Generate Nano Banana Prompt",
            command=self._on_generate_prompt,
            fg_color="green",
        )
        generate_prompt_btn.pack(fill="x", pady=5)

        generate_video_btn = ctk.CTkButton(
            button_frame,
            text="Generate Video",
            command=self._on_generate_video,
            fg_color="purple",
        )
        generate_video_btn.pack(fill="x", pady=5)

    def _select_idol_image(self):
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh idol",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        )
        if file_path:
            self.idol_image_path = file_path
            self.idol_image_label.configure(
                text=file_path.split("/")[-1], fg_color="green"
            )
            if self.on_idol_image_select:
                self.on_idol_image_select(file_path)

    def _select_dance_video(self):
        file_path = filedialog.askopenfilename(
            title="Chọn video nhảy",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.dance_video_path = file_path
            self.dance_video_label.configure(
                text=file_path.split("/")[-1], fg_color="green"
            )
            if self.on_dance_video_select:
                self.on_dance_video_select(file_path)

    def _select_first_frame(self):
        file_path = filedialog.askopenfilename(
            title="Chọn frame đầu",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        )
        if file_path:
            self.first_frame_path = file_path
            self.first_frame_label.configure(
                text=file_path.split("/")[-1], fg_color="green"
            )
            if self.on_first_frame_select:
                self.on_first_frame_select(file_path)

    def _on_generate_kol(self):
        if self.on_generate_kol:
            self.on_generate_kol()

    def _on_generate_prompt(self):
        if self.on_generate_prompt:
            self.on_generate_prompt()

    def _on_generate_video(self):
        if self.on_generate_video:
            self.on_generate_video()
