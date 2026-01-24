# Hướng Dẫn Sử Dụng: Tạo Prompt cho Idol + Affiliate Product

## Workflow Tổng Quan

Khi bạn có:
- **Ảnh idol** (ảnh nhân vật chính)
- **Ảnh sản phẩm affiliate** (sản phẩm cần quảng cáo)

Bạn sẽ tạo prompt để generate ảnh idol mặc/đeo/sử dụng sản phẩm bằng Nano Banana Image.

## Các Bước Thực Hiện

### Bước 1: Phân Tích Ảnh với Gemini AI

1. Mở Gemini AI (https://gemini.google.com/app)
2. Upload 2 ảnh:
   - Ảnh idol
   - Ảnh sản phẩm affiliate
3. Copy nội dung từ file `GEMINI_IDOL_PRODUCT_ANALYSIS.txt` và paste vào chat
4. Gemini sẽ phân tích và trả về JSON với cấu trúc:
   ```json
   {
     "idol": {
       "name": "...",
       "outfit_description": "...",
       "pose_style": "...",
       "body_type": "..."
     },
     "product": {
       "name": "...",
       "category": "...",
       "description": "...",
       "placement": "...",
       "visibility": "..."
     },
     "background": {...},
     "color_mood": {...},
     "composition": {
       "aspect_ratio": "9:16",
       "framing": "full body"
     },
     "extra_instructions": "..."
   }
   ```

### Bước 2: Chọn Template Prompt Phù Hợp

Dựa vào `product.category` từ JSON, chọn template tương ứng trong file `NANO_BANANA_IDOL_PRODUCT.txt`:

- **clothing** → Template cho Quần Áo
- **accessory** → Template cho Phụ Kiện
- **jewelry** → Template cho Trang Sức
- **electronics** → Template cho Điện Tử
- **cosmetics** → Template cho Mỹ Phẩm
- **Khác** → Template Tổng Quát

Nếu cần format cụ thể:
- **9:16** (vertical) → Template cho Ảnh Dọc TikTok/Instagram Story
- **1:1** (square) → Template cho Ảnh Vuông Instagram Post

### Bước 3: Điền Thông Tin vào Template

Thay thế các biến trong template bằng dữ liệu từ JSON:

**Các biến cần thay:**
- `{idol_name_segment}` → `{idol.name} ` (nếu có) hoặc bỏ qua
- `{idol_outfit_description}` → `{idol.outfit_description}`
- `{pose_style}` → `{idol.pose_style}`
- `{product_name}` → `{product.name}`
- `{product_description}` → `{product.description}`
- `{product_placement}` → `{product.placement}`
- `{product_visibility}` → `{product.visibility}`
- `{background_location}` → `{background.location}`
- `{background_environment_details}` → `{background.environment_details}`
- `{background_depth_and_space}` → `{background.depth_and_space}`
- `{primary_palette}` → `", ".join(color_mood.primary_palette)`
- `{accent_colors}` → `", ".join(color_mood.accent_colors)`
- `{overall_mood}` → `{color_mood.overall_mood}`
- `{lighting_style}` → `{color_mood.lighting_style}`
- `{composition_framing}` → `{composition.framing}`
- `{composition_aspect_ratio}` → `{composition.aspect_ratio}`
- `{extra_instructions_optional}` → `{extra_instructions}` (nếu có)

### Bước 4: Sử Dụng Prompt với Nano Banana Image

Copy prompt đã điền đầy đủ và sử dụng với Nano Banana Image generation tool.

## Ví Dụ Cụ Thể

### Input:
- Ảnh idol: Nữ idol mặc áo trắng, đứng tự nhiên
- Ảnh sản phẩm: Túi xách da màu đen

### JSON từ Gemini (ví dụ):
```json
{
  "idol": {
    "name": null,
    "outfit_description": "wearing a white casual t-shirt and blue jeans",
    "pose_style": "confident standing pose with hand on hip",
    "body_type": "slim"
  },
  "product": {
    "name": "leather handbag",
    "category": "accessory",
    "description": "black leather handbag with gold hardware, structured design, medium size",
    "placement": "carrying",
    "visibility": "prominently"
  },
  "background": {
    "location": "modern minimalist studio",
    "environment_details": "clean white background with subtle shadows",
    "depth_and_space": "idol in foreground with ample space around, shallow depth of field"
  },
  "color_mood": {
    "primary_palette": ["white", "soft gray", "black"],
    "accent_colors": ["gold accents"],
    "overall_mood": "elegant and modern",
    "lighting_style": "soft studio lighting"
  },
  "composition": {
    "aspect_ratio": "9:16",
    "framing": "full body"
  },
  "extra_instructions": null
}
```

### Prompt sau khi điền (Template cho Phụ Kiện):
```
A stylish fashion photo featuring wearing a white casual t-shirt and blue jeans
carrying a leather handbag - black leather handbag with gold hardware, structured design, medium size. 
The idol poses in a confident standing pose with hand on hip stance, with the leather handbag 
prominently showcased as a key element of the look. Background: modern minimalist studio 
enhanced by clean white background with subtle shadows, utilizing idol in foreground with ample 
space around, shallow depth of field for visual depth. Color scheme focuses on white, soft gray, 
black highlighted by gold accents, creating a elegant and modern aesthetic with soft studio lighting 
illumination. Professional fashion photography, full body composition, 9:16 format, the leather 
handbag is clearly visible and well-lit, high detail, magazine quality.
```

## Lưu Ý Quan Trọng

1. **Đảm bảo sản phẩm nổi bật**: Chọn `visibility` phù hợp (prominent, featured cho sản phẩm quan trọng)
2. **Placement phù hợp**: 
   - Quần áo → "wearing"
   - Túi, ví → "carrying", "holding"
   - Trang sức → "adorned with", "wearing"
   - Điện tử → "using", "holding"
3. **Aspect ratio**: Chọn theo nền tảng đăng bài:
   - TikTok/Instagram Story: 9:16
   - Instagram Feed: 1:1 hoặc 4:5
4. **Framing**: 
   - Full body: Cho sản phẩm lớn (quần áo, túi)
   - Half body: Cho phụ kiện, trang sức
   - Close-up: Cho mỹ phẩm, trang sức nhỏ

## Tự Động Hóa (Tùy Chọn)

Bạn có thể tạo script Python để tự động:
1. Upload ảnh lên Gemini và lấy JSON
2. Parse JSON và chọn template
3. Điền thông tin vào template
4. Generate prompt cuối cùng

Script có thể tham khảo cấu trúc từ `src/integrations/gemini_flow.py` và `src/core/prompt_builder.py`.
