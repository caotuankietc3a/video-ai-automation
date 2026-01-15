import os
from typing import Optional
from ..config.constants import PROMPTS_RESPONSES_DIR


def save_gemini_response(project_name: str, response_type: str, response: str) -> None:
    """
    Lưu response từ Gemini vào file theo project.
    
    Args:
        project_name: Tên project
        response_type: Loại response (video_analysis, content, characters, scenes, veo3_prompts)
        response: Nội dung response cần lưu
    """
    if not project_name:
        project_name = "default"
    
    project_prompts_dir = os.path.join(PROMPTS_RESPONSES_DIR, project_name)
    os.makedirs(project_prompts_dir, exist_ok=True)
    
    filename_map = {
        "video_analysis": "video_analysis.txt",
        "content": "content.txt",
        "characters": "characters_response.txt",
        "scenes": "scenes_response.txt",
        "veo3_prompts": "veo3_prompts_response.txt",
    }
    
    filename = filename_map.get(response_type, f"{response_type}.txt")
    file_path = os.path.join(project_prompts_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response)

