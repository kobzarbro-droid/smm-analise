"""Instagram client for API interactions - ONLY V1 Private API."""
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from instagrapi import Client
from instagrapi.exceptions import ClientError, MediaNotFound, RateLimitError
from config.settings import settings
from src.instagram.auth import InstagramAuth
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _forbidden_method_warning(method_name: str):
    """Raise exception for forbidden public API methods."""
    error_msg = (
        f"FORBIDDEN: {method_name} is a PUBLIC API method and should NOT be used!\n"
        f"Use ONLY Private API V1 methods:\n"
        f"  - user_id_from_username(username) to get user_id\n"
        f"  - user_info_v1(user_id) to get user info\n"
        f"  - user_medias_v1(user_id, amount) to get posts\n"
        f"  - user_stories_v1(user_id) to get stories\n"
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def _patch_forbidden_methods(client: Client):
    """Patch forbidden public API methods to raise warnings."""
    forbidden_methods = [
        'user_info_by_username',
        'user_info_by_username_gql',
        'user_info_by_username_v1',  # Just in case
    ]
    
    for method_name in forbidden_methods:
        if hasattr(client, method_name):
            # Replace method with a warning function
            setattr(
                client,
                method_name,
                lambda *args, **kwargs: _forbidden_method_warning(method_name)
            )
    
    logger.info("Patched forbidden public API methods with warnings")


def retry_on_error(max_retries=3, delay=2, backoff=2):
    """Decorator for retrying on errors with rate limit handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    retries += 1
                    wait_time = current_delay * (backoff ** retries)
                    logger.warning(
                        f"Rate limit hit for {func.__name__}. "
                        f"Retry {retries}/{max_retries} after {wait_time}s"
                    )
                    if retries >= max_retries:
                        raise
                    time.sleep(wait_time)
                except (ClientError, Exception) as e:
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
        
        # Patch forbidden public API methods
        _patch_forbidden_methods(self.client)
        
        self.auth = InstagramAuth(username, password)
        self.user_id = None
        self.username = username or settings.INSTAGRAM_USERNAME
        self._user_id_cache = {}  # Cache for user IDs
    
    def _use_alternative_api(self):
        """Switch to alternative API mode - use ONLY Private API V1."""
        # Use only private API (V1)
        try:
            self.client.private_requests = True
            logger.info("Switched to private API V1 mode")
        except AttributeError:
            # Attribute doesn't exist in this version
            logger.warning("Could not set private_requests attribute")
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_id(self, username: str) -> int:
        """Get user ID with caching - use ONLY V1 method."""
        if username in self._user_id_cache:
            return self._user_id_cache[username]
        
        try:
            user_id = self.client.user_id_from_username(username)
            self._user_id_cache[username] = user_id
            logger.info(f"User ID for @{username}: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Failed to get user_id for {username}: {e}")
            raise
    
    def login(self, force_login: bool = False) -> bool:
        """
        Login to Instagram - ONLY V1 Private API.
        
        Args:
            force_login: Force fresh login
            
        Returns:
            True if successful, False otherwise
        """
        success = self.auth.login(self.client, force_login)
        if success:
            try:
                # After successful login, switch to private API
                self._use_alternative_api()
                logger.info("Switched to private API mode")
                
                # Use ONLY V1 Private API methods
                user_id = self.client.user_id_from_username(self.username)
                self.user_id = user_id
                logger.info(f"User ID found: {self.user_id}")
                
                # Verify with user_info_v1
                user_info = self.client.user_info_v1(user_id)
                logger.info(f"User info_v1 returned actual user data for @{user_info.username}")
            except Exception as e:
                logger.error(f"Failed to get user info via V1 API: {e}")
                return False
        return success
    
    def get_user_info(self, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get user account information - ONLY V1 API with safe extraction.
        
        Args:
            username: Username to get info for (defaults to authenticated user)
            
        Returns:
            Dictionary with user information
        """
        try:
            target_username = username or self.username
            
            # Use ONLY V1 Private API - NO fallbacks to public API
            user_id = self.get_user_id(target_username)
            logger.info(f"user_id found: {user_id}")
            
            user = self.client.user_info_v1(user_id)
            logger.info(f"user_info_v1 returned actual user data for @{user.username}")
            
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
            logger.error(f"Failed to get user info via V1 API for {username}: {e}")
            return None
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_posts(
        self,
        username: Optional[str] = None,
        amount: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's posts - ONLY V1 API with safe validation error handling.
        
        Args:
            username: Username (defaults to authenticated user)
            amount: Number of posts to retrieve
            
        Returns:
            List of post dictionaries
        """
        try:
            target_username = username or self.username
            user_id = self.get_user_id(target_username)
            
            logger.info(f"Fetching posts for @{target_username} (user_id: {user_id})...")
            
            # Use ONLY V1 API
            try:
                medias = self.client.user_medias_v1(user_id, amount)
                logger.info(f"Retrieved {len(medias)} posts via V1 API for @{target_username}")
            except Exception as e:
                logger.error(f"V1 API failed: {e}")
                return []
            
            posts = []
            for media in medias:
                try:
                    post_data = self._media_to_dict(media)
                    if post_data:
                        posts.append(post_data)
                except Exception as e:
                    logger.warning(f"Skipped media due to validation error: {e}")
                    continue
            
            logger.info(f"Successfully retrieved {len(posts)} posts for @{target_username}")
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
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_stories(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's active stories - ONLY V1 API.
        
        Args:
            username: Username (defaults to authenticated user)
            
        Returns:
            List of story dictionaries
        """
        try:
            target_username = username or self.username
            user_id = self.get_user_id(target_username)
            
            logger.info(f"Fetching stories for @{target_username}...")
            
            # Use ONLY V1 Private API method - NO fallbacks
            stories = self.client.user_stories_v1(user_id)
            logger.info(f"Retrieved {len(stories)} stories via V1 API for @{target_username}")
            
            story_list = []
            for story in stories:
                try:
                    story_data = self._story_to_dict(story)
                    if story_data:
                        story_list.append(story_data)
                except Exception as e:
                    logger.warning(f"Skipped story due to validation error: {e}")
                    continue
            
            logger.info(f"Successfully collected stories via V1 only (0 public calls)")
            return story_list
            
        except Exception as e:
            logger.error(f"Failed to get stories via V1 API for {username}: {e}")
            return []
    
    @retry_on_error(max_retries=3, delay=2)
    def get_user_reels(
        self,
        username: Optional[str] = None,
        amount: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's reels - filter from posts.
        
        Args:
            username: Username (defaults to authenticated user)
            amount: Number of reels to retrieve
            
        Returns:
            List of reel dictionaries
        """
        try:
            target_username = username or self.username
            logger.info(f"Fetching reels for @{target_username}...")
            
            # Get all medias and filter for reels
            medias = self.get_user_posts(target_username, amount=amount * 3)
            
            reels = []
            for media in medias:
                # Check if it's a reel
                if self._is_reel_dict(media):
                    reel_data = media.copy()
                    reel_data['media_type'] = 'reel'
                    reels.append(reel_data)
            
            logger.info(f"Found {len(reels)} reels out of {len(medias)} posts for @{target_username}")
            return reels[:amount]
            
        except Exception as e:
            logger.error(f"Failed to get reels for {username}: {e}")
            return []
    
    def _is_reel_dict(self, media_dict: dict) -> bool:
        """Check if media dict represents a reel."""
        try:
            # First check if it's explicitly marked as a reel
            if media_dict.get('is_reel', False):
                return True
            
            # Check if media_type is video (as string)
            if media_dict.get('media_type') != 'video':
                return False
            
            # Videos with play_count are likely reels
            return media_dict.get('play_count', 0) > 0
        except Exception:
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
    
    def _extract_media_urls(self, media_obj) -> tuple:
        """Extract URLs safely from media object."""
        thumbnail_url = None
        media_url = None
        try:
            if hasattr(media_obj, 'thumbnail_url') and media_obj.thumbnail_url:
                thumbnail_url = str(media_obj.thumbnail_url)
            if hasattr(media_obj, 'video_url') and media_obj.video_url:
                media_url = str(media_obj.video_url)
            elif thumbnail_url:
                media_url = thumbnail_url
        except Exception as e:
            logger.warning(f"Error extracting media URLs: {e}")
        return thumbnail_url, media_url
    
    def _media_to_dict(self, media, is_reel: bool = False) -> Optional[Dict[str, Any]]:
        """Convert Media object to dictionary with safe extraction to avoid Pydantic errors."""
        try:
            # Extract hashtags from caption
            hashtags = []
            caption_text = getattr(media, 'caption_text', '')
            if caption_text:
                words = caption_text.split()
                hashtags = [word for word in words if word.startswith('#')]
            
            # Determine media type safely
            media_type_map = {1: 'photo', 2: 'video', 8: 'carousel'}
            media_type_value = getattr(media, 'media_type', 0)
            media_type = media_type_map.get(media_type_value, 'unknown')
            
            # Safe extraction of counts
            like_count = getattr(media, 'like_count', 0) or 0
            comment_count = getattr(media, 'comment_count', 0) or 0
            view_count = getattr(media, 'view_count', None) or 0
            play_count = getattr(media, 'play_count', None) or 0
            
            # Check if this is a reel (safely)
            is_reel_flag = False
            try:
                product_type = getattr(media, 'product_type', '')
                is_reel_flag = (product_type == 'clips') or is_reel
            except Exception as e:
                logger.warning(f"Error checking reel flag: {e}")
                is_reel_flag = is_reel
            
            # Calculate engagement rate
            engagement = like_count + comment_count
            engagement_rate = (engagement / max(view_count or play_count or 1, 1)) * 100 if (view_count or play_count) else 0
            
            # Extract URLs safely
            thumbnail_url, media_url = self._extract_media_urls(media)
            
            data = {
                'post_id': str(getattr(media, 'pk', '')),
                'media_type': 'reel' if is_reel_flag else media_type,
                'caption': caption_text or '',
                'hashtags': hashtags,
                'posted_at': getattr(media, 'taken_at', None),
                'likes_count': like_count,
                'comments_count': comment_count,
                'engagement_rate': round(engagement_rate, 2),
                'thumbnail_url': thumbnail_url,
                'media_url': media_url,
                'is_reel': is_reel_flag,
            }
            
            # Warn if posted_at is missing
            if data['posted_at'] is None:
                logger.warning(f"Media {data['post_id']} missing taken_at timestamp")
                data['posted_at'] = datetime.now()
            
            # Add reel/video-specific fields
            if is_reel_flag or media_type == 'video':
                data['plays_count'] = play_count or view_count or 0
                data['shares_count'] = getattr(media, 'reshare_count', 0) or 0
                data['duration'] = getattr(media, 'video_duration', 0) or 0
            
            return data
            
        except Exception as e:
            logger.warning(f"Error converting media to dict: {e}")
            return None
    
    def _story_to_dict(self, story) -> Optional[Dict[str, Any]]:
        """Convert Story object to dictionary with safe extraction."""
        try:
            media_type_map = {1: 'photo', 2: 'video'}
            media_type_value = getattr(story, 'media_type', 0)
            
            taken_at = getattr(story, 'taken_at', None)
            if taken_at is None:
                logger.warning(f"Story {getattr(story, 'pk', 'unknown')} missing taken_at timestamp")
                taken_at = datetime.now()
            
            # Extract URLs safely
            thumbnail_url, media_url = self._extract_media_urls(story)
            
            return {
                'story_id': str(getattr(story, 'pk', '')),
                'media_type': media_type_map.get(media_type_value, 'unknown'),
                'posted_at': taken_at,
                'expires_at': taken_at + timedelta(hours=24),
                'views_count': getattr(story, 'view_count', 0) or 0,
                'thumbnail_url': thumbnail_url,
                'media_url': media_url,
            }
        except Exception as e:
            logger.warning(f"Error converting story to dict: {e}")
            return None
    
    def logout(self):
        """Logout from Instagram."""
        self.auth.logout(self.client)
