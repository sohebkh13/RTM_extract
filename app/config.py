from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # AI Configuration - Groq Only
    GROQ_API_KEY: str = ""
    VITE_GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "gemma2-9b-it"  # Correct model name with dots
    GROQ_FALLBACK_MODEL: str = "llama-3.1-8b-instant"  # Fallback when primary model hits limits
    AI_MAX_TOKENS: int = 8000
    AI_TEMPERATURE: float = 0.1
    
    # Legacy fields (ignored)
    VITE_GOOGLE_AI_API_KEY: str = ""  # Ignored - for backward compatibility
    
    # Token Management
    MAX_TOKENS_PER_CHUNK: int = 4800  # Reduced to avoid API limits with buffer
    TOKEN_OVERLAP: int = 200  # Slightly increased overlap for better context
    GROQ_REQUESTS_PER_MINUTE: int = 35  # Slightly more aggressive rate limiting
    GROQ_DAILY_TOKEN_LIMIT: int = 500000
    GROQ_DAILY_REQUEST_LIMIT: int = 14400
    
    # File Configuration  
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ['.xlsx', '.xls']
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    # Processing Configuration
    FOCUS_SHEET_NAME: str = "2- tool Requirements"
    REQUIREMENT_ID_PREFIX: str = "REQ"
    TEST_CASE_ID_PREFIX: str = "TC"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Use VITE_ prefixed keys if main keys are empty
        if not self.GROQ_API_KEY and self.VITE_GROQ_API_KEY:
            self.GROQ_API_KEY = self.VITE_GROQ_API_KEY
            
        # Create directories if they don't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

settings = Settings()
