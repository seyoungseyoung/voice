"""
Configuration management for Sentinel-Voice
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
ROOT_DIR = Path(__file__).parent.parent


class APIConfig(BaseModel):
    """API Configuration"""
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    naver_client_id: str = os.getenv("NAVER_CLIENT_ID", "")
    naver_client_secret: str = os.getenv("NAVER_CLIENT_SECRET", "")
    clova_api_key: str = os.getenv("CLOVA_API_KEY", "")


class ModelConfig(BaseModel):
    """Model Configuration"""
    whisper_model_path: str = os.getenv("WHISPER_MODEL_PATH", "models/whisper")
    kobert_model_path: str = os.getenv("KOBERT_MODEL_PATH", "models/kobert")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "data/vector_db")


class ServerConfig(BaseModel):
    """Server Configuration"""
    host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    port: int = int(os.getenv("SERVER_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"


class SecurityConfig(BaseModel):
    """Security Configuration"""
    pii_masking_enabled: bool = os.getenv("PII_MASKING_ENABLED", "True").lower() == "true"
    min_call_duration: int = int(os.getenv("MIN_CALL_DURATION", "30"))


class RiskScoringConfig(BaseModel):
    """Risk Scoring Configuration"""
    keyword_weight: float = float(os.getenv("KEYWORD_WEIGHT", "0.3"))
    sentiment_weight: float = float(os.getenv("SENTIMENT_WEIGHT", "0.3"))
    similarity_weight: float = float(os.getenv("SIMILARITY_WEIGHT", "0.4"))
    risk_threshold: int = int(os.getenv("RISK_THRESHOLD", "70"))


class Config:
    """Main Configuration"""
    def __init__(self):
        self.api = APIConfig()
        self.model = ModelConfig()
        self.server = ServerConfig()
        self.security = SecurityConfig()
        self.risk_scoring = RiskScoringConfig()

    @property
    def data_dir(self) -> Path:
        return ROOT_DIR / "data"

    @property
    def model_dir(self) -> Path:
        return ROOT_DIR / "models"

    @property
    def log_dir(self) -> Path:
        return ROOT_DIR / "logs"


# Global config instance
config = Config()
