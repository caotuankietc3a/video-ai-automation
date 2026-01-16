import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..config.constants import PROJECTS_DIR

class ProjectManager:
    def __init__(self):
        os.makedirs(PROJECTS_DIR, exist_ok=True)
    
    def list_projects(self) -> List[str]:
        if not os.path.exists(PROJECTS_DIR):
            return []
        
        files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith('.json')]
        return sorted(files)
    
    def load_project(self, project_file: str) -> Optional[Dict[str, Any]]:
        project_path = os.path.join(PROJECTS_DIR, project_file)
        if not os.path.exists(project_path):
            return None
        
        with open(project_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_project(self, project_data: Dict[str, Any]) -> str:
        project_name = project_data.get('name', f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        project_file = project_data.get('file', f"{len(self.list_projects()) + 1}. {project_name}.json")
        
        if not project_file.endswith('.json'):
            project_file += '.json'
        
        project_path = os.path.join(PROJECTS_DIR, project_file)
        
        project_data['file'] = project_file
        project_data['updated_at'] = datetime.now().isoformat()
        
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        return project_file
    
    def create_project(self, name: str, **kwargs) -> Dict[str, Any]:
        project_data = {
            'name': name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'style': kwargs.get('style', '3d_Pixar'),
            'duration': kwargs.get('duration', 120),
            'veo_profile': kwargs.get('veo_profile', 'VEO3 ULTRA'),
            'model': kwargs.get('model', 'Veo 3.1 - Fast'),
            'aspect_ratio': kwargs.get('aspect_ratio', 'Khổ ngang (16:9)'),
            'num_outputs': kwargs.get('num_outputs', 1),
            'ambience_fx': kwargs.get('ambience_fx', True),
            'fixed_camera': kwargs.get('fixed_camera', False),
            'background_music': kwargs.get('background_music', True),
            'illustration_cues': kwargs.get('illustration_cues', False),
            'script': kwargs.get('script', ''),
            'run_type': kwargs.get('run_type', 'Text to Video API'),
            'ai_model': kwargs.get('ai_model', 'VEO3 ULTRA'),
            'dialogue_language': kwargs.get('dialogue_language', 'en-US'),
            'project_link': kwargs.get('project_link', ''),
            'gemini_project_link': kwargs.get('gemini_project_link', ''),
            'chatgpt_training_link': kwargs.get('chatgpt_training_link', ''),
            'characters': {},
            'scenes': [],
            'prompts': [],
            'videos': [],
            'status': 'draft'
        }
        
        project_file = self.save_project(project_data)
        project_data['file'] = project_file
        return project_data
    
    def copy_project(self, source_file: str, new_name: str) -> Optional[str]:
        source_project = self.load_project(source_file)
        if not source_project:
            return None
        
        source_project['name'] = new_name
        source_project['created_at'] = datetime.now().isoformat()
        source_project.pop('file', None)
        
        new_file = self.save_project(source_project)
        return new_file
    
    def delete_project(self, project_file: str) -> bool:
        project_path = os.path.join(PROJECTS_DIR, project_file)
        if os.path.exists(project_path):
            os.remove(project_path)
            return True
        return False
    
    def update_project(self, project_file: str, updates: Dict[str, Any]) -> bool:
        project = self.load_project(project_file)
        if not project:
            return False
        
        project.update(updates)
        self.save_project(project)
        return True

project_manager = ProjectManager()

