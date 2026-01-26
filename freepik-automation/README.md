## Freepik Automation (Idol TikTok/Vinahouse → Kling)

### Mục tiêu
- Xây flow riêng (tách biệt với `veo3-automation`) cho bài toán:
  - Ảnh idol (có background rõ ràng).
  - Video nhảy TikTok/Vinahouse.
  - **[MỚI]** Tạo ảnh KOL từ idol image + frame đầu video (giữ nguyên khuôn mặt idol, giữ nguyên pose từ video).
  - Tự động phân tích qua Gemini web (browser automation, không dùng API).
  - Sinh prompt tối ưu cho Kling và Nano Banana (với bối cảnh/khung cảnh + tông màu + không khí).
  - Tự động mở Freepik Video Generator + chọn model Kling + upload start image/video + bấm Generate.
  - **[MỚI]** UI application với CustomTkinter để quản lý workflow dễ dàng.

### Cấu trúc thư mục
- `src/`
  - `core/`: model dữ liệu, logic build prompt Kling và Nano Banana.
  - `integrations/`:
    - `gemini_flow.py`: điều khiển Gemini trên browser để phân tích idol + video và trả về JSON structured.
    - `gemini_image_flow.py`: **[MỚI]** điều khiển Gemini để generate ảnh KOL từ idol image + frame đầu video.
    - `freepik_flow.py`: login Freepik + mở Video Generator + chọn model Kling + upload file + Generate.
  - `cli/`: entry scripts để chạy flow từ dòng lệnh.
  - `ui/`: **[MỚI]** UI components (main window, project panel, result panel, settings).
  - `utils/`: **[MỚI]** utility functions (video processing).
- `prompts/`: các file prompt text dùng cho Gemini/Kling.
  - `IDOL_KOL_GENERATION_PROMPT.txt`: **[MỚI]** prompt để tạo ảnh KOL.
- `data/`
  - `inputs/`: ảnh idol + video nhảy đầu vào (nếu muốn quản lý theo folder).
  - `outputs/`: JSON phân tích + prompt Kling + Nano Banana prompt + ảnh KOL.
    - `kol_images/`: **[MỚI]** thư mục chứa ảnh KOL đã generate.
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

**Dependencies chính:**
- `opencv-python`: extract frame từ video
- `customtkinter>=5.2.0`: UI application
- `pillow>=10.0.0`: image preview trong UI
- `pydub`, `SpeechRecognition`: tự động giải reCAPTCHA (audio) khi login Freepik

**reCAPTCHA (login Freepik) – ffmpeg:**
- Giải reCAPTCHA dùng nhận dạng giọng nói từ audio. `pydub` cần **ffmpeg** để đọc/ghi file audio.
- Cài ffmpeg:
  - **macOS:** `brew install ffmpeg`
  - **Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install ffmpeg`
  - **Windows:** tải từ [ffmpeg.org](https://ffmpeg.org/download.html) hoặc `winget install ffmpeg`, rồi thêm vào PATH.
- Speech: ưu tiên Google Speech API; nếu lỗi sẽ thử fallback offline (Sphinx). Cài thêm `pocketsphinx` để dùng fallback: `pip install pocketsphinx`.

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

**Hoặc cấu hình qua UI:** Mở Settings tab trong UI application và nhập thông tin tài khoản.

---

### 3. Chạy UI Application (MỚI)

Chạy ứng dụng UI với giao diện đồ họa:

```bash
cd "freepik-automation"
python main.py
```

**Tính năng UI:**
- Upload idol image và dance video qua file dialog
- Checkbox để chọn có tạo ảnh KOL hay không
- Upload first frame (optional) hoặc tự động extract từ video
- Buttons để:
  - Generate KOL Image
  - Generate Nano Banana Prompt
  - Generate Video (Freepik)
- Hiển thị kết quả:
  - Preview ảnh KOL đã generate
  - Nano Banana Prompt (có thể copy/save)
  - Video results
  - Activity logs
- Settings tab để cấu hình Freepik account

---

### 4. Chạy flow phân tích Gemini → sinh prompt (CLI)

CLI: `src/cli/run_freepik_flow.py`

**Ví dụ cơ bản:**

```bash
cd "freepik-automation"
python -m src.cli.run_freepik_flow \
  --idol-image "/full/path/to/idol.png" \
  --dance-video "/full/path/to/dance.mp4" \
  --mode prompt_only
```

**Ví dụ với tạo ảnh KOL:**

```bash
cd "freepik-automation"
python -m src.cli.run_freepik_flow \
  --idol-image "/full/path/to/idol.png" \
  --dance-video "/full/path/to/dance.mp4" \
  --mode prompt_only \
  --generate-kol-image
