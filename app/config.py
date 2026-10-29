"""Application configuration; secrets never belong in source control."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / '.env'), extra='ignore')
    app_name: str = 'SalesGenie AI'
    database_url: str = f'sqlite:///{ROOT / "salesgenie.db"}'
    cors_origins: str = 'http://localhost:8501,http://127.0.0.1:8501'
    llm_provider: str = 'mock'
    llm_api_key: str = ''
    llm_model: str = 'gpt-4o-mini'
    llm_api_url: str = 'https://api.openai.com/v1/chat/completions'
    model_path: str = str(ROOT / 'artifacts' / 'conversion_model.joblib')
    metrics_path: str = str(ROOT / 'artifacts' / 'model_metrics.json')
    max_csv_bytes: int = 5_000_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
