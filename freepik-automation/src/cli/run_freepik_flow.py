from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from ..core.workflow import (
    FreepikWorkflow,
    default_workflow_config,
)

logger = logging.getLogger(__name__)

Mode = Literal["prompt_only", "full"]


def build_project_config(
    idol_image: Path,
    dance_video: Path,
    mode: Mode,
    project_root: Path,
    project_name: Optional[str] = None,
    project_file: Optional[str] = None,
    generate_kol_image: bool = False,
    first_frame: Optional[Path] = None,
    start_image_override: Optional[Path] = None,
    workflow_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    name = project_name or f"{idol_image.stem}_{dance_video.stem}"
    wc = workflow_config or default_workflow_config(mode, generate_kol_image)
    out: Dict[str, Any] = {
        "project_name": name,
        "idol_image": str(idol_image),
        "dance_video": str(dance_video),
        "mode": mode,
        "generate_kol_image": generate_kol_image,
        "first_frame": str(first_frame) if first_frame else None,
        "start_image_override": str(start_image_override) if start_image_override else None,
        "workflow_config": wc,
        "project_root": project_root,
    }
    if project_file:
        out["file"] = project_file
    return out


async def run_flow(
    idol_image: Path,
    dance_video: Path,
    mode: Mode,
    project_root: Path,
    project_name: Optional[str] = None,
    project_file: Optional[str] = None,
    generate_kol_image: bool = False,
    first_frame: Optional[Path] = None,
    start_image_override: Optional[Path] = None,
    workflow_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    logger.info(
        "Bắt đầu flow | idol=%s | video=%s | mode=%s",
        idol_image.name,
        dance_video.name,
        mode,
    )
    project_config = build_project_config(
        idol_image=idol_image,
        dance_video=dance_video,
        mode=mode,
        project_root=project_root,
        project_name=project_name,
        project_file=project_file,
        generate_kol_image=generate_kol_image,
        first_frame=first_frame,
        start_image_override=start_image_override,
        workflow_config=workflow_config,
    )
    workflow = FreepikWorkflow(project_root=project_root, project_config=project_config)
    result = await workflow.run(
        idol_image=idol_image,
        dance_video=dance_video,
        first_frame=first_frame,
        start_image_override=start_image_override,
    )
    logger.info("Flow hoàn tất.")
    return result


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Freepik Idol TikTok → Gemini → Kling prompt → Freepik Video"
    )
    parser.add_argument("--idol-image", required=True, help="Đường dẫn ảnh idol")
    parser.add_argument("--dance-video", required=True, help="Đường dẫn video nhảy")
    parser.add_argument(
        "--mode",
        choices=["prompt_only", "full"],
        default="prompt_only",
        help="prompt_only: chỉ tạo prompt; full: tạo prompt + mở Freepik/Kling",
    )
    parser.add_argument(
        "--generate-kol-image",
        action="store_true",
        help="Tạo ảnh KOL từ idol image + frame đầu video",
    )
    parser.add_argument(
        "--first-frame",
        type=str,
        default=None,
        help="Đường dẫn frame đầu (nếu không cung cấp sẽ tự động extract từ video)",
    )
    parser.add_argument(
        "--start-image",
        type=str,
        default=None,
        help="Ảnh dùng cho bước tạo video (upload từ máy). Nếu không truyền thì dùng idol/KOL.",
    )

    args = parser.parse_args()

    idol_image = Path(args.idol_image).expanduser().resolve()
    dance_video = Path(args.dance_video).expanduser().resolve()

    if not idol_image.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh idol: {idol_image}")
    if not dance_video.is_file():
        raise FileNotFoundError(f"Không tìm thấy video nhảy: {dance_video}")

    project_root = Path(__file__).resolve().parents[2]

    first_frame_path = None
    if args.first_frame:
        first_frame_path = Path(args.first_frame).expanduser().resolve()
        if not first_frame_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy frame đầu: {first_frame_path}")

    start_image_override = None
    if args.start_image:
        start_image_override = Path(args.start_image).expanduser().resolve()
        if not start_image_override.is_file():
            raise FileNotFoundError(f"Không tìm thấy ảnh start: {start_image_override}")

    asyncio.run(
        run_flow(
            idol_image=idol_image,
            dance_video=dance_video,
            mode=args.mode,
            project_root=project_root,
            generate_kol_image=args.generate_kol_image,
            first_frame=first_frame_path,
            start_image_override=start_image_override,
        )
    )


if __name__ == "__main__":
    main()
