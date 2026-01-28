"""Instagram authentication module."""
import json
from pathlib import Path
from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    BadPassword
)
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InstagramAuth:
    """Handle Instagram authentication and session management."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize authentication handler.
        
        Args:
            username: Instagram username (optional, uses settings if not provided)
            password: Instagram password (optional, uses settings if not provided)
        """
        self.username = username or settings.INSTAGRAM_USERNAME
        self.password = password or settings.INSTAGRAM_PASSWORD
        self.session_file = settings.DATA_DIR / f"session_{self.username}.json"
        settings.ensure_directories()
    
    def login(self, client: Client, force_login: bool = False) -> bool:
        """
        Login to Instagram with session management.
        
        Args:
            client: Instagrapi Client instance
            force_login: Force fresh login even if session exists
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Try to load existing session
            if not force_login and self.session_file.exists():
                logger.info(f"Loading session from: {self.session_file}")
                try:
                    session_data = json.loads(self.session_file.read_text())
                    client.set_settings(session_data)
                    client.login(self.username, self.password)
                    
                    # Verify session is valid
                    client.get_timeline_feed()
                    logger.info("Successfully logged in using saved session")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Saved session invalid, performing fresh login: {e}")
                    self.session_file.unlink(missing_ok=True)
            
            # Perform fresh login
            logger.info(f"Logging in as: {self.username}")
            client.login(self.username, self.password)
            
            # Save session
            self.save_session(client)
            
            logger.info("Successfully logged in and saved session")
            return True
            
        except TwoFactorRequired as e:
            logger.error("Two-factor authentication required")
            logger.error("Please disable 2FA temporarily or implement 2FA handler")
            return False
            
        except ChallengeRequired as e:
            logger.error("Challenge required - Instagram is requesting verification")
            logger.error("Please login manually through browser and try again")
            return False
            
        except BadPassword as e:
            logger.error("Invalid username or password")
            return False
            
        except LoginRequired as e:
            logger.error("Login required but credentials may be invalid")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
            return False
    
    def save_session(self, client: Client) -> bool:
        """
        Save current session to file.
        
        Args:
            client: Instagrapi Client instance
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session_data = client.get_settings()
            self.session_file.write_text(json.dumps(session_data, indent=2))
            logger.info(f"Session saved to: {self.session_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)
            return False
    
    def logout(self, client: Client) -> bool:
        """
        Logout and clear session.
        
        Args:
            client: Instagrapi Client instance
            
        Returns:
            True if logged out successfully, False otherwise
        """
        try:
            client.logout()
            self.session_file.unlink(missing_ok=True)
            logger.info("Logged out and cleared session")
            return True
        except Exception as e:
            logger.error(f"Error during logout: {e}", exc_info=True)
            return False
    
    def is_logged_in(self, client: Client) -> bool:
        """
        Check if client is currently logged in.
        
        Args:
            client: Instagrapi Client instance
            
        Returns:
            True if logged in, False otherwise
        """
        try:
            client.get_timeline_feed()
            return True
        except Exception:
            return False