```

**Ví dụ với first frame tự cung cấp:**

```bash
cd "freepik-automation"
python -m src.cli.run_freepik_flow \
  --idol-image "/full/path/to/idol.png" \
  --dance-video "/full/path/to/dance.mp4" \
  --mode prompt_only \
  --generate-kol-image \
  --first-frame "/full/path/to/first_frame.jpg"
```

**Các flags:**
- `--idol-image`: Đường dẫn ảnh idol (required)
- `--dance-video`: Đường dẫn video nhảy (required)
- `--mode`: `prompt_only` hoặc `full` (default: `prompt_only`)
- `--generate-kol-image`: **[MỚI]** Flag để tạo ảnh KOL từ idol image + frame đầu video
- `--first-frame`: **[MỚI]** Đường dẫn frame đầu (optional, nếu không cung cấp sẽ tự động extract từ video)

**Flow:**
- Nếu `--generate-kol-image` được bật:
  - Tự động extract frame đầu từ video (nếu không có `--first-frame`)
  - Mở Gemini web và upload idol image + first frame
  - Generate ảnh KOL với khuôn mặt idol, giữ nguyên pose từ frame đầu
  - Lưu ảnh KOL vào `data/outputs/kol_images/`
  - Sử dụng ảnh KOL làm input cho bước tiếp theo
- Mở Gemini web để phân tích idol + video
- Dùng prompt trong `prompts/IDOL_VIDEO_ANALYSIS_PROMPT.txt` để yêu cầu JSON:
  - Idol, Dance, BackgroundContext (location, environment_details, depth_and_space),
  - ColorMood (primary_palette, accent_colors, overall_mood, lighting_style),
  - extra_instructions.
- Parse JSON → build prompt Kling trong `src/core/prompt_builder.py`.
- **[MỚI]** Build prompt Nano Banana trong `src/core/nano_banana_prompt_builder.py`.
- Lưu prompts tại:
  - `data/outputs/kling_prompt.txt`
  - `data/outputs/nano_banana_prompt.txt` **[MỚI]**
- In prompts ra console.

---

### 5. Flow tạo ảnh KOL (MỚI)

Module: `src/integrations/gemini_image_flow.py`

**Mục đích:** Tạo ảnh KOL từ idol image + frame đầu video để đảm bảo pose chính xác khi ghép video, tránh lệch hình.

**Cách hoạt động:**
1. Extract frame đầu từ video (hoặc sử dụng frame đã cung cấp)
2. Upload idol image + first frame vào Gemini
3. Sử dụng prompt `prompts/IDOL_KOL_GENERATION_PROMPT.txt`:
   - Giữ nguyên khuôn mặt của idol từ ảnh input
   - Giữ nguyên pose, kiểu tóc, trang phục từ frame đầu video
   - Đảm bảo pose chính xác để ghép video không bị lệch hình
4. Download ảnh KOL đã generate về local
5. Lưu vào `data/outputs/kol_images/`

**Sử dụng trong code:**

```python
from pathlib import Path
import asyncio
from src.integrations.gemini_image_flow import (
    GeminiImageGenerator,
    default_gemini_image_config,
)
from src.utils.video_utils import extract_first_frame
from src.config.constants import BASE_DIR, KOL_IMAGES_DIR

async def main():
    idol_image = Path("/path/to/idol.png")
    dance_video = Path("/path/to/dance.mp4")
    
    # Extract frame đầu
    first_frame = extract_first_frame(dance_video)
    
    # Generate ảnh KOL
    config = default_gemini_image_config(BASE_DIR)
    generator = GeminiImageGenerator(config)
    
    KOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = KOL_IMAGES_DIR / "kol_generated.jpg"
    
    kol_image = await generator.generate_kol_image(
        idol_image_path=idol_image,
        first_frame_path=first_frame,
        output_path=output_path,
    )
    
    print(f"Đã tạo ảnh KOL: {kol_image}")

asyncio.run(main())
```

---

### 6. Flow tạo video trên Freepik (Video Generator + Kling)

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
    start_image=Path("/full/path/to/idol_start_image.png"),  # Có thể dùng ảnh KOL
    video_file=Path("/full/path/to/dance_video.mp4"),
  )

asyncio.run(main())
```

- Flow bên trong:
  - Login Freepik bằng `freepik_account.email/password` trong `data/config.json`.
  - Click menu `Video Generator` (sidebar pinned tool).
  - Click button chọn list models, chọn `Kling 2.6 Motion Control`.
  - Upload **Start image** (có thể là ảnh KOL) và **Video** bằng các input file tương ứng.
  - Click nút `Generate` để bắt đầu render video.

