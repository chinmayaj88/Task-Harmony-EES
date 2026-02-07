import os
import json
import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from schemas import ExtractionResult
from prompts import v4_prompt

# Advanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ShipmentExtractor")

class ExtractionError(Exception):
    """Custom exception for extraction failures."""
    pass

class ShipmentExtractor:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"): #"llama-3.3-70b-versatile"
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.sleep_time = 5.0  # Conservative sleep for 70B rate limits
        self.port_reference = self._load_port_reference()

    def _load_port_reference(self) -> str:
        """Loads port reference data in a compact string format to save tokens."""
        possible_paths = ["port_codes_reference.json", "data/port_codes_reference.json"]
        path = next((p for p in possible_paths if os.path.exists(p)), None)
        if not path:
            return "No reference data available."
        with open(path, "r", encoding='utf-8') as f:
            data = json.load(f)
            return ",".join([f"{item['code']}:{item['name']}" for item in data])

    def _call_llm(self, user_content: str, retries: int = 3) -> Dict[str, Any]:
        """Core LLM call logic with exponential backoff and temperature=0."""
        # Inject context into the template
        system_prompt = v4_prompt.format(port_reference=self.port_reference, user_input="{user_input}")
        
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt.replace("{user_input}", user_content)},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0, # Mandatory for reproducibility
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise ExtractionError("LLM returned an empty response.")
                
                return json.loads(content)

            except Exception as e:
                err_msg = str(e).lower()
                wait = (attempt + 1) * 20 if "rate_limit" in err_msg or "429" in err_msg else (attempt + 1) * 5
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        
        raise ExtractionError(f"Failed after {retries} retries.")

    def process_email(self, email: Dict[str, Any]) -> ExtractionResult:
        """Processes a single email and returns a validated result."""
        email_id = email.get("id", "UNKNOWN")
        subject = email.get("subject", "")
        body = email.get("body", "")
        
        # Structure as expected by the prompt
        content = f"Subject: {subject}\nBody: {body}"

        try:
            raw_data = self._call_llm(content)
            
            # Handle list returns if any
            if isinstance(raw_data, list):
                raw_data = raw_data[0] if raw_data else {}

            raw_data['id'] = email_id
            return ExtractionResult(**raw_data)
        except Exception as e:
            logger.error(f"Error processing {email_id}: {str(e)}")
            # Fallback for failed extractions: null fields as per instructions
            return ExtractionResult(id=email_id)

    def run_batch(self, input_path: str, output_path: str):
        """Processes emails with resume capability and incremental saving."""
        if not os.path.exists(input_path):
            logger.error(f"Input file not found at {input_path}")
            return

        emails = []
        with open(input_path, "r", encoding='utf-8') as f:
            emails = json.load(f)

        # Resume logic
        results = []
        processed_ids = set()
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding='utf-8') as f:
                    results = json.load(f)
                    processed_ids = {item["id"] for item in results if item.get("id")}
                logger.info(f"Resuming. Skipping {len(processed_ids)} already processed.")
            except: pass

        logger.info(f"Processing {len(emails)} emails...")

        try:
            for i, email in enumerate(emails):
                email_id = email.get('id')
                if email_id in processed_ids:
                    continue
                
                logger.info(f"[{i+1}/{len(emails)}] {email_id}")
                result = self.process_email(email)
                if result.reasoning:
                    logger.info(f"Reasoning: {result.reasoning}")
                results.append(result.model_dump())
                
                # Checkpointed save
                with open(output_path, "w", encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                
                time.sleep(self.sleep_time)
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
        finally:
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    # CONFIGURATION: Choose version (v1, v2, v3, v4)
    VERSION = "v4" 
    
    extractor = ShipmentExtractor(prompt_version=VERSION)
    
    # MISSION: Extract 50 emails and save to root 'output.json' for assessment submission
    # The system will automatically resume if the file exists!
    extractor.run_batch(
        input_path="data/emails_input.json", 
        output_path="output.json"
    )
