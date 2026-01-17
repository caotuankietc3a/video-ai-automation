import os
import google.genai as genai
from typing import List, Optional
from .ai_providers import AIProvider
from ..data.config_manager import config_manager

class GeminiClient(AIProvider):
    def __init__(self):
        api_key = config_manager.get_api_key("gemini")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
        self.model_name = "gemini-1.5-pro"
        self.vision_model_name = "gemini-1.5-pro"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key not configured")
        
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
        )
        return response.text
    
    async def generate_with_images(self, prompt: str, image_paths: List[str], **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key not configured")
        
        import asyncio
        from google.genai import types
        
        parts = [types.Part.from_text(text=prompt)]
        
        for img_path in image_paths:
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    image_data = f.read()
                parts.append(types.Part.from_bytes(
                    data=image_data,
                    mime_type=self._get_mime_type(img_path)
                ))
        
        if len(parts) == 1:
            return await self.generate_text(prompt, **kwargs)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.vision_model_name,
                contents=parts
            )
        )
        return response.text
    
    def _get_mime_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def is_available(self) -> bool:
        return self.client is not None

