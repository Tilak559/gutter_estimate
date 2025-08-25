import pydantic_settings
from typing import List
import os

class config(pydantic_settings.BaseSettings):
    # Google API Configuration
    google_api_key: str = ""
    project_id: str = ""
    google_credentials_path: str = ""
    google_scopes: str = ""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"

config = config()
