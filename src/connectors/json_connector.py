import json
from typing import List, Dict, Any
from .base import BaseConnector
from loguru import logger

class JSONConnector(BaseConnector):
    """Connector for reading emails from a JSON file (standard batch processing)."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def fetch_emails(self) -> List[Dict[str, Any]]:
        logger.info(f"Loading emails from JSON source: {self.file_path}")
        try:
            with open(self.file_path, "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON emails: {e}")
            return []
