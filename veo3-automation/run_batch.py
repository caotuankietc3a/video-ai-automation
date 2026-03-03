#!/usr/bin/env python3
import sys
import os
import json
import argparse
import logging
import multiprocessing

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
        description="Batch Video Runner - Chạy workflow VEO3 cho nhiều videos với multiprocessing",
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

Chế độ Multiprocessing:
  - Videos được chia đều cho các process
  - Mỗi process chạy browser riêng biệt
  - Tránh browser bị đơ do share state
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
        help="Số lượng process chạy song song (override config file)"
    )

    parser.add_argument(
        "--chrome-user-data-dir",
        type=str,
        default=None,
        help="Đường dẫn Chrome user data dir để chạy theo profile"
    )

    parser.add_argument(
        "--chrome-profile-directory",
        type=str,
        default=None,
        help="Tên profile directory (ví dụ: Default, Profile 1)"
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
    print("🎬 BATCH VIDEO RUNNER - VEO3 Automation (Multiprocessing)")
    print("=" * 60)
    
    config_data = load_config(args.config_file)
    
    if args.max_concurrent is not None:
        config_data["max_concurrent"] = args.max_concurrent

    if args.chrome_user_data_dir is not None:
        config_data.setdefault("chrome_profile", {})
        config_data["chrome_profile"]["enabled"] = True
        config_data["chrome_profile"]["user_data_dir"] = args.chrome_user_data_dir

    if args.chrome_profile_directory is not None:
        config_data.setdefault("chrome_profile", {})
        config_data["chrome_profile"]["enabled"] = True
        config_data["chrome_profile"]["profile_directory"] = args.chrome_profile_directory

    batch_config = BatchConfig.from_dict(config_data)
    
    num_processes = min(batch_config.max_concurrent, len(batch_config.videos))
    
    print(f"📁 Config file: {args.config_file}")
    print(f"🎥 Số videos: {len(batch_config.videos)}")
    print(f"🔧 Số processes: {num_processes}")
    print(f"📊 Videos/process: ~{len(batch_config.videos) // num_processes if num_processes > 0 else 0}")
    print(f"🎨 Default style: {batch_config.default_style}")
    print(f"⏱️  Default duration: {batch_config.default_duration}s")
    print(f"📐 Default aspect ratio: {batch_config.default_aspect_ratio}")
    if batch_config.chrome_profile_enabled:
        print(f"👤 Chrome profile: BẬT ({batch_config.chrome_user_data_dir})")
        if batch_config.chrome_profile_directory:
            print(f"📂 Chrome profile directory: {batch_config.chrome_profile_directory}")
    else:
        print("👤 Chrome profile: TẮT")
    print("=" * 60)

    if batch_config.chrome_profile_enabled and batch_config.max_concurrent > 1:
        print("⚠️ Đang bật Chrome profile, ép max_concurrent = 1 để tránh lock profile")
        batch_config.max_concurrent = 1
        num_processes = 1
    
    if len(batch_config.videos) == 0:
        print("⚠️ Không có video nào trong config!")
        sys.exit(1)
    
    runner = BatchRunner(batch_config, dry_run=args.dry_run)
    
    try:
        results = runner.run()
        
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
        import traceback
        print(f"\n❌ Lỗi không mong đợi: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    main()
