import json
from typing import Dict, Any, Optional
from ..integrations import get_ai_provider, WebContentGenerator
from ..config.prompts import prompt_templates
from ..data.config_manager import config_manager
from ..utils.json_utils import extract_json_from_text, validate_character_json

class CharacterExtractor:
    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.provider_name = config_manager.get("default_model", "gemini")
        self.provider = get_ai_provider(self.provider_name)
        self.use_browser: bool = bool(
            config_manager.get("character_extraction.use_browser", True),
        )
        self.web_client: Optional[WebContentGenerator]
        if self.use_browser:
            self.web_client = WebContentGenerator()
        else:
            self.web_client = None
    
    async def extract_characters(self, content: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        prompt = prompt_templates.get_content_to_character(content)
        if self.use_browser and self.web_client is not None:
            response_text = await self.web_client.generate(prompt)
        else:
            if not self.provider.is_available():
                raise RuntimeError(f"AI provider {self.provider_name} is not available")
            response_text = await self.provider.generate_text(prompt)
        
        try:
            characters_json = extract_json_from_text(response_text)
            
            if not validate_character_json(characters_json):
                raise ValueError("Invalid character JSON structure")
            
            project_name = project_name or self.project_name
            from ..utils.response_saver import save_gemini_response
            save_gemini_response(project_name, "characters", response_text)
            
            return characters_json
        except Exception as e:
            raise ValueError(f"Failed to parse character JSON: {e}")

