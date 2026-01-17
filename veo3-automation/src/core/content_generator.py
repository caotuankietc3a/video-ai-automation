from typing import Optional

from ..integrations import WebContentGenerator, get_ai_provider
from ..config.prompts import prompt_templates
from ..data.config_manager import config_manager
from ..utils.json_utils import parse_content_sections


class ContentGenerator:
    def __init__(self, project_name: str = "default") -> None:
        self.project_name = project_name
        self.provider_name: str = config_manager.get("default_model", "gemini")
        self.provider = get_ai_provider(self.provider_name)
        self.use_browser: bool = bool(
            config_manager.get("content_generation.use_browser", True),
        )
    
    async def generate_content(self, video_analysis: str, user_script: str = "", project_name: Optional[str] = None, project_config: Optional[dict] = None) -> dict:
        prompt = prompt_templates.get_video_to_content(video_analysis, user_script)
        
        gemini_link = None
        if project_config:
            gemini_link = project_config.get("gemini_project_link") or project_config.get("gemini_video_analysis_link")
        
        if self.use_browser:
            web_client = WebContentGenerator(gemini_project_link=gemini_link)
            content_text = await web_client.generate(prompt, project_config)
        else:
            if not self.provider.is_available():
                raise RuntimeError(f"AI provider {self.provider_name} is not available")
            content_text = await self.provider.generate_text(prompt)
        
        if not content_text:
            raise RuntimeError("Không thể tạo nội dung, content_text rỗng")
        
        project_name = project_name or self.project_name
        from ..utils.response_saver import save_gemini_response
        save_gemini_response(project_name, "content", content_text)
        
        sections = parse_content_sections(content_text)
        
        return {
            "full_content": content_text,
            "characters_section": sections.get("characters", "") if sections else "",
            "story_section": sections.get("story", "") if sections else "",
            "storyboard_section": sections.get("storyboard", "") if sections else ""
        }

