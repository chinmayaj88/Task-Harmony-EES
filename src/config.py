from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GROQ_API_KEY: str
    MODEL_NAME: str = "llama-3.1-8b-instant"
    PROMPT_VERSION: str = "v6"
    SLEEP_TIME: float = 1.0
    
    # Email Settings
    EMAIL_HOST: Optional[str] = None
    EMAIL_USER: Optional[str] = None
    EMAIL_PASS: Optional[str] = None
    EMAIL_FOLDER: str = "INBOX"
    
    # Path Settings
    PORT_CODES_REFERENCE_PATH: str = "data/port_codes_reference.json"
    INPUT_PATH: str = "data/emails_input.json"
    OUTPUT_PATH: str = "outputs/output_v6.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
