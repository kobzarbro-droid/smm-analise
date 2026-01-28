"""Instagram client for API interactions."""
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from instagrapi import Client
from instagrapi.types import Media, Story, UserShort
from instagrapi.exceptions import ClientError, MediaNotFound
from config.settings import settings
from src.instagram.auth import InstagramAuth
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
                user_info = self.client.user_info_by_username(self.username)
                self.user_id = user_info.pk
                logger.info(f"User ID: {self.user_id}")
            except Exception as e:
                logger.error(f"Failed to get user info: {e}")
                return False
        return success
    
    def get_user_info(self, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get user account information.
        
        Args:
            username: Username to get info for (defaults to authenticated user)
            
        Returns:
            Dictionary with user information
        """
        try:
            target_username = username or self.username
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
    
    def get_user_posts(
        self,
        username: Optional[str] = None,
        amount: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's posts.
        
        Args:
            username: Username (defaults to authenticated user)
            amount: Number of posts to retrieve
            
        Returns:
            List of post dictionaries
        """
        try:
            target_username = username or self.username
            user_id = self.client.user_id_from_username(target_username)
            medias = self.client.user_medias(user_id, amount=amount)
            
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
            user_id = self.client.user_id_from_username(target_username)
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
            user_id = self.client.user_id_from_username(target_username)
            
            # Get all medias and filter for reels (videos from clips)
            medias = self.client.user_medias(user_id, amount=amount)
            
            reels = []
            for media in medias:
                # Check if it's a reel (video with specific product_type)
                if media.media_type == 2 and media.product_type == 'clips':
                    reel_data = self._media_to_dict(media, is_reel=True)
                    if reel_data:
                        reels.append(reel_data)
            
            logger.info(f"Retrieved {len(reels)} reels for @{target_username}")
            return reels
            
        except Exception as e:
            logger.error(f"Failed to get reels for {username}: {e}")
            return []
    
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
        """Convert Media object to dictionary."""
        try:
            # Extract hashtags from caption
            hashtags = []
            if media.caption_text:
                words = media.caption_text.split()
                hashtags = [word for word in words if word.startswith('#')]
            
            # Determine media type
            media_type_map = {1: 'photo', 2: 'video', 8: 'carousel'}
            media_type = media_type_map.get(media.media_type, 'unknown')
            
            # Calculate engagement rate
            engagement = media.like_count + media.comment_count
            engagement_rate = (engagement / max(media.view_count or 1, 1)) * 100 if media.view_count else 0
            
            data = {
                'post_id': str(media.pk),
                'media_type': 'reel' if is_reel else media_type,
                'caption': media.caption_text or '',
                'hashtags': hashtags,
                'posted_at': media.taken_at,
                'likes_count': media.like_count,
                'comments_count': media.comment_count,
                'engagement_rate': round(engagement_rate, 2),
                'thumbnail_url': str(media.thumbnail_url) if media.thumbnail_url else None,
                'media_url': str(media.video_url) if media.video_url else str(media.thumbnail_url) if media.thumbnail_url else None,
            }
            
            # Add reel-specific fields
            if is_reel:
                data['plays_count'] = media.view_count or 0
                data['shares_count'] = media.reshare_count or 0
                data['duration'] = media.video_duration or 0
            
            return data
            
        except Exception as e:
            logger.error(f"Error converting media to dict: {e}")
            return None
    
    def _story_to_dict(self, story: Story) -> Optional[Dict[str, Any]]:
        """Convert Story object to dictionary."""
        try:
            media_type_map = {1: 'photo', 2: 'video'}
            
            return {
                'story_id': str(story.pk),
                'media_type': media_type_map.get(story.media_type, 'unknown'),
                'posted_at': story.taken_at,
                'expires_at': story.taken_at + timedelta(hours=24),
                'views_count': getattr(story, 'view_count', 0),
                'thumbnail_url': str(story.thumbnail_url) if story.thumbnail_url else None,
                'media_url': str(story.video_url) if story.video_url else str(story.thumbnail_url) if story.thumbnail_url else None,
            }
        except Exception as e:
            logger.error(f"Error converting story to dict: {e}")
            return None
    
    def logout(self):
        """Logout from Instagram."""
        self.auth.logout(self.client)
