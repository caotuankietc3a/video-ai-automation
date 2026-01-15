from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import base64

class AIProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_with_images(self, prompt: str, image_paths: List[str], **kwargs) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

