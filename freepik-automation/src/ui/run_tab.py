from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .project_panel import ProjectPanel
from .result_panel import ResultPanel


class _UILogHandler(logging.Handler):
    def __init__(self, result_panel: ResultPanel):
        super().__init__()
        self._panel = result_panel
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._panel.after(0, lambda m=msg: self._panel.add_log(m))
        except Exception:
            pass


class RunTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        self.idol_image_path: Path | None = None
        self.dance_video_path: Path | None = None
        self.kol_image_path: Path | None = None
        self.first_frame_path: Path | None = None
        self.video_start_image_path: Path | None = None
        self.current_project_file: str | None = None
        self.current_project_name: str | None = None

        self.project_panel = ProjectPanel(
            self,
            on_idol_image_select=self._on_idol_image_select,
            on_dance_video_select=self._on_dance_video_select,
            on_first_frame_select=self._on_first_frame_select,
            on_video_start_image_select=self._on_video_start_image_select,
            on_project_loaded=self._on_project_loaded,
            on_generate_video=self._on_generate_video,
        )
        self.result_panel = ResultPanel(self)
        _handler = _UILogHandler(self.result_panel)
        _handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(_handler)
        self._log_handler = _handler

    def _on_idol_image_select(self, file_path: str | None):
        self.idol_image_path = Path(file_path) if file_path else None
        if self.idol_image_path:
            self.result_panel.update_idol_image(str(self.idol_image_path))

    def _on_dance_video_select(self, file_path: str | None):
        self.dance_video_path = Path(file_path) if file_path else None

    def _on_first_frame_select(self, file_path: str | None):
        self.first_frame_path = Path(file_path) if file_path else None

    def _on_video_start_image_select(self, file_path: str | None):
        self.video_start_image_path = Path(file_path) if file_path else None

    def _on_project_loaded(self, project: dict | None):
        if project is None:
            self.current_project_file = None
            self.current_project_name = None
            return
        self.current_project_file = project.get("file")
        self.current_project_name = project.get("name")

    def _on_generate_video(self):
        if not self.idol_image_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh idol trước")
            return

        if not self.dance_video_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn video nhảy trước")
            return

        def run_async():
            result: dict | None = None
            try:
                self.result_panel.after(0, lambda: self.result_panel.add_log("Step: Bắt đầu tạo video (Freepik/Kling)..."))
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._generate_video_async())
                loop.close()
                r = result

                def on_success() -> None:
                    if r:
                        kling_prompt = r.get("kling_prompt", "")
                        if kling_prompt:
                            self.result_panel.update_prompt(kling_prompt)
                        kol_img = r.get("kol_image")
                        if kol_img:
                            self.kol_image_path = Path(kol_img)
                            self.result_panel.update_kol_image(kol_img)
                    self.result_panel.add_log("Step: Đã chạy Generate video xong.")
                    messagebox.showinfo("Thành công", "Đã tạo video (Freepik/Kling)")

                self.after(0, on_success)
            except Exception as e:
                err_msg = str(e)
                self.result_panel.after(0, lambda m=err_msg: self.result_panel.add_log(f"Lỗi: {m}"))
                self.result_panel.after(0, lambda m=err_msg: messagebox.showerror("Lỗi", f"Không thể tạo video: {m}"))

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def _generate_video_async(self) -> dict | None:
        from ..cli.run_freepik_flow import run_flow
        from ..config.constants import BASE_DIR

        generate_kol = self.kol_image_path is None
        return await run_flow(
            idol_image=self.idol_image_path,
            dance_video=self.dance_video_path,
            mode="full",
            project_root=BASE_DIR,
            project_name=self.current_project_name,
            project_file=self.current_project_file,
            generate_kol_image=generate_kol,
            first_frame=self.first_frame_path,
            start_image_override=self.video_start_image_path,
        )
