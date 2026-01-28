"""Data collector for Instagram content and statistics."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config.settings import settings
from src.instagram.client import InstagramClient
from src.database.repository import Repository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataCollector:
    """Collector for Instagram data with database persistence."""
    
    def __init__(self, client: Optional[InstagramClient] = None):
        """
        Initialize data collector.
        
        Args:
            client: InstagramClient instance (creates new one if not provided)
        """
        self.client = client or InstagramClient()
        self.repository = Repository()
        self.username = settings.get_target('instagram_account') or settings.INSTAGRAM_USERNAME
    
    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all data: posts, stories, and reels.
        
        Returns:
            Dictionary with collection statistics
        """
        logger.info("Starting full data collection...")
        
        stats = {
            'posts_collected': 0,
            'stories_collected': 0,
            'reels_collected': 0,
            'errors': []
        }
        
        # Collect posts
        try:
            posts_count = self.collect_posts()
            stats['posts_collected'] = posts_count
        except Exception as e:
            logger.error(f"Error collecting posts: {e}")
            stats['errors'].append(f"Posts: {str(e)}")
        
        # Collect stories
        try:
            stories_count = self.collect_stories()
            stats['stories_collected'] = stories_count
        except Exception as e:
            logger.error(f"Error collecting stories: {e}")
            stats['errors'].append(f"Stories: {str(e)}")
        
        # Collect reels
        try:
            reels_count = self.collect_reels()
            stats['reels_collected'] = reels_count
        except Exception as e:
            logger.error(f"Error collecting reels: {e}")
            stats['errors'].append(f"Reels: {str(e)}")
        
        # Update daily statistics
        try:
            self.update_daily_stats()
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
            stats['errors'].append(f"Daily stats: {str(e)}")
        
        logger.info(f"Collection complete: {stats}")
        return stats
    
    def collect_posts(self, amount: int = 50) -> int:
        """
        Collect recent posts and save to database.
        
        Args:
            amount: Number of posts to collect
            
        Returns:
            Number of posts collected
        """
        logger.info(f"Collecting posts for @{self.username}...")
        
        posts = self.client.get_user_posts(self.username, amount=amount)
        collected = 0
        
        for post_data in posts:
            try:
                # Check if post already exists
                existing = self.repository.get_post_by_id(post_data['post_id'])
                
                if existing:
                    # Update metrics
                    metrics = {
                        'likes_count': post_data['likes_count'],
                        'comments_count': post_data['comments_count'],
                        'engagement_rate': post_data['engagement_rate'],
                    }
                    self.repository.update_post_metrics(post_data['post_id'], metrics)
                else:
                    # Create new post
                    self.repository.create_post(post_data)
                    collected += 1
                
            except Exception as e:
                logger.error(f"Error saving post {post_data.get('post_id')}: {e}")
        
        logger.info(f"Collected {collected} new posts, updated {len(posts) - collected} existing")
        return collected
    
    def collect_stories(self) -> int:
        """
        Collect active stories and save to database.
        
        Returns:
            Number of stories collected
        """
        logger.info(f"Collecting stories for @{self.username}...")
        
        stories = self.client.get_user_stories(self.username)
        collected = 0
        
        for story_data in stories:
            try:
                # Check if story already exists
                story = self.repository.session.query(
                    self.repository.session.query.__self__.Story
                ).filter_by(story_id=story_data['story_id']).first()
                
                if not story:
                    self.repository.create_story(story_data)
                    collected += 1
                    
            except Exception as e:
                logger.error(f"Error saving story {story_data.get('story_id')}: {e}")
        
        logger.info(f"Collected {collected} new stories")
        return collected
    
    def collect_reels(self, amount: int = 50) -> int:
        """
        Collect reels and save to database.
        
        Args:
            amount: Number of reels to collect
            
        Returns:
            Number of reels collected
        """
        logger.info(f"Collecting reels for @{self.username}...")
        
        reels = self.client.get_user_reels(self.username, amount=amount)
        collected = 0
        
        for reel_data in reels:
            try:
                # Check if reel already exists
                reel = self.repository.session.query(
                    self.repository.session.query.__self__.Reel
                ).filter_by(reel_id=reel_data['post_id']).first()
                
                if not reel:
                    # Adapt post data to reel format
                    reel_create_data = {
                        'reel_id': reel_data['post_id'],
                        'caption': reel_data['caption'],
                        'hashtags': reel_data['hashtags'],
                        'posted_at': reel_data['posted_at'],
                        'plays_count': reel_data.get('plays_count', 0),
                        'likes_count': reel_data['likes_count'],
                        'comments_count': reel_data['comments_count'],
                        'shares_count': reel_data.get('shares_count', 0),
                        'engagement_rate': reel_data['engagement_rate'],
                        'thumbnail_url': reel_data['thumbnail_url'],
                        'video_url': reel_data['media_url'],
                        'duration': reel_data.get('duration', 0),
                    }
                    self.repository.create_reel(reel_create_data)
                    collected += 1
                    
            except Exception as e:
                logger.error(f"Error saving reel {reel_data.get('post_id')}: {e}")
        
        logger.info(f"Collected {collected} new reels")
        return collected
    
    def update_daily_stats(self, date: Optional[datetime] = None) -> None:
        """
        Update daily statistics.
        
        Args:
            date: Date to update stats for (defaults to today)
        """
        if date is None:
            date = datetime.now()
        
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info(f"Updating daily stats for {date:%Y-%m-%d}...")
        
        # Get counts for the day
        start_date = date
        end_date = date + timedelta(days=1)
        
        # Get posts, stories, reels for the day
        posts = self.repository.get_posts_by_date_range(start_date, end_date)
        stories = self.repository.get_stories_by_date(date)
        reels = self.repository.get_reels_by_week(start_date)  # Get week, filter later
        
        # Filter reels to today only
        reels_today = [r for r in reels if start_date <= r.posted_at < end_date]
        
        # Calculate aggregates
        total_likes = sum(p.likes_count for p in posts)
        total_comments = sum(p.comments_count for p in posts)
        total_reach = sum(p.reach for p in posts)
        
        avg_engagement = 0.0
        if posts:
            avg_engagement = sum(p.engagement_rate for p in posts) / len(posts)
        
        # Get follower count
        user_info = self.client.get_user_info(self.username)
        followers_count = user_info['followers_count'] if user_info else 0
        
        # Check target completion
        targets = settings.load_targets().get('targets', {})
        stories_target = targets.get('stories_per_day', 3)
        
        stat_data = {
            'posts_count': len(posts),
            'stories_count': len(stories),
            'reels_count': len(reels_today),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_reach': total_reach,
            'followers_count': followers_count,
            'avg_engagement_rate': round(avg_engagement, 2),
            'stories_target_met': len(stories) >= stories_target,
        }
        
        self.repository.create_or_update_daily_stat(date, stat_data)
        logger.info(f"Daily stats updated: {stat_data}")
    
    def collect_competitor_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Collect data for a competitor account.
        
        Args:
            username: Competitor's Instagram username
            
        Returns:
            Competitor data dictionary or None
        """
        logger.info(f"Collecting competitor data for @{username}...")
        
        try:
            # Get user info
            user_info = self.client.get_user_info(username)
            if not user_info:
                return None
            
            # Get recent posts
            posts = self.client.get_user_posts(username, amount=10)
            
            # Calculate metrics
            avg_engagement = 0.0
            avg_likes = 0.0
            avg_comments = 0.0
            top_post = None
            top_engagement = 0.0
            
            if posts:
                total_engagement = sum(p['engagement_rate'] for p in posts)
                avg_engagement = total_engagement / len(posts)
                avg_likes = sum(p['likes_count'] for p in posts) / len(posts)
                avg_comments = sum(p['comments_count'] for p in posts) / len(posts)
                
                # Find top post
                for post in posts:
                    if post['engagement_rate'] > top_engagement:
                        top_engagement = post['engagement_rate']
                        top_post = post['post_id']
            
            competitor_data = {
                'full_name': user_info['full_name'],
                'followers_count': user_info['followers_count'],
                'following_count': user_info['following_count'],
                'posts_count': user_info['media_count'],
                'recent_posts': posts[:10],
                'avg_engagement_rate': round(avg_engagement, 2),
                'avg_likes': round(avg_likes, 2),
                'avg_comments': round(avg_comments, 2),
                'top_post_id': top_post,
                'top_post_engagement': round(top_engagement, 2),
            }
            
            # Save to database
            self.repository.create_or_update_competitor(username, competitor_data)
            
            logger.info(f"Competitor data collected for @{username}")
            return competitor_data
            
        except Exception as e:
            logger.error(f"Error collecting competitor data for {username}: {e}")
            return None
    
    def close(self):
        """Close repository connection."""
        self.repository.close()
