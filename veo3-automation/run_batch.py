#!/usr/bin/env python3
import sys
import os
import json
import argparse
import asyncio
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.batch_runner import BatchRunner, BatchConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"❌ Lỗi: Không tìm thấy file config: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi: File JSON không hợp lệ: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Batch Video Runner - Chạy workflow VEO3 cho nhiều videos cùng lúc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python run_batch.py data/batch_configs/my_config.json
  python run_batch.py config.json --max-concurrent 3
  python run_batch.py config.json --dry-run

Cấu trúc file JSON config:
{
  "default_config": {
    "duration": 120,
    "style": "3d_Pixar",
    "aspect_ratio": "Khổ dọc (9:16)",
    "veo_profile": "VEO3 ULTRA",
    "outputs_per_prompt": 1
  },
  "max_concurrent": 2,
  "videos": [
    {
      "url": "https://youtube.com/watch?v=xxx",
      "name": "Video_1"
    },
    {
      "url": "https://tiktok.com/@user/video/xxx",
      "name": "Video_2",
      "duration": 60,
      "style": "anime_2d"
    }
  ]
}
        """
    )
    
    parser.add_argument(
        "config_file",
        help="Đường dẫn đến file JSON config"
    )
    
    parser.add_argument(
        "--max-concurrent", "-m",
        type=int,
        default=None,
        help="Số lượng video chạy song song (override config file)"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Chỉ hiển thị thông tin, không thực hiện"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Hiển thị log chi tiết"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 60)
    print("🎬 BATCH VIDEO RUNNER - VEO3 Automation")
    print("=" * 60)
    
    config_data = load_config(args.config_file)
    
    if args.max_concurrent is not None:
        config_data["max_concurrent"] = args.max_concurrent
    
    batch_config = BatchConfig.from_dict(config_data)
    
    print(f"📁 Config file: {args.config_file}")
    print(f"🎥 Số videos: {len(batch_config.videos)}")
    print(f"⚡ Max concurrent: {batch_config.max_concurrent}")
    print(f"🎨 Default style: {batch_config.default_style}")
    print(f"⏱️  Default duration: {batch_config.default_duration}s")
    print(f"📐 Default aspect ratio: {batch_config.default_aspect_ratio}")
    print("=" * 60)
    
    if len(batch_config.videos) == 0:
        print("⚠️ Không có video nào trong config!")
        sys.exit(1)
    
    runner = BatchRunner(batch_config, dry_run=args.dry_run)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(runner.run())
        
        if not args.dry_run:
            success_count = sum(1 for r in results if r.success)
            if success_count == len(results):
                print("\n✅ Tất cả videos đã hoàn thành thành công!")
                sys.exit(0)
            else:
                print(f"\n⚠️ {len(results) - success_count} videos thất bại")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Đã dừng bởi người dùng")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Lỗi không mong đợi: {e}")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
