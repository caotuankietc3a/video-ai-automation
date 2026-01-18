# VEO3 AI Automation Tool

Tool tự động hóa quy trình tạo video VEO3 với AI, hỗ trợ phân tích video, tạo nội dung, trích xuất nhân vật, tạo scenes và generate video một cách tự động.

## 📋 Mục lục

- [Tính năng](#tính-năng)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Sử dụng](#sử-dụng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Workflow](#workflow)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## ✨ Tính năng

### Core Features

- **Phân tích video tự động**: Sử dụng AI Vision để phân tích nội dung video, nhân vật, bối cảnh
- **Tạo nội dung mới**: Tạo câu chuyện và nội dung mới dựa trên video gốc với tính giáo dục
- **Trích xuất nhân vật**: Tự động trích xuất thông tin nhân vật thành JSON structured data
- **Tạo scenes**: Tạo danh sách scenes với tính liên tục và logic
- **Generate VEO3 prompts**: Chuyển đổi scenes thành prompts tối ưu cho VEO3
- **Tạo video VEO3**: Tự động tạo video qua Google Flow (browser automation hoặc API)

### UI Features

- **Giao diện hiện đại**: CustomTkinter với dark theme
- **Quản lý projects**: Tạo, lưu, copy, xóa projects
- **Upload video**: Hỗ trợ upload từ local file hoặc URL (YouTube, TikTok)
- **Real-time updates**: Auto-refresh kết quả và progress tracking
- **Activity logs**: Ghi lại toàn bộ quá trình workflow

### AI Integration

- **Multi-provider support**: Gemini, OpenAI, Anthropic, Local models (Ollama)
- **Flexible switching**: Dễ dàng chuyển đổi giữa các AI providers
- **Browser automation**: Playwright automation cho Google Flow

## 💻 Yêu cầu hệ thống

- Python 3.8+
- macOS, Windows, hoặc Linux
- RAM: Tối thiểu 4GB (khuyến nghị 8GB+)
- Disk space: Tối thiểu 2GB cho dependencies và data

## 🚀 Cài đặt

### 1. Clone repository

```bash
cd "/Users/kietcao/Movies/AI Automation Optimization/veo3-automation"
```

### 2. Tạo virtual environment (khuyến nghị)

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cài đặt Playwright browsers

```bash
playwright install chromium
```

### 5. Kiểm tra cài đặt

```bash
python main.py
```

Nếu không có lỗi, ứng dụng sẽ khởi động với giao diện desktop.

## ⚙️ Cấu hình

### API Keys

1. Mở ứng dụng và vào tab **"Cài đặt"**
2. Nhập API keys cho các providers bạn muốn sử dụng:
   - **Gemini API Key**: Lấy từ [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **OpenAI API Key**: Lấy từ [OpenAI Platform](https://platform.openai.com/api-keys)
   - **Anthropic API Key**: Lấy từ [Anthropic Console](https://console.anthropic.com/)
3. Click **"Lưu API Keys"**

### Local AI Models (Optional)

Nếu sử dụng local models với Ollama:

1. Cài đặt Ollama: https://ollama.ai/
2. Chạy Ollama server:
   ```bash
   ollama serve
   ```
3. Pull model:
   ```bash
   ollama pull llama2
   ```
4. Trong app, local API URL mặc định là `http://localhost:11434`

### Cấu hình mặc định

File cấu hình được lưu tại `data/config.json`. Bạn có thể chỉnh sửa trực tiếp hoặc qua UI:

- `default_model`: Model mặc định (gemini, openai, anthropic, local)
- `default_style`: Phong cách video mặc định
- `default_duration`: Thời lượng video mặc định (giây)
- `auto_update_interval`: Khoảng thời gian auto-refresh (giây)

## 📖 Sử dụng

### Batch Runner (CLI)

Chạy workflow VEO3 cho nhiều videos cùng lúc từ command line.

#### Cách sử dụng

```bash
cd veo3-automation

# Chạy với config file
python run_batch.py data/batch_configs/sample_config.json

# Override số lượng video chạy song song
python run_batch.py config.json --max-concurrent 3

# Dry run để xem preview (không thực hiện)
python run_batch.py config.json --dry-run

# Hoặc dùng shell script
./run_batch.sh data/batch_configs/sample_config.json
```

#### Cấu trúc file JSON config

```json
{
  "default_config": {
    "duration": 120,
    "style": "3d_Pixar",
    "aspect_ratio": "Khổ dọc (9:16)",
    "veo_profile": "VEO3 ULTRA",
    "ai_model": "VEO3 ULTRA",
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
```

#### Các tùy chọn config

| Field | Mô tả | Mặc định |
|-------|-------|----------|
| `duration` | Thời lượng video (giây) | 120 |
| `style` | Phong cách video | "3d_Pixar" |
| `aspect_ratio` | Tỷ lệ khung hình | "Khổ dọc (9:16)" |
| `veo_profile` | VEO3 profile | "VEO3 ULTRA" |
| `ai_model` | AI model viết prompt | "VEO3 ULTRA" |
| `outputs_per_prompt` | Số video/prompt | 1 |
| `max_concurrent` | Số video chạy song song | 2 |

#### Styles có sẵn

- `3d_Pixar`
- `anime_2d`
- `cinematic`
- `live_action`

#### Aspect Ratios có sẵn

- `Khổ dọc (9:16)` - TikTok/Reels
- `Khổ ngang (16:9)` - YouTube
- `Khổ vuông (1:1)` - Instagram

---

### Workflow cơ bản (GUI)

1. **Tạo Project mới**

   - Nhập tên project
   - Click **"+ Mới"** hoặc nhập tên và click **"Lưu"**

2. **Upload Video**

   - Click **"Upload Video"** để chọn file từ máy
   - Hoặc click **"Copy từ Youtube/Tiktok:"** để nhập URL

3. **Nhập Script/Idea** (Optional)

   - Nhập kịch bản hoặc ý tưởng vào textarea "Kịch bản / Ý tưởng"

4. **Cấu hình Settings**

   - Chọn **Phong cách** (3d_Pixar, anime_2d, cinematic, live_action)
   - Nhập **Thời lượng video** (giây)
   - Chọn **Veo Profile** (VEO3, VEO3 ULTRA, VEO3.1, VEO3.1 Fast)
   - Chọn **AI model viết prompt**

5. **Khởi động Workflow**

   - Click **"Khởi động"** để bắt đầu
   - Theo dõi progress trong tab **"5. Nhật ký hoạt động"**

6. **Xem kết quả**

   - Tab **"1. Nhân vật"**: Xem danh sách nhân vật đã trích xuất
   - Tab **"2. Phân cảnh"**: Xem danh sách scenes
   - Tab **"3. Prompts"**: Xem VEO3 prompts đã generate
   - Tab **"4. Video by VEO3"**: Xem danh sách videos đã tạo

7. **Merge Videos** (Optional)
   - Click **"Merge video"** để gộp tất cả videos thành một file
   - Click **"Open the merged video"** để mở file đã merge

### Quản lý Projects

- **Lưu project**: Click **"Lưu"** để lưu thay đổi
- **Copy project**: Chọn project từ dropdown, click **"+ Copy"**
- **Xóa project**: Chọn project, click **"Xóa"**
- **Load project**: Chọn project từ dropdown

### Auto Update

- Nhập số giây vào **"Auto update (seconds)"**
- Click **"Apply"** để kích hoạt auto-refresh
- Kết quả sẽ tự động cập nhật theo khoảng thời gian đã đặt

## 📁 Cấu trúc dự án

```
veo3-automation/
├── main.py                 # Entry point (GUI)
├── run_batch.py            # Batch runner CLI
├── run_batch.sh            # Shell script wrapper
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
├── .gitignore            # Git ignore rules
│
├── prompts/              # Prompt templates
│   └── veo3_prompts.txt  # Original prompt templates
│
├── data/                 # Data storage
│   ├── projects/         # Project JSON files
│   ├── videos/           # Uploaded videos
│   ├── outputs/          # Generated videos
│   ├── logs/             # Activity logs
│   ├── batch_configs/    # Batch runner config files
│   │   └── sample_config.json
│   └── config.json       # App configuration
│
└── src/                  # Source code
    ├── config/           # Configuration
    │   ├── constants.py  # App constants
    │   └── prompts.py    # Prompt loader
    │
    ├── core/             # Workflow engine
    │   ├── workflow.py   # Main orchestrator
    │   ├── batch_runner.py  # Batch processing
    │   ├── video_analyzer.py
    │   ├── content_generator.py
    │   ├── character_extractor.py
    │   ├── scene_generator.py
    │   └── veo3_prompt_generator.py
    │
    ├── integrations/     # External integrations
    │   ├── ai_providers.py
    │   ├── gemini_client.py
    │   ├── openai_client.py
    │   ├── anthropic_client.py
    │   ├── local_ai_client.py
    │   ├── browser_automation.py
    │   └── veo3_flow.py
    │
    ├── data/             # Data management
    │   ├── config_manager.py
    │   ├── project_manager.py
    │   └── video_manager.py
    │
    ├── utils/            # Utilities
    │   ├── json_utils.py
    │   └── logger.py
    │
    └── ui/               # User interface
        ├── main_window.py
        ├── run_tab.py
        ├── settings_tab.py
        ├── project_panel.py
        ├── result_panel.py
        └── components/
            ├── character_view.py
            ├── scene_view.py
            ├── video_list.py
            └── log_view.py
```

## 🔄 Workflow

Tool thực hiện workflow tự động qua 6 bước:

### 1. VIDEO_ANALYSIS

- **Input**: Video file(s) hoặc URL(s)
- **Process**:
  - Extract frames từ video (10 frames/video)
  - Gửi frames + prompt đến AI Vision model
  - Phân tích: nội dung, nhân vật, bối cảnh, phong cách, tông màu
- **Output**: Video analysis text

### 2. VIDEO_TO_CONTENT_PROMPT

- **Input**: Video analysis + user script/idea
- **Process**:
  - Load prompt template
  - Format prompt với video_analysis
  - Gọi AI model để generate content mới
  - Parse response thành 3 phần: Characters, Story, Storyboard
- **Output**: Content description (characters, story, storyboard)

### 3. CONTENT_TO_CHARACTER_PROMPT

- **Input**: Content từ bước 2
- **Process**:
  - Load character extraction prompt
  - Gọi AI model với content
  - Parse và validate JSON response
  - Extract tất cả nhân vật với đầy đủ thông tin
- **Output**: `characters.json` file

### 4. CONTENT_TO_SCENE_PROMPT

- **Input**: Content + characters.json
- **Process**:
  - Tính số scenes (theo công thức: T = N × l, S = round(T/8))
  - Load scene generation prompt
  - Gọi AI model
  - Parse và validate scenes JSON array
  - Đảm bảo tính liên tục giữa scenes
- **Output**: `scenes.json` array

### 5. SCENE_TO_PROMPT_VEO3

- **Input**: Scene JSON + characters.json
- **Process**:
  - Load VEO3 prompt template
  - Convert scene JSON thành VEO3 prompt text (tiếng Anh)
  - Generate prompt chi tiết cho từng scene
  - Đảm bảo tính nhất quán với scene trước
- **Output**: VEO3 prompts (text)

### 6. VEO3 Generation

- **Input**: VEO3 prompts
- **Process**:
  - Sử dụng Playwright để automate Google Flow (nếu use_browser=True)
  - Hoặc gọi Gemini API với VEO3 flow
  - Monitor generation status
  - Download generated videos
- **Output**: Video files

## 🐛 Troubleshooting

### Lỗi "API key not configured"

- **Giải pháp**: Vào tab "Cài đặt" và nhập API key cho provider bạn đang sử dụng

### Lỗi "Prompt file not found"

- **Giải pháp**: Đảm bảo file `prompts/veo3_prompts.txt` tồn tại

### Lỗi "Browser automation failed"

- **Giải pháp**:
  - Chạy `playwright install chromium`
  - Kiểm tra kết nối internet
  - Thử tắt browser automation và dùng API mode

### Video không upload được

- **Giải pháp**:
  - Kiểm tra định dạng file (hỗ trợ: mp4, avi, mov, mkv)
  - Kiểm tra dung lượng file
  - Kiểm tra quyền ghi vào thư mục `data/videos/`

### Workflow bị dừng giữa chừng

- **Giải pháp**:
  - Kiểm tra logs trong tab "5. Nhật ký hoạt động"
  - Kiểm tra API keys còn hợp lệ
  - Kiểm tra kết nối internet
  - Thử chạy lại từ đầu

### JSON parsing errors

- **Giải pháp**:
  - Kiểm tra response từ AI model
  - Thử với model khác (Gemini thường cho kết quả tốt hơn)
  - Kiểm tra prompt templates có đúng format không

## 📝 Notes

- **API Costs**: Sử dụng AI APIs sẽ tốn phí. Kiểm tra pricing của từng provider
- **Processing Time**: Workflow có thể mất vài phút đến vài giờ tùy vào số lượng videos và độ phức tạp
- **Video Quality**: Chất lượng video phụ thuộc vào VEO3 profile và settings
- **Browser Automation**: Cần đăng nhập Google account để sử dụng Google Flow

## 🔧 Development

### Chạy tests (nếu có)

```bash
python -m pytest tests/
```

### Format code

```bash
black src/
```

### Type checking

```bash
mypy src/
```

## 📄 License

Dự án này được phát triển cho mục đích sử dụng nội bộ.

## 👥 Contributors

- Development: AI Automation Team

## 📞 Support

Nếu gặp vấn đề, vui lòng kiểm tra:

1. Logs trong tab "5. Nhật ký hoạt động"
2. File `data/logs/` để xem chi tiết
3. Documentation trong code comments

---

**Version**: 1.1.0  
**Last Updated**: 2026
