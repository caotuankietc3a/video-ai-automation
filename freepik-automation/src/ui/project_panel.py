from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ..data.project_manager import project_manager


class ProjectPanel(ctk.CTkFrame):
    NEW_PROJECT_VALUE = "-- Mới --"

    def __init__(
        self,
        parent,
        on_idol_image_select: Optional[Callable[[str | None], None]] = None,
        on_dance_video_select: Optional[Callable[[str | None], None]] = None,
        on_first_frame_select: Optional[Callable[[str | None], None]] = None,
        on_video_start_image_select: Optional[Callable[[str | None], None]] = None,
        on_project_loaded: Optional[Callable[[Optional[dict]], None]] = None,
        on_generate_video: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.on_idol_image_select = on_idol_image_select
        self.on_dance_video_select = on_dance_video_select
        self.on_first_frame_select = on_first_frame_select
        self.on_video_start_image_select = on_video_start_image_select
        self.on_project_loaded = on_project_loaded
        self.on_generate_video = on_generate_video

        self.idol_image_path: str | None = None
        self.dance_video_path: str | None = None
        self.first_frame_path: str | None = None
        self.video_start_image_path: str | None = None
        self.current_project_file: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        self.pack(side="left", fill="both", padx=10, pady=10)

        title_label = ctk.CTkLabel(
            self, text="Project & Input", font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))

        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=400)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)

        proj_frame = ctk.CTkFrame(self.scrollable_frame)
        proj_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(proj_frame, text="Project:").pack(side="left", padx=5)
        self.project_combo_var = ctk.StringVar(value=self.NEW_PROJECT_VALUE)
        self.project_combo = ctk.CTkComboBox(
            proj_frame,
            values=self._project_list(),
            variable=self.project_combo_var,
            command=self._on_project_select,
            width=200,
        )
        self.project_combo.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(proj_frame, text="Lưu", width=60, fg_color="green", command=self._save_project).pack(
            side="left", padx=2
        )

        name_frame = ctk.CTkFrame(self.scrollable_frame)
        name_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(name_frame, text="Tên project:").pack(side="left", padx=5)
        self.project_name_entry = ctk.CTkEntry(name_frame, placeholder_text="Để trống = tự đặt theo idol_video")
        self.project_name_entry.pack(side="left", padx=5, fill="x", expand=True)

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
        ctk.CTkButton(
            link_frame,
            text="Gắn link",
            width=100,
            command=self._open_link_popup,
        ).pack(side="left", padx=5)

        video_start_frame = ctk.CTkFrame(self.scrollable_frame)
        video_start_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(video_start_frame, text="Start image (cho tạo video):").pack(
            side="left", padx=5
        )
        self.video_start_image_label = ctk.CTkLabel(
            video_start_frame, text="Mặc định (idol/KOL)", fg_color="gray", corner_radius=5
        )
        self.video_start_image_label.pack(side="left", padx=5, fill="x", expand=True)
        video_start_btn = ctk.CTkButton(
            video_start_frame,
            text="Chọn",
            width=100,
            command=self._select_video_start_image,
        )
        video_start_btn.pack(side="left", padx=5)
        video_start_clear_btn = ctk.CTkButton(
            video_start_frame,
            text="Mặc định",
            width=80,
            fg_color="gray",
            command=self._clear_video_start_image,
        )
        video_start_clear_btn.pack(side="left", padx=5)

        button_frame = ctk.CTkFrame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=20)

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

    def _open_link_popup(self) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title("Gắn link TikTok/YouTube/FB")
        popup.geometry("420x140")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        f = ctk.CTkFrame(popup)
        f.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(f, text="Dán link video:").pack(anchor="w", padx=8, pady=(8, 2))
        entry = ctk.CTkEntry(f, placeholder_text="https://...", width=380)
        entry.pack(fill="x", padx=8, pady=(0, 8))
        entry.focus_set()

        def on_tải() -> None:
            url = (entry.get() or "").strip()
            if not url:
                messagebox.showwarning(
                    "Thiếu link",
                    "Vui lòng dán link TikTok / YouTube / Facebook vào ô trên.",
                    parent=popup,
                )
                return
            popup_btn = btn_tải
            self._download_and_extract_first_frame(
                url,
                after_success=popup.destroy,
                run_btn=popup_btn,
            )

        btn_frame = ctk.CTkFrame(f, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        btn_tải = ctk.CTkButton(btn_frame, text="Tải & cắt frame", width=120, command=on_tải)
        btn_tải.pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="Đóng", width=80, fg_color="gray", command=popup.destroy).pack(side="left")

    def _download_and_extract_first_frame(
        self,
        url: str,
        *,
        after_success: Optional[Callable[[], None]] = None,
        run_btn: Optional[ctk.CTkButton] = None,
    ) -> None:
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
                messagebox.showinfo("Xong", "Đã tải video và cắt frame đầu.")
                if after_success:
                    after_success()

            self.after(0, update_ui)

        import threading

        if run_btn and run_btn.winfo_exists():
            run_btn.configure(state="disabled", text="Đang tải...")

        def restore_btn() -> None:
            if run_btn and run_btn.winfo_exists():
                run_btn.configure(state="normal", text="Tải & cắt frame")

        def run() -> None:
            try:
                do_work()
            finally:
                self.after(0, restore_btn)
        threading.Thread(target=run, daemon=True).start()

    def _select_video_start_image(self):
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh dùng cho bước tạo video (từ máy)",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        )
        if file_path:
            self.video_start_image_path = file_path
            self.video_start_image_label.configure(
                text=file_path.split("/")[-1].split("\\")[-1], fg_color="green"
            )
        else:
            self.video_start_image_path = None
            self.video_start_image_label.configure(
                text="Mặc định (idol/KOL)", fg_color="gray"
            )
        if self.on_video_start_image_select:
            self.on_video_start_image_select(self.video_start_image_path)

    def _clear_video_start_image(self):
        self.video_start_image_path = None
        self.video_start_image_label.configure(
            text="Mặc định (idol/KOL)", fg_color="gray"
        )
        if self.on_video_start_image_select:
            self.on_video_start_image_select(None)

    def _on_generate_video(self):
        if self.on_generate_video:
            self.on_generate_video()

    def _project_list(self) -> list[str]:
        return [self.NEW_PROJECT_VALUE] + project_manager.list_projects()

    def _refresh_project_combo(self) -> None:
        self.project_combo.configure(values=self._project_list())

    def _on_project_select(self, value: str) -> None:
        if not value or value == self.NEW_PROJECT_VALUE:
            self.current_project_file = None
            self._clear_inputs_ui()
            if self.on_project_loaded:
                self.on_project_loaded(None)
            return
        proj = project_manager.load_project(value)
        if proj:
            self.current_project_file = value
            self._load_project_into_ui(proj)
            if self.on_project_loaded:
                self.on_project_loaded(proj)

    def _clear_inputs_ui(self) -> None:
        self.idol_image_path = None
        self.dance_video_path = None
        self.first_frame_path = None
        self.video_start_image_path = None
        self.idol_image_label.configure(text="Chưa chọn", fg_color="gray")
        self.dance_video_label.configure(text="Chưa chọn", fg_color="gray")
        self.first_frame_label.configure(text="Chưa chọn", fg_color="gray")
        self.video_start_image_label.configure(text="Mặc định (idol/KOL)", fg_color="gray")
        self.project_name_entry.delete(0, "end")
        if self.on_idol_image_select:
            self.on_idol_image_select(None)
        if self.on_dance_video_select:
            self.on_dance_video_select(None)
        if self.on_first_frame_select:
            self.on_first_frame_select(None)
        if self.on_video_start_image_select:
            self.on_video_start_image_select(None)

    def _load_project_into_ui(self, proj: dict) -> None:
        self.project_name_entry.delete(0, "end")
        self.project_name_entry.insert(0, proj.get("name", ""))

        idol = proj.get("idol_image") or ""
        dance = proj.get("dance_video") or ""
        first = proj.get("first_frame") or ""
        start_img = proj.get("start_image_override") or ""

        self.idol_image_path = idol if (idol and Path(idol).exists()) else None
        self.dance_video_path = dance if (dance and Path(dance).exists()) else None
        self.first_frame_path = first if (first and Path(first).exists()) else None
        self.video_start_image_path = start_img if (start_img and Path(start_img).exists()) else None

        self.idol_image_label.configure(
            text=Path(idol).name if self.idol_image_path else "Chưa chọn",
            fg_color="green" if self.idol_image_path else "gray",
        )
        self.dance_video_label.configure(
            text=Path(dance).name if self.dance_video_path else "Chưa chọn",
            fg_color="green" if self.dance_video_path else "gray",
        )
        self.first_frame_label.configure(
            text=Path(first).name if self.first_frame_path else "Chưa chọn",
            fg_color="green" if self.first_frame_path else "gray",
        )
        self.video_start_image_label.configure(
            text=Path(start_img).name if self.video_start_image_path else "Mặc định (idol/KOL)",
            fg_color="green" if self.video_start_image_path else "gray",
        )

        if self.on_idol_image_select:
            self.on_idol_image_select(self.idol_image_path)
        if self.on_dance_video_select:
            self.on_dance_video_select(self.dance_video_path)
        if self.on_first_frame_select:
            self.on_first_frame_select(self.first_frame_path)
        if self.on_video_start_image_select:
            self.on_video_start_image_select(self.video_start_image_path)

    def _save_project(self) -> None:
        idol = self.idol_image_path
        dance = self.dance_video_path
        name = (self.project_name_entry.get() or "").strip()
        if not idol or not dance:
            messagebox.showwarning(
                "Thiếu input",
                "Cần chọn Idol Image và Dance Video trước khi lưu project.",
            )
            return
        if not name:
            name = f"{Path(idol).stem}_{Path(dance).stem}"

        if self.current_project_file:
            project_manager.update_project(
                self.current_project_file,
                {
                    "name": name,
                    "idol_image": idol,
                    "dance_video": dance,
                    "first_frame": self.first_frame_path or "",
                    "start_image_override": self.video_start_image_path or "",
                },
            )
            messagebox.showinfo("Đã lưu", f"Đã cập nhật project '{name}'.")
        else:
            proj = project_manager.create_project(
                name=name,
                idol_image=idol,
                dance_video=dance,
                mode="prompt_only",
                status="draft",
            )
            self.current_project_file = proj.get("file")
            project_manager.update_project(
                self.current_project_file or "",
                {
                    "first_frame": self.first_frame_path or "",
                    "start_image_override": self.video_start_image_path or "",
                },
            )
            self._refresh_project_combo()
            self.project_combo_var.set(self.current_project_file or self.NEW_PROJECT_VALUE)
            if self.on_project_loaded:
                self.on_project_loaded(project_manager.load_project(self.current_project_file or ""))
            messagebox.showinfo("Đã lưu", f"Đã tạo project '{name}'.")
