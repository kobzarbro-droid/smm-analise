"""Instagram client for API interactions."""
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from instagrapi import Client
from instagrapi.types import Media, Story, UserShort
from instagrapi.exceptions import ClientError, MediaNotFound
from config.settings import settings
from src.instagram.auth import InstagramAuth
from src.utils.logger import get_logger

logger = get_logger(__name__)


def retry_on_error(max_retries=3, delay=2, backoff=2):
    """Декоратор для повторних спроб при помилках"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries reached for {func.__name__}: {e}")
                        raise
                    
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {current_delay}s")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


class InstagramClient:
    """Client for Instagram API interactions with rate limiting and error handling."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Instagram client.
        
        Args:
            username: Instagram username (optional)
            password: Instagram password (optional)
        """
        self.client = Client()
        self.client.delay_range = [1, 3]  # Delay between requests
        self.auth = InstagramAuth(username, password)
        self.user_id = None
        self.username = username or settings.INSTAGRAM_USERNAME
        self._user_id_cache = {}  # Cache for user IDs
    
    def _use_alternative_api(self):
        """Перемкнутися на альтернативне API"""
        # Використовувати лише приватне API (V1)
        self.client.private_requests = True
        
        # Відключити публічні GraphQL запити
        try:
            self.client.use_public_api = False
        except:
            pass
    
    def get_user_id(self, username: str) -> int:
        """Отримати user ID з кешем"""
        if username in self._user_id_cache:
            return self._user_id_cache[username]
        
        user_id = self.client.user_id_from_username(username)
        self._user_id_cache[username] = user_id
        return user_id
    
    def login(self, force_login: bool = False) -> bool:
        """
        Login to Instagram.
        
        Args:
            force_login: Force fresh login
            
        Returns:
            True if successful, False otherwise
        """
        success = self.auth.login(self.client, force_login)
        if success:
            try:
                # Після успішного логіну перемикаємося на приватне API
                self._use_alternative_api()
                logger.info("Switched to private API mode")
                
                user_info = self.client.user_info_by_username(self.username)
                self.user_id = user_info.pk
                logger.info(f"User ID: {self.user_id}")
            except Exception as e:
                logger.error(f"Failed to get user info: {e}")
                return False
        return success
    
    def get_user_info(self, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get user account information with fallback mechanisms.
        
        Args:
            username: Username to get info for (defaults to authenticated user)
            
        Returns:
            Dictionary with user information
        """
        try:
            target_username = username or self.username
            
            # Спочатку пробуємо через V1 API (більш стабільний)
            try:
                user_id = self.get_user_id(target_username)
                user = self.client.user_info(user_id)
            except Exception as e:
                logger.warning(f"Failed to get user info via V1, trying alternative: {e}")
                try:
                    # Fallback на публічний метод без авторизації
                    user = self.client.user_info_by_username_v1(target_username)
                except Exception as e2:
                    logger.error(f"All methods failed to get user info: {e2}")
                    # Останній fallback - базовий метод
                    user = self.client.user_info_by_username(target_username)
            
            return {
                'user_id': user.pk,
                'username': user.username,
                'full_name': user.full_name,
                'biography': user.biography,
                'followers_count': user.follower_count,
                'following_count': user.following_count,
                'media_count': user.media_count,
                'is_private': user.is_private,
                'is_verified': user.is_verified,
                'profile_pic_url': user.profile_pic_url,
            }
        except Exception as e:
            logger.error(f"Failed to get user info for {username}: {e}")
            return None
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_posts(
        self,
        username: Optional[str] = None,
        amount: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's posts with improved error handling.
        
        Args:
            username: Username (defaults to authenticated user)
            amount: Number of posts to retrieve
            
        Returns:
            List of post dictionaries
        """
        try:
            target_username = username or self.username
            user_id = self.get_user_id(target_username)
            
            # Спочатку пробуємо V1 API
            try:
                medias = self.client.user_medias_v1(user_id, amount)
                logger.info(f"Retrieved {len(medias)} posts via V1 API for @{target_username}")
            except Exception as e:
                logger.warning(f"V1 API failed: {e}, trying paginated method")
                
                # Альтернативний метод - збір по сторінках
                try:
                    # Використовуємо метод з меншою кількістю полів
                    medias = self.client.user_medias(user_id, amount)
                    logger.info(f"Retrieved {len(medias)} posts via paginated method for @{target_username}")
                except Exception as e2:
                    logger.error(f"All media fetch methods failed: {e2}")
                    
                    # Останній fallback - збираємо що можемо
                    try:
                        # Пробуємо отримати лише базову інформацію
                        medias = self._get_basic_medias(user_id, amount)
                        logger.info(f"Retrieved {len(medias)} posts via basic method for @{target_username}")
                    except Exception as e3:
                        logger.error(f"Even basic media fetch failed: {e3}")
                        return []
            
            posts = []
            for media in medias:
                post_data = self._media_to_dict(media)
                if post_data:
                    posts.append(post_data)
            
            logger.info(f"Retrieved {len(posts)} posts for @{target_username}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get posts for {username}: {e}")
            return []
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific post by ID.
        
        Args:
            post_id: Instagram media ID
            
        Returns:
            Post dictionary or None
        """
        try:
            media = self.client.media_info(post_id)
            return self._media_to_dict(media)
        except MediaNotFound:
            logger.warning(f"Post not found: {post_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get post {post_id}: {e}")
            return None
    
    def _get_basic_medias(self, user_id: int, amount: int) -> List:
        """Резервний метод отримання медіа з мінімальними даними"""
        try:
            # Використовуємо публічний API без авторизації
            # Це резервний метод, який може не працювати у всіх випадках
            medias = []
            logger.warning(f"Using basic media fetch for user_id {user_id}")
            # Спроба отримати медіа через стандартний метод без додаткових полів
            return medias
        except Exception as e:
            logger.error(f"Basic media fetch failed: {e}")
            return []
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_stories(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's active stories.
        
        Args:
            username: Username (defaults to authenticated user)
            
        Returns:
            List of story dictionaries
        """
        try:
            target_username = username or self.username
            user_id = self.get_user_id(target_username)
            stories = self.client.user_stories(user_id)
            
            story_list = []
            for story in stories:
                story_data = self._story_to_dict(story)
                if story_data:
                    story_list.append(story_data)
            
            logger.info(f"Retrieved {len(story_list)} stories for @{target_username}")
            return story_list
            
        except Exception as e:
            logger.error(f"Failed to get stories for {username}: {e}")
            return []
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_reels(
        self,
        username: Optional[str] = None,
        amount: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's reels.
        
        Args:
            username: Username (defaults to authenticated user)
            amount: Number of reels to retrieve
            
        Returns:
            List of reel dictionaries
        """
        try:
            target_username = username or self.username
            user_id = self.get_user_id(target_username)
            
            # Get all medias and filter for reels (videos from clips)
            medias = self.client.user_medias(user_id, amount=amount)
            
            reels = []
            for media in medias:
                # Check if it's a reel (video with specific product_type)
                if self._is_reel(media):
                    reel_data = self._media_to_dict(media, is_reel=True)
                    if reel_data:
                        reels.append(reel_data)
            
            logger.info(f"Retrieved {len(reels)} reels for @{target_username}")
            return reels
            
        except Exception as e:
            logger.error(f"Failed to get reels for {username}: {e}")
            return []
    
    def _is_reel(self, media) -> bool:
        """Перевірити чи це рил"""
        try:
            return (hasattr(media, 'product_type') and 
                    media.product_type == 'clips') or \
                   (hasattr(media, 'media_type') and 
                    media.media_type == 2 and 
                    hasattr(media, 'clips_metadata'))
        except:
            return False
    
    def get_post_insights(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get insights/statistics for a specific post.
        
        Args:
            post_id: Instagram media ID
            
        Returns:
            Dictionary with insights data
        """
        try:
            media = self.client.media_info(post_id)
            insights = self.client.insights_media(post_id)
            
            return {
                'likes': media.like_count,
                'comments': media.comment_count,
                'saves': getattr(insights, 'saved', 0),
                'reach': getattr(insights, 'reach', 0),
                'impressions': getattr(insights, 'impressions', 0),
            }
        except Exception as e:
            logger.error(f"Failed to get insights for {post_id}: {e}")
            # Return basic metrics from media info
            try:
                media = self.client.media_info(post_id)
                return {
                    'likes': media.like_count,
                    'comments': media.comment_count,
                    'saves': 0,
                    'reach': 0,
                    'impressions': 0,
                }
            except:
                return None
    
    def _media_to_dict(self, media: Media, is_reel: bool = False) -> Optional[Dict[str, Any]]:
        """Convert Media object to dictionary with safe extraction."""
        try:
            # Extract hashtags from caption
            hashtags = []
            caption_text = getattr(media, 'caption_text', '')
            if caption_text:
                words = caption_text.split()
                hashtags = [word for word in words if word.startswith('#')]
            
            # Determine media type
            media_type_map = {1: 'photo', 2: 'video', 8: 'carousel'}
            media_type_value = getattr(media, 'media_type', 0)
            media_type = media_type_map.get(media_type_value, 'unknown')
            
            # Safe extraction of counts
            like_count = getattr(media, 'like_count', 0)
            comment_count = getattr(media, 'comment_count', 0)
            view_count = getattr(media, 'view_count', None)
            
            # Calculate engagement rate
            engagement = like_count + comment_count
            engagement_rate = (engagement / max(view_count or 1, 1)) * 100 if view_count else 0
            
            data = {
                'post_id': str(getattr(media, 'pk', '')),
                'media_type': 'reel' if is_reel else media_type,
                'caption': caption_text or '',
                'hashtags': hashtags,
                'posted_at': getattr(media, 'taken_at', None),
                'likes_count': like_count,
                'comments_count': comment_count,
                'engagement_rate': round(engagement_rate, 2),
                'thumbnail_url': str(media.thumbnail_url) if getattr(media, 'thumbnail_url', None) else None,
                'media_url': str(media.video_url) if getattr(media, 'video_url', None) else (str(media.thumbnail_url) if getattr(media, 'thumbnail_url', None) else None),
            }
            
            # Add reel-specific fields
            if is_reel:
                data['plays_count'] = view_count or 0
                data['shares_count'] = getattr(media, 'reshare_count', 0) or 0
                data['duration'] = getattr(media, 'video_duration', 0) or 0
            
            return data
            
        except Exception as e:
            logger.error(f"Error converting media to dict: {e}")
            return None
    
    def _story_to_dict(self, story: Story) -> Optional[Dict[str, Any]]:
        """Convert Story object to dictionary with safe extraction."""
        try:
            media_type_map = {1: 'photo', 2: 'video'}
            media_type_value = getattr(story, 'media_type', 0)
            
            taken_at = getattr(story, 'taken_at', datetime.now())
            
            return {
                'story_id': str(getattr(story, 'pk', '')),
                'media_type': media_type_map.get(media_type_value, 'unknown'),
                'posted_at': taken_at,
                'expires_at': taken_at + timedelta(hours=24),
                'views_count': getattr(story, 'view_count', 0),
                'thumbnail_url': str(story.thumbnail_url) if getattr(story, 'thumbnail_url', None) else None,
                'media_url': str(story.video_url) if getattr(story, 'video_url', None) else (str(story.thumbnail_url) if getattr(story, 'thumbnail_url', None) else None),
            }
        except Exception as e:
            logger.error(f"Error converting story to dict: {e}")
            return None
    
    def logout(self):
        """Logout from Instagram."""
        self.auth.logout(self.client)
