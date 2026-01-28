"""Database repository for data access operations."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
from src.database.models import (
    Post, Story, Reel, DailyStat, AIRecommendation,
    Competitor, Hashtag, get_session
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Repository:
    """Repository class for database operations."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize repository with database session."""
        self.session = session or get_session()
    
    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()
    
    # Post operations
    def create_post(self, post_data: Dict[str, Any]) -> Post:
        """Create a new post record."""
        post = Post(**post_data)
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        logger.info(f"Created post: {post.post_id}")
        return post
    
    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        """Get post by Instagram post ID."""
        return self.session.query(Post).filter(Post.post_id == post_id).first()
    
    def get_posts_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Post]:
        """Get posts within date range."""
        return self.session.query(Post).filter(
            and_(Post.posted_at >= start_date, Post.posted_at <= end_date)
        ).order_by(desc(Post.posted_at)).all()
    
    def get_recent_posts(self, limit: int = 10) -> List[Post]:
        """Get most recent posts."""
        return self.session.query(Post).order_by(
            desc(Post.posted_at)
        ).limit(limit).all()
    
    def update_post_metrics(self, post_id: str, metrics: Dict[str, Any]) -> Optional[Post]:
        """Update post metrics."""
        post = self.get_post_by_id(post_id)
        if post:
            for key, value in metrics.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            post.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(post)
            logger.info(f"Updated post metrics: {post_id}")
        return post
    
    # Story operations
    def create_story(self, story_data: Dict[str, Any]) -> Story:
        """Create a new story record."""
        story = Story(**story_data)
        self.session.add(story)
        self.session.commit()
        self.session.refresh(story)
        logger.info(f"Created story: {story.story_id}")
        return story
    
    def get_stories_by_date(self, date: datetime) -> List[Story]:
        """Get stories posted on a specific date."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self.session.query(Story).filter(
            and_(Story.posted_at >= start, Story.posted_at < end)
        ).all()
    
    # Reel operations
    def create_reel(self, reel_data: Dict[str, Any]) -> Reel:
        """Create a new reel record."""
        reel = Reel(**reel_data)
        self.session.add(reel)
        self.session.commit()
        self.session.refresh(reel)
        logger.info(f"Created reel: {reel.reel_id}")
        return reel
    
    def get_reels_by_week(self, start_date: datetime) -> List[Reel]:
        """Get reels posted in a specific week."""
        end_date = start_date + timedelta(days=7)
        return self.session.query(Reel).filter(
            and_(Reel.posted_at >= start_date, Reel.posted_at < end_date)
        ).all()
    
    # Daily statistics operations
    def create_or_update_daily_stat(self, date: datetime, stat_data: Dict[str, Any]) -> DailyStat:
        """Create or update daily statistics."""
        stat = self.session.query(DailyStat).filter(
            DailyStat.date == date.replace(hour=0, minute=0, second=0, microsecond=0)
        ).first()
        
        if stat:
            for key, value in stat_data.items():
                if hasattr(stat, key):
                    setattr(stat, key, value)
        else:
            stat = DailyStat(date=date, **stat_data)
            self.session.add(stat)
        
        self.session.commit()
        self.session.refresh(stat)
        logger.info(f"Updated daily stat for: {date:%Y-%m-%d}")
        return stat
    
    def get_daily_stat(self, date: datetime) -> Optional[DailyStat]:
        """Get daily statistics for a specific date."""
        return self.session.query(DailyStat).filter(
            DailyStat.date == date.replace(hour=0, minute=0, second=0, microsecond=0)
        ).first()
    
    def get_daily_stats_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[DailyStat]:
        """Get daily statistics within date range."""
        return self.session.query(DailyStat).filter(
            and_(DailyStat.date >= start_date, DailyStat.date <= end_date)
        ).order_by(DailyStat.date).all()
    
    # AI Recommendation operations
    def create_recommendation(self, rec_data: Dict[str, Any]) -> AIRecommendation:
        """Create a new AI recommendation."""
        recommendation = AIRecommendation(**rec_data)
        self.session.add(recommendation)
        self.session.commit()
        self.session.refresh(recommendation)
        logger.info(f"Created AI recommendation: {recommendation.recommendation_type}")
        return recommendation
    
    def get_recent_recommendations(self, limit: int = 10) -> List[AIRecommendation]:
        """Get recent AI recommendations."""
        return self.session.query(AIRecommendation).order_by(
            desc(AIRecommendation.created_at)
        ).limit(limit).all()
    
    def get_recommendations_for_post(self, post_id: int) -> List[AIRecommendation]:
        """Get all recommendations for a specific post."""
        return self.session.query(AIRecommendation).filter(
            AIRecommendation.post_id == post_id
        ).all()
    
    # Competitor operations
    def create_or_update_competitor(
        self, username: str, competitor_data: Dict[str, Any]
    ) -> Competitor:
        """Create or update competitor data."""
        competitor = self.session.query(Competitor).filter(
            Competitor.username == username
        ).first()
        
        if competitor:
            for key, value in competitor_data.items():
                if hasattr(competitor, key):
                    setattr(competitor, key, value)
            competitor.last_analyzed = datetime.utcnow()
        else:
            competitor = Competitor(username=username, **competitor_data)
            self.session.add(competitor)
        
        self.session.commit()
        self.session.refresh(competitor)
        logger.info(f"Updated competitor: @{username}")
        return competitor
    
    def get_all_competitors(self) -> List[Competitor]:
        """Get all competitor records."""
        return self.session.query(Competitor).order_by(
            desc(Competitor.last_analyzed)
        ).all()
    
    def get_competitor(self, username: str) -> Optional[Competitor]:
        """Get competitor by username."""
        return self.session.query(Competitor).filter(
            Competitor.username == username
        ).first()
    
    # Hashtag operations
    def create_or_update_hashtag(
        self, tag: str, hashtag_data: Dict[str, Any]
    ) -> Hashtag:
        """Create or update hashtag statistics."""
        # Remove # if present
        tag = tag.lstrip('#')
        
        hashtag = self.session.query(Hashtag).filter(
            Hashtag.tag == tag
        ).first()
        
        if hashtag:
            for key, value in hashtag_data.items():
                if hasattr(hashtag, key):
                    setattr(hashtag, key, value)
            hashtag.updated_at = datetime.utcnow()
        else:
            hashtag = Hashtag(tag=tag, **hashtag_data)
            self.session.add(hashtag)
        
        self.session.commit()
        self.session.refresh(hashtag)
        return hashtag
    
    def get_top_hashtags(self, limit: int = 20) -> List[Hashtag]:
        """Get top performing hashtags."""
        return self.session.query(Hashtag).order_by(
            desc(Hashtag.avg_engagement_rate)
        ).limit(limit).all()
    
    def get_trending_hashtags(self, limit: int = 10) -> List[Hashtag]:
        """Get trending hashtags."""
        return self.session.query(Hashtag).filter(
            Hashtag.is_trending == True
        ).order_by(desc(Hashtag.trend_score)).limit(limit).all()
    
    # Analytics queries
    def get_engagement_stats(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated engagement statistics."""
        posts = self.get_posts_by_date_range(start_date, end_date)
        
        if not posts:
            return {
                'total_posts': 0,
                'total_likes': 0,
                'total_comments': 0,
                'avg_engagement': 0.0
            }
        
        total_likes = sum(p.likes_count for p in posts)
        total_comments = sum(p.comments_count for p in posts)
        avg_engagement = sum(p.engagement_rate for p in posts) / len(posts)
        
        return {
            'total_posts': len(posts),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'avg_engagement': round(avg_engagement, 2)
        }
    
    def get_best_post(self, start_date: datetime, end_date: datetime) -> Optional[Post]:
        """Get best performing post in date range."""
        return self.session.query(Post).filter(
            and_(Post.posted_at >= start_date, Post.posted_at <= end_date)
        ).order_by(desc(Post.engagement_rate)).first()
    
    def get_top_posts(
        self, limit: int = 3, start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Post]:
        """Get top performing posts."""
        query = self.session.query(Post)
        
        if start_date and end_date:
            query = query.filter(
                and_(Post.posted_at >= start_date, Post.posted_at <= end_date)
            )
        
        return query.order_by(desc(Post.engagement_rate)).limit(limit).all()
