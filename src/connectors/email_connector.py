from typing import List, Dict, Any, Optional
from imap_tools import MailBox, AND
from .base import BaseConnector
from loguru import logger

class EmailConnector(BaseConnector):
    """
    Production-grade connector for fetching real emails via IMAP.
    Requires EMAIL_HOST, EMAIL_USER, and EMAIL_PASS in environment.
    """
    
    def __init__(self, host: str, user: str, password: str, folder: str = "INBOX"):
        self.host = host
        self.user = user
        self.password = password
        self.folder = folder
        
    def fetch_emails(self, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Connecting to email server {self.host} for user {self.user}...")
        emails = []
        try:
            with MailBox(self.host).login(self.user, self.password, self.folder) as mailbox:
                # Fetch recent unseen emails or just limit count for demo
                for msg in mailbox.fetch(AND(all=True), limit=limit, reverse=True):
                    emails.append({
                        "id": f"email_{msg.uid}",
                        "subject": msg.subject,
                        "body": msg.text or msg.html
                    })
            logger.info(f"Successfully fetched {len(emails)} emails from cloud server.")
            return emails
        except Exception as e:
            logger.error(f"Email Connection Error: {e}")
            return []
