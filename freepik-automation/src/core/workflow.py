from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

from ..config.constants import KOL_IMAGES_DIR
from ..data.project_manager import project_manager
from ..utils.video_utils import extract_first_frame

logger = logging.getLogger(__name__)

STEP_KOL_IMAGE = "kol_image"
STEP_GEMINI_ANALYZE = "gemini_analyze"
STEP_BUILD_PROMPT = "build_prompt"
STEP_SAVE_OUTPUTS = "save_outputs"
STEP_FREEPIK_VIDEO = "freepik_video"

DEFAULT_STEPS_ORDER: List[str] = [
    STEP_KOL_IMAGE,
    STEP_GEMINI_ANALYZE,
    STEP_BUILD_PROMPT,
    STEP_SAVE_OUTPUTS,
    STEP_FREEPIK_VIDEO,
]

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 3


def default_workflow_config(mode: str, generate_kol_image: bool) -> Dict[str, Any]:
    steps = [STEP_GEMINI_ANALYZE, STEP_BUILD_PROMPT, STEP_SAVE_OUTPUTS]
    if generate_kol_image:
        steps.insert(0, STEP_KOL_IMAGE)
    if mode == "full":
        steps.append(STEP_FREEPIK_VIDEO)
    return {
        "steps": steps,
        "retry": {"max_retries": DEFAULT_MAX_RETRIES, "delay_seconds": DEFAULT_RETRY_DELAY_SECONDS},
        "step_config": {
            s: {"enabled": True, "max_retries": DEFAULT_MAX_RETRIES}
            for s in DEFAULT_STEPS_ORDER
        },
    }


