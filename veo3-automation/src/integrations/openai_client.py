import os
from openai import AsyncOpenAI
from typing import List, Optional
from .ai_providers import AIProvider, encode_image
from ..data.config_manager import config_manager

class OpenAIClient(AIProvider):
    def __init__(self):
        api_key = config_manager.get_api_key("openai")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        model = kwargs.get("model", self.model)
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            **{k: v for k, v in kwargs.items() if k != "model"}
        )
        return response.choices[0].message.content
    
    async def generate_with_images(self, prompt: str, image_paths: List[str], **kwargs) -> str:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        model = kwargs.get("model", "gpt-4-vision-preview")
        
        content = [{"type": "text", "text": prompt}]
        
        for img_path in image_paths:
            if os.path.exists(img_path):
                base64_image = encode_image(img_path)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": content}
            ],
            **{k: v for k, v in kwargs.items() if k != "model"}
        )
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return self.client is not None

