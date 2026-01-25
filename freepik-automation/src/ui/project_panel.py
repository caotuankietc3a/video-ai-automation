from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox


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
            text="Chọn file",
            width=80,
            command=self._select_first_frame,
        )
        first_frame_btn.pack(side="left", padx=5)

        link_frame = ctk.CTkFrame(self.scrollable_frame)
        link_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(link_frame, text="Link TikTok/YouTube/FB:").pack(
            side="left", padx=5
        )
        self.video_url_entry = ctk.CTkEntry(
            link_frame, placeholder_text="Dán link video rồi bấm Tải & cắt frame", width=200
        )
        self.video_url_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.url_first_frame_btn = ctk.CTkButton(
            link_frame,
            text="Tải & cắt frame",
            width=120,
            command=self._download_and_extract_first_frame,
        )
        self.url_first_frame_btn.pack(side="left", padx=5)

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

    def _download_and_extract_first_frame(self):
        url = (self.video_url_entry.get() or "").strip()
        if not url:
            messagebox.showwarning(
                "Thiếu link",
                "Vui lòng dán link TikTok / YouTube / Facebook vào ô phía trên rồi bấm \"Tải & cắt frame\".",
            )
            return

        def do_work() -> None:
            from ..utils.video_utils import (
                _validate_video_url,
                download_video_from_url,
                extract_first_frame,
            )

            err_msg: str | None = None
            frame_path: str | None = None
            video_path: str | None = None
            try:
                ok, _ = _validate_video_url(url)
                if not ok:
                    err_msg = "URL không hợp lệ. Chỉ hỗ trợ TikTok, YouTube, Facebook."
                    return
                video_path_obj = download_video_from_url(url)
                if not video_path_obj or not video_path_obj.exists():
                    err_msg = "Không tải được video từ link."
                    return
                video_path = str(video_path_obj)
                frame_path_obj = extract_first_frame(video_path_obj)
                frame_path = str(frame_path_obj)
            except Exception as e:
                err_msg = str(e)

            def update_ui() -> None:
                if err_msg:
                    messagebox.showerror("Lỗi", err_msg)
                    return
                if frame_path:
                    self.first_frame_path = frame_path
                    self.first_frame_label.configure(
                        text=frame_path.split("/")[-1].split("\\")[-1], fg_color="green"
                    )
                    if self.on_first_frame_select:
                        self.on_first_frame_select(frame_path)
                if video_path:
                    self.dance_video_path = video_path
                    self.dance_video_label.configure(
                        text=video_path.split("/")[-1].split("\\")[-1], fg_color="green"
                    )
                    if self.on_dance_video_select:
                        self.on_dance_video_select(video_path)
                self.video_url_entry.delete(0, "end")
                messagebox.showinfo("Xong", "Đã tải video và cắt frame đầu.")

            self.after(0, update_ui)

        import threading

        self.url_first_frame_btn.configure(state="disabled", text="Đang tải...")
        def restore_btn() -> None:
            self.url_first_frame_btn.configure(state="normal", text="Tải & cắt frame")
        def run() -> None:
            try:
                do_work()
            finally:
                self.after(0, restore_btn)
        threading.Thread(target=run, daemon=True).start()

    def _on_generate_kol(self):
        if self.on_generate_kol:
            self.on_generate_kol()

    def _on_generate_prompt(self):
        if self.on_generate_prompt:
            self.on_generate_prompt()

    def _on_generate_video(self):
        if self.on_generate_video:
            self.on_generate_video()
