import aiohttp
from typing import List, Optional
from .ai_providers import AIProvider
from ..data.config_manager import config_manager

class LocalAIClient(AIProvider):
    def __init__(self):
        self.api_url = config_manager.get("api_keys.local_api_url", "http://localhost:11434")
        self.model = "llama2"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Local AI API not available")
        
        model = kwargs.get("model", self.model)
        url = f"{self.api_url}/api/generate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "")
                else:
                    raise Exception(f"Local AI API error: {response.status}")
    
    async def generate_with_images(self, prompt: str, image_paths: List[str], **kwargs) -> str:
        return await self.generate_text(prompt, **kwargs)
    
    def is_available(self) -> bool:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return True
            else:
                result = loop.run_until_complete(self._check_availability())
                return result
        except:
            return False
    
    async def _check_availability(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    return response.status == 200
        except:
            return False