class FreepikWorkflow:
    def __init__(
        self,
        project_root: Path,
        project_config: Dict[str, Any],
    ):
        self.project_root = project_root
        self.config = project_config
        self.project_file: Optional[str] = project_config.get("file")
        self._wf_config = project_config.get("workflow_config") or default_workflow_config(
            project_config.get("mode", "prompt_only"),
            project_config.get("generate_kol_image", False),
        )
        self._steps_order: List[str] = self._wf_config.get("steps") or DEFAULT_STEPS_ORDER
        self._retry = self._wf_config.get("retry") or {}
        self._max_retries = self._retry.get("max_retries", DEFAULT_MAX_RETRIES)
        self._delay_seconds = self._retry.get("delay_seconds", DEFAULT_RETRY_DELAY_SECONDS)
        self._step_cfg = self._wf_config.get("step_config") or {}

    def _step_max_retries(self, step_id: str) -> int:
        return (
            self._step_cfg.get(step_id, {}).get("max_retries")
            or self._max_retries
        )

    def _step_enabled(self, step_id: str) -> bool:
        if step_id not in self._steps_order:
            return False
        return self._step_cfg.get(step_id, {}).get("enabled", True)

    def _get_workflow_step(self) -> str:
        if not self.project_file:
            return "start"
        proj = project_manager.load_project(self.project_file)
        return (proj or {}).get("workflow_step", "start")

    def _update_workflow_step(self, step_id: str) -> None:
        if not self.project_file:
            return
        project_manager.update_project(self.project_file, {"workflow_step": step_id})

    async def _retry_step(
        self,
        step_name: str,
        step_coro: Callable[[], Coroutine[Any, Any, Any]],
        max_retries: Optional[int] = None,
        delay_seconds: Optional[float] = None,
    ) -> Any:
        mx = max_retries if max_retries is not None else self._max_retries
        delay = delay_seconds if delay_seconds is not None else self._delay_seconds
        last_error: Optional[Exception] = None
        for attempt in range(1, mx + 1):
            try:
                return await step_coro()
            except Exception as e:
                last_error = e
                logger.warning(
                    "[%s] Lỗi lần %s/%s: %s",
                    step_name,
                    attempt,
                    mx,
                    str(e),
                )
                if attempt < mx:
                    logger.info("[%s] Retry sau %ss...", step_name, delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("[%s] Đã thử %s lần, thất bại", step_name, mx)
        raise last_error or RuntimeError(f"Step {step_name} failed")

    async def run(
        self,
        idol_image: Path,
        dance_video: Path,
        first_frame: Optional[Path] = None,
        start_image_override: Optional[Path] = None,
    ) -> Dict[str, Any]:
        name = self.config.get("project_name") or f"{idol_image.stem}_{dance_video.stem}"
        generate_kol = self.config.get("generate_kol_image", False)
        mode = self.config.get("mode", "prompt_only")

        kol_image_path: Optional[Path] = None
        start_image: Path = idol_image
        kling_data = None
        result_prompt = None
        kling_data_dict: Optional[Dict[str, Any]] = None

        existing_project = None
        if self.project_file:
            proj = project_manager.load_project(self.project_file)
            if proj:
                existing_project = proj
                saved_wf = proj.get("workflow_config")
                if saved_wf and isinstance(saved_wf, dict):
                    base = self._wf_config
                    self._wf_config = {**base, **saved_wf}
                    self._steps_order = self._wf_config.get("steps") or self._steps_order
                    self._retry = self._wf_config.get("retry") or self._retry
                    self._max_retries = self._retry.get("max_retries", self._max_retries)
                    self._delay_seconds = self._retry.get("delay_seconds", self._delay_seconds)
                    self._step_cfg = self._wf_config.get("step_config") or self._step_cfg
        if existing_project is None:
            for pf in project_manager.list_projects():
                proj = project_manager.load_project(pf)
                if proj and proj.get("name") == name:
                    existing_project = proj
                    if not self.project_file:
                        self.project_file = proj.get("file")
                    saved_wf = (proj or {}).get("workflow_config")
                    if saved_wf and isinstance(saved_wf, dict):
                        base = self._wf_config
                        self._wf_config = {**base, **saved_wf}
                        self._steps_order = self._wf_config.get("steps") or self._steps_order
                        self._retry = self._wf_config.get("retry") or self._retry
                        self._max_retries = self._retry.get("max_retries", self._max_retries)
                        self._delay_seconds = self._retry.get("delay_seconds", self._delay_seconds)
                        self._step_cfg = self._wf_config.get("step_config") or self._step_cfg
                    break

        if not existing_project:
            proj = project_manager.create_project(
                name=name,
                idol_image=str(idol_image),
                dance_video=str(dance_video),
                mode=mode,
                status="draft",
            )
            self.project_file = proj.get("file")
        else:
            saved_kol = (existing_project or {}).get("kol_image")
            if saved_kol:
                p = Path(saved_kol)
                if p.exists():
                    kol_image_path = p
                    start_image = p

        current = self._get_workflow_step()
        if current == "complete":
            logger.info("Workflow đã hoàn thành, trả về kết quả đã lưu")
            p = project_manager.load_project(self.project_file or "")
            return {
                "kling_prompt": (p or {}).get("kling_prompt", ""),
                "kling_data": (p or {}).get("kling_data"),
                "kol_image": (p or {}).get("kol_image"),
            }

        try:
            start_index = self._steps_order.index(current)
        except ValueError:
            start_index = 0

        if current in (STEP_BUILD_PROMPT, STEP_SAVE_OUTPUTS):
            try:
                start_index = self._steps_order.index(STEP_GEMINI_ANALYZE)
            except ValueError:
                pass

        if start_index > 0:
            proj = project_manager.load_project(self.project_file or "")
            if proj:
                saved_prompt = proj.get("kling_prompt")
                saved_data = proj.get("kling_data")
                if saved_prompt is not None:
                    result_prompt = saved_prompt
                if saved_data is not None:
                    kling_data_dict = saved_data

        for step_index, step_id in enumerate(self._steps_order):
            if step_index < start_index:
                continue
            if not self._step_enabled(step_id):
                continue
            if step_id == STEP_KOL_IMAGE:

                async def _do_kol() -> Path:
                    nonlocal first_frame
                    if first_frame is None:
                        first_frame = extract_first_frame(dance_video)
                    from ..integrations.gemini_image_flow import (
                        GeminiImageGenerator,
                        default_gemini_image_config,
                    )
                    KOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                    out = KOL_IMAGES_DIR / f"{idol_image.stem}_kol.jpg"
                    gen = GeminiImageGenerator(default_gemini_image_config(self.project_root))
                    return await gen.generate_kol_image(
                        idol_image_path=idol_image,
                        first_frame_path=first_frame,
                        output_path=out,
                    )

                kol_image_path = await self._retry_step(
                    STEP_KOL_IMAGE, _do_kol, max_retries=self._step_max_retries(STEP_KOL_IMAGE)
                )
                start_image = kol_image_path
                self._update_workflow_step(STEP_GEMINI_ANALYZE)

            elif step_id == STEP_GEMINI_ANALYZE:

                async def _do_analyze():
                    from ..integrations.gemini_flow import (
                        GeminiIdolAnalyzer,
                        default_gemini_config,
                    )
                    cfg = default_gemini_config(self.project_root)
                    analyzer = GeminiIdolAnalyzer(cfg)
                    return await analyzer.analyze(
                        idol_image_path=start_image,
                        dance_video_path=dance_video,
                    )

                kling_data = await self._retry_step(
                    "Gemini Analyze", _do_analyze, max_retries=self._step_max_retries(STEP_GEMINI_ANALYZE)
                )
                self._update_workflow_step(STEP_BUILD_PROMPT)

            elif step_id == STEP_BUILD_PROMPT:
                from ..core.prompt_builder import build_kling_prompt
                tpl = self.project_root / "prompts" / "KLING_VIDEO_PROMPT.txt"
                res = build_kling_prompt(kling_data, tpl)
                result_prompt = res.prompt
                kling_data_dict = asdict(kling_data)
                kling_data_dict["idol"] = asdict(kling_data.idol)
                kling_data_dict["dance"] = asdict(kling_data.dance)
                kling_data_dict["background"] = asdict(kling_data.background)
                kling_data_dict["color_mood"] = asdict(kling_data.color_mood)
                self._update_workflow_step(STEP_SAVE_OUTPUTS)

            elif step_id == STEP_SAVE_OUTPUTS:
                out_dir = self.project_root / "data" / "outputs"
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "kling_prompt.txt").write_text(result_prompt, encoding="utf-8")
                update = {
                    "kling_prompt": result_prompt,
                    "kling_data": kling_data_dict,
                    "status": "prompt_generated" if mode != "full" else "completed",
                    "workflow_config": self._wf_config,
                }
                if kol_image_path:
                    update["kol_image"] = str(kol_image_path)
                project_manager.update_project(self.project_file or "", update)
                self._update_workflow_step(STEP_FREEPIK_VIDEO if STEP_FREEPIK_VIDEO in self._steps_order else "complete")

            elif step_id == STEP_FREEPIK_VIDEO:
                from ..integrations.freepik_flow import generate_video_from_config
                video_start = start_image_override if start_image_override else start_image

                async def _do_freepik():
                    await generate_video_from_config(
                        start_image=video_start,
                        video_file=dance_video,
                        kling_prompt=result_prompt,
                    )

                await self._retry_step(
                    "Freepik Video", _do_freepik, max_retries=self._step_max_retries(STEP_FREEPIK_VIDEO)
                )
                project_manager.update_project(self.project_file or "", {"status": "video_generated"})
                self._update_workflow_step("complete")

        return {
            "kling_prompt": result_prompt or "",
            "kling_data": kling_data_dict,
            "kol_image": str(kol_image_path) if kol_image_path else None,
        }
