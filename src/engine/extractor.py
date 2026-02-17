import json
import time
import os
from typing import List, Optional, Dict, Any
from groq import Groq
from loguru import logger
from ..config import settings
from ..schemas import ExtractionResult
from ..prompts import PROMPTS

class ShipmentExtractor:
    """
    Core AI Engine for the Shipment Extraction System.
    Handles LLM communication, context management, and reliability protocols.
    """
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL_NAME
        self.version = settings.PROMPT_VERSION
        self.port_reference = self._load_port_reference()
        
    def _load_port_reference(self) -> str:
        path = settings.PORT_CODES_REFERENCE_PATH
        if not os.path.exists(path):
            logger.warning(f"Port Reference Data not found at {path}. System fidelity might be limited.")
            return "No reference data loaded."
            
        try:
            with open(path, "r", encoding='utf-8') as f:
                data = json.load(f)
                context_parts = []
                for item in data:
                    base = f"{item['code']}:{item['name']}"
                    aliases = item.get("aliases", [])
                    aliases = [a for a in aliases if a.lower() != item['name'].lower()]
                    if aliases:
                        base += f"[{'/'.join(aliases)}]"
                    context_parts.append(base)
                return ", ".join(context_parts)
        except Exception as e:
            logger.error(f"Integrity Error: Failed to parse port reference: {e}")
            return "Error loading reference data."

    def extract_from_content(self, content: str, retries: int = 3) -> Dict[str, Any]:
        template = PROMPTS.get(self.version, PROMPTS["v6"])
        system_prompt = template.format(port_reference=self.port_reference, user_input="{user_input}").replace("{user_input}", content)
        
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                wait = (attempt + 1) * 5
                logger.warning(f"LLM API Transient Error ({attempt+1}/{retries}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
        
        return {}

    def process_item(self, email_data: Dict[str, Any]) -> ExtractionResult:
        email_id = email_data.get("id", "UNKN")
        content = f"Subject: {email_data.get('subject', '')}\nBody: {email_data.get('body', '')}"
        
        try:
            raw_data = self.extract_from_content(content)
            if isinstance(raw_data, list): raw_data = raw_data[0] if raw_data else {}
            raw_data['id'] = email_id
            return ExtractionResult(**raw_data)
        except Exception as e:
            logger.error(f"Extraction failed for {email_id}: {e}")
            return ExtractionResult(id=email_id)
