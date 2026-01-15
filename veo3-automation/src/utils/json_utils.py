import json
import re
from typing import Any, Dict, List

def extract_json_from_text(text: str) -> Dict[str, Any]:
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    raise ValueError("No valid JSON found in text")

def validate_character_json(data: Dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False
    
    for char_id, char_data in data.items():
        if not char_id.startswith("CHAR_"):
            return False
        
        required_fields = ["id", "name", "species", "appearance", "outfit", "personality"]
        for field in required_fields:
            if field not in char_data:
                return False
    
    return True

def validate_scene_json(data: List[Dict[str, Any]]) -> bool:
    if not isinstance(data, list):
        return False
    
    for scene in data:
        required_fields = ["scene_id", "duration_sec", "visual_style", "background_lock", 
                          "camera", "character_lock", "mood"]
        for field in required_fields:
            if field not in scene:
                return False
    
    return True

def parse_content_sections(content: str) -> Dict[str, str]:
    sections = {
        "characters": "",
        "story": "",
        "storyboard": ""
    }
    
    if "PHẦN A" in content:
        parts = re.split(r'PHẦN [ABC]\.', content)
        if len(parts) >= 2:
            sections["characters"] = parts[1].strip()
        if len(parts) >= 3:
            sections["story"] = parts[2].strip()
        if len(parts) >= 4:
            sections["storyboard"] = parts[3].strip()
    
    return sections

