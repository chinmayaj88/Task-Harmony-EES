from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseConnector(ABC):
    """Base class for data ingestion connectors."""
    
    @abstractmethod
    def fetch_emails(self) -> List[Dict[str, Any]]:
        """Fetches raw email data (ID, Subject, Body)."""
        pass
