import os
import google.generativeai as genai
from typing import List, Optional
from PIL import Image
from .ai_providers import AIProvider, encode_image
from ..data.config_manager import config_manager

class GeminiClient(AIProvider):
    def __init__(self):
        api_key = config_manager.get_api_key("gemini")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = None
        self.vision_model = None
    
    def _get_model(self):
        if not self.model:
            self.model = genai.GenerativeModel('gemini-pro')
        return self.model
    
    def _get_vision_model(self):
        if not self.vision_model:
            self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        return self.vision_model
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key not configured")
        
        import asyncio
        model = self._get_model()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        return response.text
    
    async def generate_with_images(self, prompt: str, image_paths: List[str], **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key not configured")
        
        import asyncio
        model = self._get_vision_model()
        
        images = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                img = Image.open(img_path)
                images.append(img)
        
        if not images:
            return await self.generate_text(prompt, **kwargs)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content([prompt] + images))
        return response.text
    
    def is_available(self) -> bool:
        api_key = config_manager.get_api_key("gemini")
        return bool(api_key)

