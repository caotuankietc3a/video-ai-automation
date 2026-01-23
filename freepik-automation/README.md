## Freepik Automation (Idol TikTok/Vinahouse → Kling)

### Mục tiêu
- Xây flow riêng (tách biệt với `veo3-automation`) cho bài toán:
  - Ảnh idol (có background rõ ràng).
  - Video nhảy TikTok/Vinahouse.
  - Tự động phân tích qua Gemini web (browser automation, không dùng API).
  - Sinh prompt tối ưu cho Kling (với bối cảnh/khung cảnh + tông màu + không khí).
  - Tự động mở Freepik Video Generator + chọn model Kling + upload start image/video + bấm Generate.

### Cấu trúc thư mục
- `src/`
  - `core/`: model dữ liệu, logic build prompt Kling.
  - `integrations/`:
    - `gemini_flow.py`: điều khiển Gemini trên browser để phân tích idol + video và trả về JSON structured.
    - `freepik_flow.py`: login Freepik + mở Video Generator + chọn model Kling + upload file + Generate.
  - `cli/`: entry scripts để chạy flow từ dòng lệnh.
- `prompts/`: các file prompt text dùng cho Gemini/Kling.
- `data/`
  - `inputs/`: ảnh idol + video nhảy đầu vào (nếu muốn quản lý theo folder).
  - `outputs/`: JSON phân tích + prompt Kling + log kết quả.
- `tests/`: test cho `core` và parser.

---

### 1. Cài đặt dependency

Trong thư mục `freepik-automation/`:

```bash
pip install -r requirements.txt

# nếu chưa cài Playwright browsers
python -m playwright install
```

Yêu cầu: Python 3.10+ (nên dùng cùng version với `veo3-automation`).

---

### 2. Cấu hình tài khoản Freepik

File cấu hình nằm tại:

- `data/config.json` (tự động tạo lần đầu chạy).

Bạn cần chỉnh sửa các field:

```json
{
  "freepik_account": {
    "email": "your_email@example.com",
    "password": "your_password"
  },
  "browser_automation": {
    "headless": false,
    "timeout": 30000,
    "channel": "chrome"
  }
}
```

> Lưu ý: file này KHÔNG nên commit lên git nếu chứa credential thật.

---

### 3. Chạy flow phân tích Gemini → sinh prompt Kling

CLI: `src/cli/run_freepik_flow.py`

Ví dụ chạy từ root project:

```bash
cd "freepik-automation"
python -m src.cli.run_freepik_flow \
  --idol-image "/full/path/to/idol.png" \
  --dance-video "/full/path/to/dance.mp4" \
  --mode prompt_only
```

- Flow:
  - Mở Gemini web.
  - Dùng prompt trong `prompts/GEMINI_IDOL_ANALYSIS.txt` để yêu cầu JSON:
    - Idol, Dance, BackgroundContext (location, environment_details, depth_and_space),
    - ColorMood (primary_palette, accent_colors, overall_mood, lighting_style),
    - extra_instructions.
  - Parse JSON → build prompt Kling trong `src/core/prompt_builder.py`.
  - Lưu prompt tại: `data/outputs/kling_prompt.txt` và in ra console.

---

### 4. Flow tạo video trên Freepik (Video Generator + Kling)

Module: `src/integrations/freepik_flow.py`

- Hàm tiện ích đọc email/password từ `data/config.json`:

  - `login_freepik_from_config()` – chỉ login.
  - `generate_video_from_config(start_image: Path, video_file: Path)` – login + mở Video Generator + chọn model Kling + upload + Generate.

Ví dụ dùng từ 1 script Python (chạy trong `freepik-automation/`):

```python
from pathlib import Path
import asyncio

from src.integrations.freepik_flow import generate_video_from_config

async def main() -> None:
  await generate_video_from_config(
    start_image=Path("/full/path/to/idol_start_image.png"),
    video_file=Path("/full/path/to/dance_video.mp4"),
  )

asyncio.run(main())
```

- Flow bên trong:
  - Login Freepik bằng `freepik_account.email/password` trong `data/config.json`.
  - Click menu `Video Generator` (sidebar pinned tool).
  - Click button chọn list models, chọn `Kling 2.6 Motion Control`.
  - Upload **Start image*** và **Video** bằng các input file tương ứng.
  - Click nút `Generate` để bắt đầu render video.

---

### 5. Chạy batch nhiều idol_image + dance_video (run_batch)

Script: `run_batch.py` (ở root `freepik-automation/`).

- **Cấu trúc file config JSON** (ví dụ `data/batch_configs/sample_config.json`):

```json
{
  "max_concurrent": 1,
  "items": [
    {
      "name": "Sample_Idol_1",
      "idol_image": "/absolute/path/to/idol1.png",
      "dance_video": "/absolute/path/to/dance1.mp4",
      "mode": "prompt_only"
    },
    {
      "name": "Sample_Idol_2",
      "idol_image": "/absolute/path/to/idol2.png",
      "dance_video": "/absolute/path/to/dance2.mp4",
      "mode": "full"
    }
  ]
}
```

- **Các field chính**:
  - `max_concurrent`: hiện tại batch runner xử lý tuần tự, trường này dùng để mở rộng sau (giữ giống style `veo3-automation`).
  - `items[]`:
    - `name`: tên mô tả (không bắt buộc, chỉ để bạn dễ nhớ).
    - `idol_image`: đường dẫn tuyệt đối tới ảnh idol.
    - `dance_video`: đường dẫn tuyệt đối tới video nhảy.
    - `mode`:
      - `"prompt_only"`: chỉ Gemini + sinh prompt Kling (không đụng Freepik).
      - `"full"`: Gemini + prompt Kling + mở Freepik Video Generator với Kling, upload image/video, bấm Generate.

- **Cách chạy**:

```bash
cd "freepik-automation"
python run_batch.py data/batch_configs/sample_config.json
```

- **Kết quả**:
  - Với mỗi item:
    - `mode="prompt_only"` → sinh prompt và lưu `data/outputs/kling_prompt.txt` (file sẽ bị ghi đè mỗi item, nên nếu cần giữ riêng bạn có thể copy ra chỗ khác sau khi chạy).
    - `mode="full"` → tương tự như trên + tự động mở Freepik và tạo video.
  - Cuối cùng in **batch summary**:
    - Số item thành công/thất bại.
    - Lý do lỗi chi tiết cho từng item fail (thiếu file, lỗi Playwright, lỗi login, v.v.).

