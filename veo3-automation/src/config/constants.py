import os

APP_NAME = "GOOGLE AI VEO3 ULTRA PLUS"
APP_VERSION = "1.0.0"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROJECTS_DIR = os.path.join(DATA_DIR, "projects")
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
PROMPTS_RESPONSES_DIR = os.path.join(DATA_DIR, "prompts")

VIDEO_STYLES = [
    "3d_Pixar",
    "anime_2d",
    "cinematic",
    "live_action"
]

VEO_PROFILES = [
    "VEO3",
    "VEO3 ULTRA",
    "VEO3.1",
    "VEO3.1 Fast"
]

ASPECT_RATIOS = [
    "Khổ ngang (16:9)",
    "Khổ dọc (9:16)",
    "Khổ vuông (1:1)"
]

AI_MODELS = {
    "gemini": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro"],
    "openai": ["gpt-4", "gpt-4-vision-preview", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
    "local": ["llama2", "mistral", "codellama"]
}

