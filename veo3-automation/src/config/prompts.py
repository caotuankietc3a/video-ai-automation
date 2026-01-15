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
    
    def get_video_to_content(self, video_analysis: str, user_prompt: str = "") -> str:
        return self.format('VIDEO_TO_CONTENT_PROMPT', 
                          video_analysis=video_analysis)
    
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