---

### 7. Chạy batch nhiều idol_image + dance_video (run_batch)

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
      "mode": "prompt_only",
      "generate_kol_image": false
    },
    {
      "name": "Sample_Idol_2",
      "idol_image": "/absolute/path/to/idol2.png",
      "dance_video": "/absolute/path/to/dance2.mp4",
      "mode": "full",
      "generate_kol_image": true,
      "first_frame": "/absolute/path/to/first_frame.jpg"
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
      - `"prompt_only"`: chỉ Gemini + sinh prompt Kling và Nano Banana (không đụng Freepik).
      - `"full"`: Gemini + prompt Kling + Nano Banana + mở Freepik Video Generator với Kling, upload image/video, bấm Generate.
    - `generate_kol_image`: **[MỚI]** (optional, default: false) có tạo ảnh KOL hay không.
    - `first_frame`: **[MỚI]** (optional) đường dẫn frame đầu, nếu không có sẽ tự động extract từ video.

- **Cách chạy**:

```bash
cd "freepik-automation"
python run_batch.py data/batch_configs/sample_config.json
```

- **Kết quả**:
  - Với mỗi item:
    - Nếu `generate_kol_image=true`: tạo ảnh KOL và lưu vào `data/outputs/kol_images/`
    - `mode="prompt_only"` → sinh prompt và lưu:
      - `data/outputs/kling_prompt.txt`
      - `data/outputs/nano_banana_prompt.txt` **[MỚI]**
      - (file sẽ bị ghi đè mỗi item, nên nếu cần giữ riêng bạn có thể copy ra chỗ khác sau khi chạy).
    - `mode="full"` → tương tự như trên + tự động mở Freepik và tạo video.
  - Cuối cùng in **batch summary**:
    - Số item thành công/thất bại.
    - Lý do lỗi chi tiết cho từng item fail (thiếu file, lỗi Playwright, lỗi login, v.v.).

---

### 8. Cấu trúc dữ liệu

**Models (`src/core/models.py`):**
- `IdolInfo`: Thông tin idol (name, outfit_description, pose_style, body_type)
- `DanceInfo`: Thông tin nhảy (style, bpm, energy_level)
- `BackgroundContext`: Bối cảnh (location, environment_details, depth_and_space)
- `ColorMood`: Tông màu (primary_palette, accent_colors, overall_mood, lighting_style)
- `KlingPromptData`: Dữ liệu để build prompt Kling
- `KlingPromptResult`: Kết quả prompt Kling
- `KolImageResult`: **[MỚI]** Kết quả ảnh KOL (image_path, idol_image_path, first_frame_path)

**Project Manager (`src/data/project_manager.py`):**
- Quản lý projects với các field:
  - `idol_image`: đường dẫn ảnh idol
  - `dance_video`: đường dẫn video nhảy
  - `kol_image`: **[MỚI]** đường dẫn ảnh KOL (nếu có)
  - `kling_prompt`: prompt Kling
  - `nano_banana_prompt`: **[MỚI]** prompt Nano Banana
  - `kling_data`: JSON data từ Gemini analysis
  - `status`: trạng thái project

---

### 9. Troubleshooting

**Lỗi "Không thể đọc frame đầu từ video":**
- Đảm bảo video file hợp lệ và có thể đọc được
- Kiểm tra codec video có được OpenCV hỗ trợ không

**Lỗi "Không thể download ảnh từ Gemini":**
- Gemini có thể cần thời gian để generate image, đợi đủ lâu
- Kiểm tra network connection
- Có thể cần đăng nhập Gemini trước khi chạy

**Lỗi UI không hiển thị:**
- Đảm bảo đã cài `customtkinter` và `pillow`
- Kiểm tra Python version >= 3.10

**Lỗi "Freepik account not configured":**
- Cấu hình email/password trong `data/config.json` hoặc Settings tab trong UI

**Lỗi reCAPTCHA / pydub / ffmpeg:**
- `Need ffmpeg` hoặc lỗi khi xử lý audio reCAPTCHA: cài ffmpeg (xem mục 1).
- Muốn fallback offline khi Google Speech lỗi: `pip install pocketsphinx`.

---

### 10. Tính năng mới (Updates)

**Version mới:**
- ✅ Tạo ảnh KOL từ idol image + frame đầu video
- ✅ Nano Banana Prompt generation
- ✅ UI Application với CustomTkinter
- ✅ Extract frame đầu từ video tự động
- ✅ Project management với KOL image tracking

**Roadmap:**
- [ ] Batch processing với KOL image generation
- [ ] Preview video trong UI
- [ ] Export/Import projects
- [ ] Advanced settings cho Gemini Image Generation
