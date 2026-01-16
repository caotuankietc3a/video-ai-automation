import os
import json
from typing import Dict, Any, List, Optional
from ..config.constants import PROMPTS_RESPONSES_DIR, PROJECTS_DIR
from ..utils.json_utils import extract_json_from_text
from .project_manager import project_manager

class DataLoader:
    def __init__(self):
        pass
    
    def load_project_data(self, project_file: str) -> Optional[Dict[str, Any]]:
        if not project_file:
            return None
        
        project = project_manager.load_project(project_file)
        if not project:
            return None
        
        project_name = project.get("name", "default")
        
        data = {
            "project": project,
            "project_name": project_name,
            "characters": project.get("characters", {}),
            "scenes": project.get("scenes", []),
            "prompts": project.get("prompts", []),
            "videos": project.get("videos", []),
            "content": None,
            "video_analysis": None
        }
        
        if not data["characters"]:
            data["characters"] = self._load_characters_from_file(project_name)
        
        if not data["scenes"]:
            data["scenes"] = self._load_scenes_from_file(project_name)
        
        if not data["prompts"]:
            data["prompts"] = self._load_prompts_from_file(project_name)
        
        data["content"] = self._load_content_from_file(project_name)
        data["video_analysis"] = self._load_video_analysis_from_file(project_name)
        
        return data
    
    def _load_characters_from_file(self, project_name: str) -> Dict[str, Any]:
        file_path = os.path.join(PROMPTS_RESPONSES_DIR, project_name, "characters_response.txt")
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return {}
                
                characters_json = extract_json_from_text(content)
                if isinstance(characters_json, dict):
                    return characters_json
        except Exception:
            pass
        
        return {}
    
    def _load_scenes_from_file(self, project_name: str) -> List[Dict[str, Any]]:
        file_path = os.path.join(PROMPTS_RESPONSES_DIR, project_name, "scenes_response.txt")
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return []
                
                scenes = extract_json_from_text(content)
                if isinstance(scenes, list):
                    return scenes
        except Exception:
            pass
        
        return []
    
    def _load_prompts_from_file(self, project_name: str) -> List[str]:
        file_path = os.path.join(PROMPTS_RESPONSES_DIR, project_name, "veo3_prompts_response.txt")
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                
                prompts = content.split("\n\n--- PROMPT SEPARATOR ---\n\n")
                return [p.strip() for p in prompts if p.strip()]
        except Exception:
            pass
        
        return []
    
    def _load_content_from_file(self, project_name: str) -> Optional[str]:
        file_path = os.path.join(PROMPTS_RESPONSES_DIR, project_name, "content.txt")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    
    def _load_video_analysis_from_file(self, project_name: str) -> Optional[str]:
        file_path = os.path.join(PROMPTS_RESPONSES_DIR, project_name, "video_analysis.txt")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

data_loader = DataLoader()

