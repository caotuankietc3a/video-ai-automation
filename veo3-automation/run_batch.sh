#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

show_help() {
    echo "🎬 Batch Video Runner - VEO3 Automation"
    echo ""
    echo "Cách sử dụng:"
    echo "  ./run_batch.sh <config_file> [options]"
    echo ""
    echo "Options:"
    echo "  -m, --max-concurrent <n>   Số lượng video chạy song song"
    echo "  -d, --dry-run              Chỉ hiển thị thông tin, không thực hiện"
    echo "  -v, --verbose              Hiển thị log chi tiết"
    echo "  -h, --help                 Hiển thị trợ giúp này"
    echo ""
    echo "Ví dụ:"
    echo "  ./run_batch.sh data/batch_configs/sample_config.json"
    echo "  ./run_batch.sh config.json --max-concurrent 3"
    echo "  ./run_batch.sh config.json --dry-run"
    echo ""
}

if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

python run_batch.py "$@"
