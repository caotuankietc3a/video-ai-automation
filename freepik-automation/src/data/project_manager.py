from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.constants import PROJECTS_DIR


class ProjectManager:
    def __init__(self) -> None:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> List[str]:
        if not PROJECTS_DIR.exists():
            return []
        files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith(".json")]
        return sorted(files)

    def load_project(self, project_file: str) -> Optional[Dict[str, Any]]:
        project_path = PROJECTS_DIR / project_file
        if not project_path.exists():
            return None
        with project_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save_project(self, project_data: Dict[str, Any]) -> str:
        project_name = project_data.get("name", f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        project_file = project_data.get("file", f"{len(self.list_projects()) + 1}. {project_name}.json")

        if not project_file.endswith(".json"):
            project_file += ".json"

        project_path = PROJECTS_DIR / project_file

        project_data["file"] = project_file
        project_data["updated_at"] = datetime.now().isoformat()

        with project_path.open("w", encoding="utf-8") as file:
            json.dump(project_data, file, indent=2, ensure_ascii=False)

        return project_file

    def create_project(
        self,
        name: str,
        idol_image: str,
        dance_video: str,
        mode: str = "prompt_only",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        project_data: Dict[str, Any] = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "idol_image": idol_image,
            "dance_video": dance_video,
            "mode": mode,
            "kling_prompt": kwargs.get("kling_prompt", ""),
            "kling_data": kwargs.get("kling_data"),
            "status": kwargs.get("status", "draft"),
        }

        project_file = self.save_project(project_data)
        project_data["file"] = project_file
        return project_data

    def update_project(self, project_file: str, updates: Dict[str, Any]) -> bool:
        project = self.load_project(project_file)
        if not project:
            return False
        project.update(updates)
        self.save_project(project)
        return True


project_manager = ProjectManager()
