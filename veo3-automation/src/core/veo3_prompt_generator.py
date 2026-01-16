import json
import logging
from typing import List, Dict, Any, Optional
from ..integrations import get_ai_provider, WebContentGenerator
from ..config.prompts import prompt_templates
from ..data.config_manager import config_manager

logger = logging.getLogger(__name__)

class VEO3PromptGenerator:
    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.provider_name = config_manager.get("default_model", "gemini")
        self.provider = get_ai_provider(self.provider_name)
        self.use_browser: bool = bool(
            config_manager.get("veo3_prompt_generation.use_browser", True),
        )
        self.web_client: Optional[WebContentGenerator]
        if self.use_browser:
            self.web_client = WebContentGenerator()
        else:
            self.web_client = None
    
    async def generate_prompts(self, scenes: List[Dict[str, Any]], 
                              characters_json: Dict[str, Any], project_name: Optional[str] = None, project_config: Optional[dict] = None) -> List[str]:
        characters_str = json.dumps(characters_json, ensure_ascii=False, indent=2)
        prompts = []
        
        previous_scene = None
        for i, scene in enumerate(scenes, 1):
            scene_str = json.dumps(scene, ensure_ascii=False, indent=2)
            
            if previous_scene:
                previous_scene_str = json.dumps(previous_scene, ensure_ascii=False, indent=2)
                prompt = prompt_templates.get_scene_to_veo3(scene_str, characters_str)
                prompt += f"\n\nPrevious scene context:\n{previous_scene_str}"
            else:
                prompt = prompt_templates.get_scene_to_veo3(scene_str, characters_str)
            
            logger.info(f"Đang tạo VEO3 prompt cho scene {i}/{len(scenes)}...")
            
            if self.use_browser and self.web_client is not None:
                veo3_prompt = await self.web_client.generate(prompt, project_config)
                prompts.append(veo3_prompt.strip())
            else:
                if not self.provider.is_available():
                    raise RuntimeError(f"AI provider {self.provider_name} is not available")
                veo3_prompt = await self.provider.generate_text(prompt)
                prompts.append(veo3_prompt.strip())
            
            previous_scene = scene
        
        project_name = project_name or self.project_name
        from ..utils.response_saver import save_gemini_response
        prompts_text = "\n\n--- PROMPT SEPARATOR ---\n\n".join(prompts)
        save_gemini_response(project_name, "veo3_prompts", prompts_text)
        
        return prompts

