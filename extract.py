import os
import json
import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from schemas import ExtractionResult
from prompts import PROMPTS

# Professional Logging Setup
# We use a clean format that's easy to read in cloud logs (like CloudWatch or Datadog)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ShipmentExtractor")

class ExtractionError(Exception):
    """Custom exception for extraction failures."""
    pass

class ShipmentExtractor:
    """
    An enterprise-grade extractor that uses LLMs (via Groq) to parse 
    complex logistics emails into structured shipment data.
    """
    def __init__(self, api_key: Optional[str] = None):
        # Configuration is hydrated from environment variables for scalability
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Cloud Configuration Error: GROQ_API_KEY is missing from environment.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
        self.version = os.getenv("PROMPT_VERSION", "v5")
        
        # Rate limit safety: we default to a conservative 5s for the 70B model 
        # but this can be tuned via SLEEP_TIME in .env
        self.sleep_time = float(os.getenv("SLEEP_TIME", "5.0"))
        
        # Load the port mapping context to inject into the LLM system prompt
        self.port_reference = self._load_port_reference()
        
        logger.info(f"Initialized Extractor [Model: {self.model} | Version: {self.version}]")

    def _load_port_reference(self) -> str:
        """
        Loads port reference data into a compact string format.
        This maximizes context density within the LLM's system prompt.
        """
        path = os.getenv("PORT_CODES_REFERENCE_PATH", "data/port_codes_reference.json")
        
        # Smart path resolution for different environments
        if not os.path.exists(path):
            path = "port_codes_reference.json" if os.path.exists("port_codes_reference.json") else path
            
        if not os.path.exists(path):
            logger.warning(f"Port Reference Missing: Tried '{path}'. Proceeding with empty context.")
            return "No reference data available."
            
        try:
            with open(path, "r", encoding='utf-8') as f:
                data = json.load(f)
                # Format: CODE:Name[Alias1/Alias2],CODE:Name[Alias1/Alias2]
                context_parts = []
                for item in data:
                    base = f"{item['code']}:{item['name']}"
                    aliases = item.get("aliases", [])
                    # Filter out the canonical name if it's in aliases to save space
                    aliases = [a for a in aliases if a.lower() != item['name'].lower()]
                    
                    if aliases:
                        alias_str = "/".join(aliases)
                        base += f"[{alias_str}]"
                    context_parts.append(base)
                    
                return ", ".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to parse port reference: {e}")
            return "Reference data corrupted."

    def _call_llm(self, user_content: str, retries: int = 3) -> Dict[str, Any]:
        """
        Handles the core LLM communication with a retry mechanism and 
        exponential backoff to survive rate limits.
        """
        # Select the prompt blueprint from our versioned registry
        template = PROMPTS.get(self.version, PROMPTS["v5"])
        
        # Compile the system prompt with active context
        system_prompt = template.format(
            port_reference=self.port_reference, 
            user_input="{user_input}"
        ).replace("{user_input}", user_content)
        
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0,  # Zero temperature is non-negotiable for reproducible data extraction
                    response_format={"type": "json_object"}
                )
                
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise ExtractionError("Upstream LLM returned an empty payload.")
                
                return json.loads(raw_content)

            except Exception as e:
                err_msg = str(e).lower()
                # If we hit a 429 (Rate Limit), we back off properly
                is_rate_limit = "rate_limit" in err_msg or "429" in err_msg
                wait = (attempt + 1) * 20 if is_rate_limit else (attempt + 1) * 5
                
                logger.warning(f"[Attempt {attempt + 1}] LLM communication error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        
        raise ExtractionError(f"Extraction failed after {retries} attempts.")

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
        """
        Executes a batch processing job with built-in checkpointing 
        and resume capabilities.
        """
        if not os.path.exists(input_path):
            logger.error(f"Operational Error: Input source '{input_path}' not found.")
            return

        with open(input_path, "r", encoding='utf-8') as f:
            emails = json.load(f)

        # Resume logic: we look at existing results to avoid double-billing on API calls
        results = []
        processed_ids = set()
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding='utf-8') as f:
                    results = json.load(f)
                    processed_ids = {item["id"] for item in results if item.get("id")}
                logger.info(f"Resume detected: Skipping {len(processed_ids)} already processed records.")
            except Exception:
                logger.info("Starting fresh extraction (no valid resume file found).")

        total_count = len(emails)
        logger.info(f"Starting extraction pipeline for {total_count} emails.")

        try:
            for i, email in enumerate(emails):
                email_id = email.get('id', 'N/A')
                
                if email_id in processed_ids:
                    continue
                
                # Progress logging for monitoring long-running jobs
                logger.info(f"Processing ({i+1}/{total_count}): {email_id}")
                
                result = self.process_email(email)
                
                if result.reasoning:
                    logger.debug(f"LLM Reasoning: {result.reasoning}")
                
                results.append(result.model_dump())
                
                # Checkpointed save after every extraction to prevent data loss
                with open(output_path, "w", encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                
                # Adaptive sleep to respect API throttling
                time.sleep(self.sleep_time)

        except KeyboardInterrupt:
            logger.warning("Batch process interrupted by operator.")
        except Exception as e:
            logger.critical(f"FATAL: Extraction pipeline collapsed: {e}")
        finally:
            # Final safe-save
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Batch complete. Results persisted to '{output_path}'.")

if __name__ == "__main__":
    load_dotenv()
    
    input_file = os.getenv("INPUT_PATH", "data/emails_input.json")
    output_file = os.getenv("OUTPUT_PATH", "output_v5.json")
    
    extractor = ShipmentExtractor()
    
    extractor.run_batch(
        input_path=input_file, 
        output_path=output_file
    )
