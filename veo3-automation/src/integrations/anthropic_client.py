import os
from anthropic import AsyncAnthropic
from typing import List, Optional
from .ai_providers import AIProvider, encode_image
from ..data.config_manager import config_manager

class AnthropicClient(AIProvider):
    def __init__(self):
        api_key = config_manager.get_api_key("anthropic")
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None
        self.model = "claude-3-opus-20240229"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        model = kwargs.get("model", self.model)
        response = await self.client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    async def generate_with_images(self, prompt: str, image_paths: List[str], **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        model = kwargs.get("model", "claude-3-opus-20240229")
        
        content = [{"type": "text", "text": prompt}]
        
        for img_path in image_paths:
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    image_data = f.read()
                    import base64
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    })
        
        response = await self.client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[
                {"role": "user", "content": content}
            ]
        )
        return response.content[0].text
    
    def is_available(self) -> bool:
        return self.client is not None

