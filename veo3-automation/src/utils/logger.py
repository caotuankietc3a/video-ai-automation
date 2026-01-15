import os
import json
from datetime import datetime
from typing import Dict, Any, List
from ..config.constants import LOGS_DIR

class Logger:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.log_file = os.path.join(LOGS_DIR, f"{project_name}_{datetime.now().strftime('%Y%m%d')}.json")
        os.makedirs(LOGS_DIR, exist_ok=True)
        self.logs: List[Dict[str, Any]] = []
        self._load_logs()
    
    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                self.logs = []
    
    def _save_logs(self):
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
    
    def log(self, level: str, message: str, data: Dict[str, Any] = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        self.logs.append(log_entry)
        self._save_logs()
    
    def info(self, message: str, data: Dict[str, Any] = None):
        self.log("INFO", message, data)
    
    def error(self, message: str, data: Dict[str, Any] = None):
        self.log("ERROR", message, data)
    
    def warning(self, message: str, data: Dict[str, Any] = None):
        self.log("WARNING", message, data)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs

