from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from ..integrations.gemini_flow import GeminiIdolAnalyzer, default_gemini_config
from ..integrations.freepik_flow import generate_video_from_config
from ..core.models import KlingPromptData
from ..core.prompt_builder import build_kling_prompt
from ..data.project_manager import project_manager


Mode = Literal["prompt_only", "full"]


async def run_flow(
    idol_image: Path,
    dance_video: Path,
    mode: Mode,
    project_root: Path,
    project_name: Optional[str] = None,
) -> Dict[str, Any]:
    config = default_gemini_config(project_root)
    analyzer = GeminiIdolAnalyzer(config)

    kling_data: KlingPromptData = await analyzer.analyze(
        idol_image_path=idol_image,
        dance_video_path=dance_video,
    )

    result = build_kling_prompt(kling_data)

    outputs_dir = project_root / "data" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = outputs_dir / "kling_prompt.txt"
    prompt_file.write_text(result.prompt, encoding="utf-8")

    print("==== KLANG PROMPT ====")
    print(result.prompt)
    print()
    print(f"Lưu prompt tại: {prompt_file}")

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

    if existing_project:
        project_file = existing_project["file"]
        project_manager.update_project(
            project_file,
            {
                "kling_prompt": result.prompt,
                "kling_data": kling_data_dict,
                "status": "completed" if mode == "full" else "prompt_generated",
            },
        )
        print(f"📁 Đã cập nhật project: {project_file}")
    else:
        project = project_manager.create_project(
            name=name,
            idol_image=str(idol_image),
            dance_video=str(dance_video),
            mode=mode,
            kling_prompt=result.prompt,
            kling_data=kling_data_dict,
            status="completed" if mode == "full" else "prompt_generated",
        )
        print(f"📁 Đã tạo project: {project['file']}")

    if mode == "full":
        print("Đang gọi Freepik Video Generator với model Kling 2.6 Motion Control...")
        await generate_video_from_config(start_image=idol_image, video_file=dance_video)
        if existing_project:
            project_manager.update_project(existing_project["file"], {"status": "video_generated"})
        else:
            project_manager.update_project(project["file"], {"status": "video_generated"})

    return {
        "kling_prompt": result.prompt,
        "kling_data": kling_data_dict,
    }


def main() -> None:
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

    args = parser.parse_args()

    idol_image = Path(args.idol_image).expanduser().resolve()
    dance_video = Path(args.dance_video).expanduser().resolve()

    if not idol_image.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh idol: {idol_image}")
    if not dance_video.is_file():
        raise FileNotFoundError(f"Không tìm thấy video nhảy: {dance_video}")

    project_root = Path(__file__).resolve().parents[2]

    asyncio.run(
        run_flow(
            idol_image=idol_image,
            dance_video=dance_video,
            mode=args.mode,  # type: ignore[arg-type]
            project_root=project_root,
        )
    )


if __name__ == "__main__":
    main()

