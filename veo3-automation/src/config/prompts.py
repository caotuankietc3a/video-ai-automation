import os
import re
from typing import Dict

from .constants import PROMPTS_DIR

PROMPT_FILES = {
    "VIDEO_ANALYSIS": "VIDEO_ANALYSIS.txt",
    "VIDEO_TO_CONTENT_PROMPT": "VIDEO_TO_CONTENT_PROMPT.txt",
    "CONTENT_TO_CHARACTER_PROMPT": "CONTENT_TO_CHARACTER_PROMPT.txt",
    "CONTENT_TO_SCENE_PROMPT": "CONTENT_TO_SCENE_PROMPT.txt",
    "SCENE_TO_PROMPT_VEO3": "SCENE_TO_PROMPT_VEO3.txt",
}

class PromptTemplates:
    def __init__(self):
        self.templates: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        for key, filename in PROMPT_FILES.items():
            file_path = os.path.join(PROMPTS_DIR, filename)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Prompt file not found: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # Bỏ dòng tiêu đề (tên section) nếu có ở dòng đầu
            lines = content.splitlines()
            if lines and lines[0].strip() == key:
                content = "\n".join(lines[1:]).lstrip()
            self.templates[key] = content
    
    def get(self, prompt_name: str) -> str:
        if prompt_name not in self.templates:
            raise ValueError(f"Prompt template '{prompt_name}' not found")
        return self.templates[prompt_name]
    
    def format(self, prompt_name: str, **kwargs) -> str:
        template = self.get(prompt_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {e}")
    
    def get_video_analysis(self) -> str:
        return self.get('VIDEO_ANALYSIS')
    
    def get_video_to_content(self, video_analysis: str, user_prompt: str = "", duration: int = 120, style: str = "3d_Pixar") -> str:
        style_guidelines = self._get_style_guidelines(style)
        return self.format('VIDEO_TO_CONTENT_PROMPT', 
                          video_analysis=video_analysis,
                          duration=duration,
                          style_guidelines=style_guidelines)
    
    def _get_style_guidelines(self, style: str) -> str:
        style_guides = {
            "3d_Pixar": """PHONG CÁCH 3D PIXAR:
- Nhân vật có phong cách 3D hoạt hình Pixar: mắt to, biểu cảm rõ ràng, màu sắc tươi sáng
- Môi trường 3D với ánh sáng mềm mại, bóng đổ mượt mà
- Chuyển động mượt mà, tự nhiên, có tính vật lý
- Màu sắc sống động, bão hòa cao, phù hợp với trẻ em
- Phong cách vui tươi, hài hước, thân thiện
- Nhân vật có tính cách rõ ràng, dễ thương""",
            
            "anime_2d": """PHONG CÁCH ANIME 2D:
- Nhân vật phong cách anime Nhật Bản: mắt to, tóc nhiều màu, biểu cảm phóng đại
- Môi trường 2D với đường nét rõ ràng, màu sắc phẳng hoặc gradient
- Chuyển động năng động, có thể có hiệu ứng tốc độ (speed lines)
- Màu sắc anime đặc trưng: pastel, neon, hoặc màu sáng
- Phong cách biểu cảm mạnh mẽ, cảm xúc rõ ràng
- Có thể có các yếu tố manga/anime: chibi, super deformed""",
            
            "cinematic": """PHONG CÁCH CINEMATIC:
- Nhân vật và môi trường có độ chi tiết cao, realistic
- Ánh sáng điện ảnh: dramatic lighting, chiaroscuro
- Chuyển động máy quay chuyên nghiệp: dolly, crane, tracking shots
- Màu sắc được chỉnh màu (color grading) theo mood
- Phong cách nghiêm túc, kịch tính, có chiều sâu
- Bố cục khung hình cân đối, quy tắc 1/3""",
            
            "live_action": """PHONG CÁCH LIVE ACTION:
- Nhân vật và môi trường thật, không phải hoạt hình
- Ánh sáng tự nhiên hoặc ánh sáng phim trường
- Chuyển động thật, tự nhiên, có thể có camera shake nhẹ
- Màu sắc tự nhiên, realistic
- Phong cách chân thực, gần gũi với cuộc sống
- Nhân vật diễn xuất tự nhiên, không phóng đại"""
        }
        return style_guides.get(style, style_guides["3d_Pixar"])
    
    def get_content_to_character(self, content: str) -> str:
        return self.format('CONTENT_TO_CHARACTER_PROMPT', content=content)
    
    def get_content_to_scene(self, content: str, characters_json: str) -> str:
        return self.format('CONTENT_TO_SCENE_PROMPT', 
                          content=content, 
                          characters_json=characters_json)
    
    def get_scene_to_veo3(self, scene_json: str, characters_info: str) -> str:
        return self.format('SCENE_TO_PROMPT_VEO3',
                          scene_json=scene_json,
                          characters_info=characters_info)

prompt_templates = PromptTemplates()

