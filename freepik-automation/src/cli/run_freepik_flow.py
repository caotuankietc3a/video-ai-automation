from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from ..integrations.gemini_flow import GeminiIdolAnalyzer, default_gemini_config
from ..integrations.gemini_image_flow import (
    GeminiImageGenerator,
    default_gemini_image_config,
)
from ..integrations.freepik_flow import generate_video_from_config
from ..core.models import KlingPromptData
from ..core.prompt_builder import build_kling_prompt
from ..core.nano_banana_prompt_builder import build_nano_banana_prompt
from ..data.project_manager import project_manager
from ..utils.video_utils import extract_first_frame
from ..config.constants import KOL_IMAGES_DIR

logger = logging.getLogger(__name__)

Mode = Literal["prompt_only", "full"]


async def run_flow(
    idol_image: Path,
    dance_video: Path,
    mode: Mode,
    project_root: Path,
    project_name: Optional[str] = None,
    generate_kol_image: bool = False,
    first_frame: Optional[Path] = None,
) -> Dict[str, Any]:
    logger.info("Step 0: Bắt đầu flow | idol=%s | video=%s | mode=%s", idol_image.name, dance_video.name, mode)

    kol_image_path: Optional[Path] = None
    start_image = idol_image

    if generate_kol_image:
        logger.info("Step 1a: Extract frame đầu từ video...")
        if first_frame is None:
            first_frame = extract_first_frame(dance_video)
            logger.info("Step 1a done: Đã extract frame đầu -> %s", first_frame)
        else:
            logger.info("Step 1a skip: Dùng first frame có sẵn -> %s", first_frame)

        logger.info("Step 1b: Tạo ảnh KOL bằng Gemini Image Generation...")
        image_config = default_gemini_image_config(project_root)
        image_generator = GeminiImageGenerator(image_config)

        KOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        kol_output_path = KOL_IMAGES_DIR / f"{idol_image.stem}_kol.jpg"

        kol_image_path = await image_generator.generate_kol_image(
            idol_image_path=idol_image,
            first_frame_path=first_frame,
            output_path=kol_output_path,
        )
        logger.info("Step 1b done: Đã tạo ảnh KOL -> %s", kol_image_path)
        start_image = kol_image_path
    else:
        logger.info("Step 1: Bỏ qua tạo KOL, dùng idol_image làm start_image")

    logger.info("Step 2: Phân tích idol + video qua Gemini...")
    config = default_gemini_config(project_root)
    analyzer = GeminiIdolAnalyzer(config)

    kling_data: KlingPromptData = await analyzer.analyze(
        idol_image_path=start_image,
        dance_video_path=dance_video,
    )
    logger.info("Step 2 done: Đã nhận JSON từ Gemini (idol, dance, background, color_mood)")

    logger.info("Step 3: Build Nano Banana prompt và Kling prompt...")
    nano_banana_prompt = build_nano_banana_prompt(
        idol_info=kling_data.idol,
        pose_style=kling_data.idol.pose_style,
        background_location=kling_data.background.location,
    )

    result = build_kling_prompt(kling_data)
    logger.info("Step 3 done: Đã build Nano Banana + Kling prompt")

    logger.info("Step 4: Ghi file prompts ra data/outputs...")
    outputs_dir = project_root / "data" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = outputs_dir / "kling_prompt.txt"
    prompt_file.write_text(result.prompt, encoding="utf-8")

    nano_banana_prompt_file = outputs_dir / "nano_banana_prompt.txt"
    nano_banana_prompt_file.write_text(nano_banana_prompt, encoding="utf-8")
    logger.info("Step 4 done: kling_prompt.txt | nano_banana_prompt.txt")

    print("==== NANO BANANA PROMPT ====")
    print(nano_banana_prompt)
    print()
    print(f"Lưu Nano Banana prompt tại: {nano_banana_prompt_file}")
    print()
    print("==== KLING PROMPT ====")
    print(result.prompt)
    print()
    print(f"Lưu Kling prompt tại: {prompt_file}")

    name = project_name or f"{idol_image.stem}_{dance_video.stem}"

    existing_project = None
    project_files = project_manager.list_projects()
    for pf in project_files:
        proj = project_manager.load_project(pf)
        if proj and proj.get("name") == name:
            existing_project = proj
            break

    kling_data_dict = asdict(kling_data)
    kling_data_dict["idol"] = asdict(kling_data.idol)
    kling_data_dict["dance"] = asdict(kling_data.dance)
    kling_data_dict["background"] = asdict(kling_data.background)
    kling_data_dict["color_mood"] = asdict(kling_data.color_mood)

    update_data = {
        "kling_prompt": result.prompt,
        "nano_banana_prompt": nano_banana_prompt,
        "kling_data": kling_data_dict,
        "status": "completed" if mode == "full" else "prompt_generated",
    }

    if kol_image_path:
        update_data["kol_image"] = str(kol_image_path)

    logger.info("Step 5: Lưu/cập nhật project...")
    if existing_project:
        project_file = existing_project["file"]
        project_manager.update_project(project_file, update_data)
        logger.info("Step 5 done: Đã cập nhật project -> %s", project_file)
        print(f"📁 Đã cập nhật project: {project_file}")
    else:
        project = project_manager.create_project(
            name=name,
            idol_image=str(idol_image),
            dance_video=str(dance_video),
            mode=mode,
            **update_data,
        )
        logger.info("Step 5 done: Đã tạo project -> %s", project["file"])
        print(f"📁 Đã tạo project: {project['file']}")

    if mode == "full":
        logger.info("Step 6: Gọi Freepik Video Generator (Kling 2.6 Motion Control)...")
        await generate_video_from_config(start_image=start_image, video_file=dance_video)
        if existing_project:
            project_manager.update_project(existing_project["file"], {"status": "video_generated"})
        else:
            project_manager.update_project(project["file"], {"status": "video_generated"})
        logger.info("Step 6 done: Freepik đã nhận lệnh Generate")
    else:
        logger.info("Step 6: Bỏ qua (mode=prompt_only)")

    logger.info("Flow hoàn tất.")
    return {
        "kling_prompt": result.prompt,
        "nano_banana_prompt": nano_banana_prompt,
        "kling_data": kling_data_dict,
        "kol_image": str(kol_image_path) if kol_image_path else None,
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Freepik Idol TikTok/Vinahouse → Gemini (browser) → Kling prompt"
    )
    parser.add_argument("--idol-image", required=True, help="Đường dẫn ảnh idol")
    parser.add_argument("--dance-video", required=True, help="Đường dẫn video nhảy")
    parser.add_argument(
        "--mode",
        choices=["prompt_only", "full"],
        default="prompt_only",
        help="prompt_only: chỉ tạo prompt; full: chuẩn bị cho gọi Kling",
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

    asyncio.run(
        run_flow(
            idol_image=idol_image,
            dance_video=dance_video,
            mode=args.mode,  # type: ignore[arg-type]
            project_root=project_root,
            generate_kol_image=args.generate_kol_image,
            first_frame=first_frame_path,
        )
    )


if __name__ == "__main__":
    main()

