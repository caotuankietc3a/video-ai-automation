from .ai_providers import AIProvider
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .local_ai_client import LocalAIClient
from .web_content_generator import WebContentGenerator


def get_ai_provider(provider_name: str) -> AIProvider:
    if provider_name == "gemini":
        return GeminiClient()
    elif provider_name == "openai":
        return OpenAIClient()
    elif provider_name == "anthropic":
        return AnthropicClient()
    if provider_name == "local":
        return LocalAIClient()
    raise ValueError(f"Unknown provider: {provider_name}")


