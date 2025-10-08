import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Define the logs directory
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
LOG_FILE = LOGS_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Also log to console
    ]
)
logger = logging.getLogger("ImportExportIntelligence")

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENAI_API_KEY: str
    GOOGLE_CSE_API_KEY: str
    GOOGLE_CSE_CX: str

# Instantiate settings
settings = Settings()

logger.info("Configuration loaded successfully.")