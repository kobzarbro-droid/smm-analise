"""Configuration management for SMM Analytics System."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml


# Load environment variables from .env file
BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings:
    """Application settings loaded from environment variables."""
    
    # Instagram settings
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/smm_analise.db")
    
    # Dashboard settings
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    DASHBOARD_HOST: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "5000"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    CONFIG_DIR: Path = BASE_DIR / "config"
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    BACKUPS_DIR: Path = BASE_DIR / "backups"
    
    # Application constants
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    RATE_LIMIT_DELAY: int = 2
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.BACKUPS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load_targets(cls) -> Dict[str, Any]:
        """Load targets configuration from YAML file."""
        targets_file = cls.CONFIG_DIR / "targets.yaml"
        if not targets_file.exists():
            raise FileNotFoundError(f"Targets file not found: {targets_file}")
        
        with open(targets_file, "r") as f:
            return yaml.safe_load(f)
    
    @classmethod
    def validate(cls) -> None:
        """Validate required settings."""
        errors = []
        warnings = []
        
        # Check required Instagram credentials
        if not cls.INSTAGRAM_USERNAME:
            errors.append("INSTAGRAM_USERNAME is required")
        if not cls.INSTAGRAM_PASSWORD:
            errors.append("INSTAGRAM_PASSWORD is required")
        
        # Check required Telegram settings
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required")
        
        # Check required OpenAI key
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate database URL
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of {valid_log_levels}")
        
        # Security check for Flask secret key
        if cls.FLASK_SECRET_KEY == "dev-secret-key-change-in-production":
            warnings.append("WARNING: Using default FLASK_SECRET_KEY. Change this in production!")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        # Print warnings
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)
        
        # Ensure directories exist
        cls.ensure_directories()
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with proper path resolution for SQLite."""
        db_url = cls.DATABASE_URL
        
        # Handle SQLite relative paths
        if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
            # Extract the relative path
            db_path = db_url.replace("sqlite:///", "")
            # Make it absolute
            absolute_path = cls.BASE_DIR / db_path
            # Return absolute SQLite URL
            return f"sqlite:///{absolute_path}"
        
        return db_url
    
    @classmethod
    def configure_logging(cls) -> None:
        """Configure application logging."""
        log_file = cls.LOGS_DIR / "smm_analise.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, cls.LOG_LEVEL.upper()))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Suppress verbose loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("instagrapi").setLevel(logging.INFO)


# Global settings instance
settings = Settings()


# Initialize logging on import
settings.configure_logging()
