import json
import math
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..integrations import get_ai_provider, WebContentGenerator
from ..config.prompts import prompt_templates
from ..data.config_manager import config_manager
from ..utils.json_utils import extract_json_from_text, validate_scene_json

if TYPE_CHECKING:
    from ..integrations.browser_automation import BrowserAutomation

class SceneGenerator:
    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.provider_name = config_manager.get("default_model", "gemini")
        self.provider = get_ai_provider(self.provider_name)
        self.use_browser: bool = bool(
            config_manager.get("scene_generation.use_browser", True),
        )
    
    async def generate_scenes(self, content: str, characters_json: Dict[str, Any], project_name: Optional[str] = None, project_config: Optional[dict] = None, browser: Optional["BrowserAutomation"] = None) -> List[Dict[str, Any]]:
        characters_str = json.dumps(characters_json, ensure_ascii=False, indent=2)
        prompt = prompt_templates.get_content_to_scene(content, characters_str)
        
        gemini_link = None
        if project_config:
            gemini_link = project_config.get("gemini_project_link") or project_config.get("gemini_video_analysis_link")
        
        if self.use_browser:
            web_client = WebContentGenerator(gemini_project_link=gemini_link, browser=browser)
            response_text = await web_client.generate(prompt, project_config)
        else:
            if not self.provider.is_available():
                raise RuntimeError(f"AI provider {self.provider_name} is not available")
            response_text = await self.provider.generate_text(prompt)
        
        project_name = project_name or self.project_name
        from ..utils.response_saver import save_gemini_response
        save_gemini_response(project_name, "scenes", response_text)
        
        try:
            scenes = extract_json_from_text(response_text)
            
            if not isinstance(scenes, list):
                raise ValueError("Scenes must be a list")
            
            if not validate_scene_json(scenes):
                raise ValueError("Invalid scene JSON structure")
            
            return scenes
        except Exception as e:
            raise ValueError(f"Failed to parse scenes JSON: {e}")

