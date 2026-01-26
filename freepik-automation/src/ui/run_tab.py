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

        self.project_panel = ProjectPanel(
            self,
            on_idol_image_select=self._on_idol_image_select,
            on_dance_video_select=self._on_dance_video_select,
            on_first_frame_select=self._on_first_frame_select,
            on_video_start_image_select=self._on_video_start_image_select,
            on_generate_kol=self._on_generate_kol,
            on_generate_video=self._on_generate_video,
        )
        self.result_panel = ResultPanel(self)
        _handler = _UILogHandler(self.result_panel)
        _handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(_handler)
        self._log_handler = _handler

    def _on_idol_image_select(self, file_path: str | None):
        if file_path:
            self.idol_image_path = Path(file_path)
            self.result_panel.update_idol_image(str(self.idol_image_path))

    def _on_dance_video_select(self, file_path: str | None):
        if file_path:
            self.dance_video_path = Path(file_path)

    def _on_first_frame_select(self, file_path: str | None):
        if file_path:
            self.first_frame_path = Path(file_path)

    def _on_video_start_image_select(self, file_path: str | None):
        self.video_start_image_path = Path(file_path) if file_path else None

    def _on_generate_kol(self):
        if not self.idol_image_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh idol trước")
            return

        if not self.dance_video_path and not self.first_frame_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn video nhảy hoặc frame đầu")
            return

        def run_async():
            try:
                self.result_panel.after(0, lambda: self.result_panel.add_log("Step: Bắt đầu tạo ảnh KOL..."))
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                kol_path = loop.run_until_complete(self._generate_kol_async())
                loop.close()
                if kol_path:
                    self.kol_image_path = Path(kol_path)
                    path_str = str(self.kol_image_path)
                    self.result_panel.after(
                        0,
                        lambda p=path_str: self.result_panel.update_kol_image(p),
                    )
                    self.result_panel.after(
                        0, lambda: self.result_panel.add_log("Step: Đã tạo ảnh KOL xong.")
                    )
                    self.result_panel.after(
                        0,
                        lambda p=kol_path: messagebox.showinfo("Thành công", f"Đã tạo ảnh KOL: {p}"),
                    )
            except Exception as e:
                err_msg = str(e)
                self.result_panel.after(0, lambda m=err_msg: self.result_panel.add_log(f"Lỗi: {m}"))
                self.result_panel.after(
                    0,
                    lambda m=err_msg: messagebox.showerror("Lỗi", f"Không thể tạo ảnh KOL: {m}"),
                )

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def _generate_kol_async(self) -> str | None:
        from ..integrations.gemini_image_flow import (
            GeminiImageGenerator,
            default_gemini_image_config,
        )
        from ..utils.video_utils import extract_first_frame
        from ..config.constants import KOL_IMAGES_DIR, BASE_DIR

        if not self.first_frame_path and self.dance_video_path:
            self.first_frame_path = extract_first_frame(self.dance_video_path)

        if not self.first_frame_path:
            raise ValueError("Không có frame đầu để tạo ảnh KOL")

        config = default_gemini_image_config(BASE_DIR)
        generator = GeminiImageGenerator(config)

        KOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        output_path = KOL_IMAGES_DIR / f"{self.idol_image_path.stem}_kol.jpg"

        kol_path = await generator.generate_kol_image(
            idol_image_path=self.idol_image_path,
            first_frame_path=self.first_frame_path,
            output_path=output_path,
        )

        return str(kol_path)

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
                kling_prompt = (result or {}).get("kling_prompt", "")
                self.result_panel.after(0, lambda p=kling_prompt: self.result_panel.update_prompt(p))
                self.result_panel.after(0, lambda: self.result_panel.add_log("Step: Đã chạy Generate video xong."))
                self.result_panel.after(0, lambda: messagebox.showinfo("Thành công", "Đã tạo video (Freepik/Kling)"))
            except Exception as e:
                err_msg = str(e)
                self.result_panel.after(0, lambda m=err_msg: self.result_panel.add_log(f"Lỗi: {m}"))
                self.result_panel.after(0, lambda m=err_msg: messagebox.showerror("Lỗi", f"Không thể tạo video: {m}"))

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def _generate_video_async(self) -> dict | None:
        from ..cli.run_freepik_flow import run_flow
        from ..config.constants import BASE_DIR

        start_image = self.kol_image_path or self.idol_image_path

        return await run_flow(
            idol_image=start_image,
            dance_video=self.dance_video_path,
            mode="full",
            project_root=BASE_DIR,
            generate_kol_image=False,
            first_frame=self.first_frame_path,
            start_image_override=self.video_start_image_path,
        )
