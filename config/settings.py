"""Application settings and configuration management."""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
env_path = BASE_DIR / 'config' / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from root
    load_dotenv()


class Settings:
    """Application settings loaded from environment variables and config files."""
    
    # Instagram credentials
    INSTAGRAM_USERNAME: str = os.getenv('INSTAGRAM_USERNAME', '')
    INSTAGRAM_PASSWORD: str = os.getenv('INSTAGRAM_PASSWORD', '')
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/data/smm_analise.db')
    
    # Application
    APP_ENV: str = os.getenv('APP_ENV', 'production')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Dashboard
    DASHBOARD_HOST: str = os.getenv('DASHBOARD_HOST', '0.0.0.0')
    DASHBOARD_PORT: int = int(os.getenv('DASHBOARD_PORT', '5000'))
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change_this_to_random_secret_key')
    
    # Scheduling
    TIMEZONE: str = os.getenv('TIMEZONE', 'Europe/Kyiv')
    DATA_COLLECTION_INTERVAL: int = int(os.getenv('DATA_COLLECTION_INTERVAL', '3600'))
    DAILY_REPORT_TIME: str = os.getenv('DAILY_REPORT_TIME', '20:00')
    WEEKLY_REPORT_DAY: int = int(os.getenv('WEEKLY_REPORT_DAY', '0'))
    WEEKLY_REPORT_TIME: str = os.getenv('WEEKLY_REPORT_TIME', '09:00')
    MONTHLY_REPORT_TIME: str = os.getenv('MONTHLY_REPORT_TIME', '09:00')
    
    # Backup
    BACKUP_ENABLED: bool = os.getenv('BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_RETENTION_DAYS: int = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
    
    # Paths
    DATA_DIR: Path = BASE_DIR / 'data'
    LOGS_DIR: Path = BASE_DIR / 'logs'
    BACKUPS_DIR: Path = BASE_DIR / 'backups'
    
    # Targets configuration
    _targets_config: Dict[str, Any] = None
    
    @classmethod
    def load_targets(cls) -> Dict[str, Any]:
        """Load targets configuration from YAML file."""
        if cls._targets_config is None:
            targets_path = BASE_DIR / 'config' / 'targets.yaml'
            if targets_path.exists():
                with open(targets_path, 'r', encoding='utf-8') as f:
                    cls._targets_config = yaml.safe_load(f)
            else:
                cls._targets_config = {}
        return cls._targets_config
    
    @classmethod
    def get_target(cls, key: str, default: Any = None) -> Any:
        """Get a specific target value."""
        targets = cls.load_targets()
        keys = key.split('.')
        value = targets
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate required settings and return list of errors."""
        errors = []
        
        if not cls.INSTAGRAM_USERNAME:
            errors.append("INSTAGRAM_USERNAME is required")
        if not cls.INSTAGRAM_PASSWORD:
            errors.append("INSTAGRAM_PASSWORD is required")
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required")
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
            
        return errors
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


# Create singleton instance
settings = Settings()
