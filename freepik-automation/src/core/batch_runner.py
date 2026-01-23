from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

from ..cli.run_freepik_flow import run_flow, Mode


@dataclass
class BatchItemConfig:
    idol_image: str
    dance_video: str
    mode: Mode = "prompt_only"
    name: Optional[str] = None


@dataclass
class BatchConfig:
    items: List[BatchItemConfig]
    max_concurrent: int = 1

    @classmethod
    def from_dict(cls, data: dict) -> "BatchConfig":
        raw_items = data.get("items", [])
        items: List[BatchItemConfig] = []
        for raw in raw_items:
            mode_value = raw.get("mode", "prompt_only")
            if mode_value not in ("prompt_only", "full"):
                mode_value = "prompt_only"
            item = BatchItemConfig(
                idol_image=raw.get("idol_image", ""),
                dance_video=raw.get("dance_video", ""),
                mode=mode_value,  # type: ignore[arg-type]
                name=raw.get("name"),
            )
            items.append(item)
        max_concurrent = int(data.get("max_concurrent", 1))
        return cls(items=items, max_concurrent=max_concurrent)


@dataclass
class BatchItemResult:
    idol_image: str
    dance_video: str
    mode: Mode
    success: bool
    error: Optional[str] = None


class FreepikBatchRunner:
    def __init__(self, config: BatchConfig, project_root: Path) -> None:
        self._config = config
        self._project_root = project_root

    def run(self) -> List[BatchItemResult]:
        results: List[BatchItemResult] = []
        for item in self._config.items:
            idol_path = Path(item.idol_image).expanduser().resolve()
            dance_path = Path(item.dance_video).expanduser().resolve()

            if not idol_path.is_file():
                results.append(
                    BatchItemResult(
                        idol_image=item.idol_image,
                        dance_video=item.dance_video,
                        mode=item.mode,
                        success=False,
                        error=f"Không tìm thấy idol_image: {idol_path}",
                    )
                )
                continue

            if not dance_path.is_file():
                results.append(
                    BatchItemResult(
                        idol_image=item.idol_image,
                        dance_video=item.dance_video,
                        mode=item.mode,
                        success=False,
                        error=f"Không tìm thấy dance_video: {dance_path}",
                    )
                )
                continue

            try:
                project_name = item.name or f"{idol_path.stem}_{dance_path.stem}"
                asyncio.run(
                    run_flow(
                        idol_image=idol_path,
                        dance_video=dance_path,
                        mode=item.mode,
                        project_root=self._project_root,
                        project_name=project_name,
                    )
                )
                results.append(
                    BatchItemResult(
                        idol_image=item.idol_image,
                        dance_video=item.dance_video,
                        mode=item.mode,
                        success=True,
                    )
                )
            except Exception as error:
                results.append(
                    BatchItemResult(
                        idol_image=item.idol_image,
                        dance_video=item.dance_video,
                        mode=item.mode,
                        success=False,
                        error=str(error),
                    )
                )

        return results

