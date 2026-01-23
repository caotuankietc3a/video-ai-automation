#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.batch_runner import BatchConfig, FreepikBatchRunner  # noqa: E402


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"❌ Lỗi: Không tìm thấy file config: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        print(f"❌ Lỗi: File JSON không hợp lệ: {error}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Freepik Batch Runner - Chạy flow Idol TikTok/Vinahouse → Gemini → Kling/Freepik cho nhiều cặp idol_image + dance_video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python run_batch.py data/batch_configs/sample_config.json

Cấu trúc file JSON config:
{
  "max_concurrent": 1,
  "items": [
    {
      "name": "Idol_1",
      "idol_image": "/full/path/to/idol1.png",
      "dance_video": "/full/path/to/dance1.mp4",
      "mode": "prompt_only"
    },
    {
      "name": "Idol_2",
      "idol_image": "/full/path/to/idol2.png",
      "dance_video": "/full/path/to/dance2.mp4",
      "mode": "full"
    }
  ]
}

mode:
  - "prompt_only": chỉ chạy Gemini + sinh prompt Kling.
  - "full": Gemini + prompt Kling + mở Freepik Video Generator (model Kling) để tạo video.
        """,
    )

    parser.add_argument(
        "config_file",
        help="Đường dẫn đến file JSON config",
    )

    args = parser.parse_args()

    config_data = load_config(args.config_file)
    batch_config = BatchConfig.from_dict(config_data)

    if not batch_config.items:
        print("⚠️ Không có item nào trong config!")
        sys.exit(1)

    project_root = Path(__file__).resolve().parent

    print("=" * 60)
    print("🎬 FREEPIK BATCH RUNNER")
    print("=" * 60)
    print(f"📁 Config file: {args.config_file}")
    print(f"🎥 Số items: {len(batch_config.items)}")
    print("=" * 60)

    runner = FreepikBatchRunner(config=batch_config, project_root=project_root)
    results = runner.run()

    success_count = sum(1 for result in results if result.success)
    print("\n" + "=" * 60)
    print("📊 BATCH SUMMARY")
    print("=" * 60)
    print(f"✅ Thành công: {success_count}/{len(results)}")
    if success_count < len(results):
        print("❌ Thất bại:")
        for result in results:
            if not result.success:
                print(f"  - {result.idol_image} / {result.dance_video}: {result.error}")

    if success_count == len(results):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()

