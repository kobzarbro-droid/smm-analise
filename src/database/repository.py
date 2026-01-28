"""Repository pattern for database operations."""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Type, TypeVar
from contextlib import contextmanager

from sqlalchemy import create_engine, select, func, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .models import (
    Base, Post, Story, Reel, DailyStat, AIRecommendation,
    Competitor, Hashtag, PostType, ContentType
)

T = TypeVar('T', bound=Base)


class Repository:
    """Repository for database operations."""
    
    def __init__(self, database_url: str):
        """Initialize repository with database URL.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop all tables in the database."""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # Generic CRUD operations
    
    def create(self, model: T) -> T:
        """Create a new record.
        
        Args:
            model: Model instance to create
            
        Returns:
            Created model instance (detached from session)
        """
        with self.get_session() as session:
            session.add(model)
            session.commit()
            session.refresh(model)
            # Make expunge to detach from session
            session.expunge(model)
        return model
    
    def get_by_id(self, model_class: Type[T], record_id: int) -> Optional[T]:
        """Get a record by ID.
        
        Args:
            model_class: Model class
            record_id: Record ID
            
        Returns:
            Model instance or None
        """
        with self.get_session() as session:
            return session.get(model_class, record_id)
    
    def update(self, model: T) -> T:
        """Update a record.
        
        Args:
            model: Model instance to update
            
        Returns:
            Updated model instance
        """
        with self.get_session() as session:
            session.merge(model)
            session.flush()
            return model
    
    def delete(self, model: T) -> None:
        """Delete a record.
        
        Args:
            model: Model instance to delete
        """
        with self.get_session() as session:
            session.delete(model)
    
    # Post operations
    
    def create_post(self, **kwargs) -> Post:
        """Create a new post.
        
        Args:
            **kwargs: Post attributes
            
        Returns:
            Created Post instance
        """
        post = Post(**kwargs)
        return self.create(post)
    
    def get_post_by_instagram_id(self, instagram_id: str) -> Optional[Post]:
        """Get post by Instagram ID.
        
        Args:
            instagram_id: Instagram post ID
            
        Returns:
            Post instance or None
        """
        with self.get_session() as session:
            stmt = select(Post).where(Post.instagram_id == instagram_id)
            return session.execute(stmt).scalar_one_or_none()
    
    def get_posts_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Post]:
        """Get posts within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of Post instances
        """
        with self.get_session() as session:
            stmt = (
                select(Post)
                .where(and_(Post.posted_at >= start_date, Post.posted_at <= end_date))
                .order_by(desc(Post.posted_at))
            )
            return list(session.execute(stmt).scalars().all())
    
    def get_recent_posts(self, limit: int = 10) -> List[Post]:
        """Get most recent posts.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of Post instances
        """
        with self.get_session() as session:
            stmt = select(Post).order_by(desc(Post.posted_at)).limit(limit)
            return list(session.execute(stmt).scalars().all())
    
    # Story operations
    
    def create_story(self, **kwargs) -> Story:
        """Create a new story.
        
        Args:
            **kwargs: Story attributes
            
        Returns:
            Created Story instance
        """
        story = Story(**kwargs)
        return self.create(story)
    
    def get_story_by_instagram_id(self, instagram_id: str) -> Optional[Story]:
        """Get story by Instagram ID.
        
        Args:
            instagram_id: Instagram story ID
            
        Returns:
            Story instance or None
        """
        with self.get_session() as session:
            stmt = select(Story).where(Story.instagram_id == instagram_id)
            return session.execute(stmt).scalar_one_or_none()
    
    def get_stories_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Story]:
        """Get stories within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of Story instances
        """
        with self.get_session() as session:
            stmt = (
                select(Story)
                .where(and_(Story.posted_at >= start_date, Story.posted_at <= end_date))
                .order_by(desc(Story.posted_at))
            )
            return list(session.execute(stmt).scalars().all())
    
    # Reel operations
    
    def create_reel(self, **kwargs) -> Reel:
        """Create a new reel.
        
        Args:
            **kwargs: Reel attributes
            
        Returns:
            Created Reel instance
        """
        reel = Reel(**kwargs)
        return self.create(reel)
    
    def get_reel_by_instagram_id(self, instagram_id: str) -> Optional[Reel]:
        """Get reel by Instagram ID.
        
        Args:
            instagram_id: Instagram reel ID
            
        Returns:
            Reel instance or None
        """
        with self.get_session() as session:
            stmt = select(Reel).where(Reel.instagram_id == instagram_id)
            return session.execute(stmt).scalar_one_or_none()
    
    def get_reels_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Reel]:
        """Get reels within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of Reel instances
        """
        with self.get_session() as session:
            stmt = (
                select(Reel)
                .where(and_(Reel.posted_at >= start_date, Reel.posted_at <= end_date))
                .order_by(desc(Reel.posted_at))
            )
            return list(session.execute(stmt).scalars().all())
    
    # DailyStat operations
    
    def create_or_update_daily_stat(self, **kwargs) -> DailyStat:
        """Create or update daily statistics.
        
        Args:
            **kwargs: DailyStat attributes (must include 'date')
            
        Returns:
            Created or updated DailyStat instance
        """
        with self.get_session() as session:
            stat_date = kwargs.get('date')
            stmt = select(DailyStat).where(DailyStat.date == stat_date)
            existing = session.execute(stmt).scalar_one_or_none()
            
            if existing:
                for key, value in kwargs.items():
                    setattr(existing, key, value)
                session.commit()
                session.refresh(existing)
                session.expunge(existing)
                return existing
            else:
                new_stat = DailyStat(**kwargs)
                session.add(new_stat)
                session.commit()
                session.refresh(new_stat)
                session.expunge(new_stat)
                return new_stat
    
    def get_daily_stat_by_date(self, stat_date: date) -> Optional[DailyStat]:
        """Get daily stat by date.
        
        Args:
            stat_date: Date to query
            
        Returns:
            DailyStat instance or None
        """
        with self.get_session() as session:
            stmt = select(DailyStat).where(DailyStat.date == stat_date)
            return session.execute(stmt).scalar_one_or_none()
    
    def get_daily_stats_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[DailyStat]:
        """Get daily stats within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of DailyStat instances
        """
        with self.get_session() as session:
            stmt = (
                select(DailyStat)
                .where(and_(DailyStat.date >= start_date, DailyStat.date <= end_date))
                .order_by(asc(DailyStat.date))
            )
            return list(session.execute(stmt).scalars().all())
    
    # AI Recommendation operations
    
    def create_ai_recommendation(self, **kwargs) -> AIRecommendation:
        """Create a new AI recommendation.
        
        Args:
            **kwargs: AIRecommendation attributes
            
        Returns:
            Created AIRecommendation instance
        """
        recommendation = AIRecommendation(**kwargs)
        return self.create(recommendation)
    
    def get_recommendations_by_content(
        self, content_id: int, content_type: ContentType
    ) -> List[AIRecommendation]:
        """Get recommendations for specific content.
        
        Args:
            content_id: Content ID
            content_type: Content type
            
        Returns:
            List of AIRecommendation instances
        """
        with self.get_session() as session:
            stmt = (
                select(AIRecommendation)
                .where(
                    and_(
                        AIRecommendation.content_id == content_id,
                        AIRecommendation.content_type == content_type
                    )
                )
                .order_by(desc(AIRecommendation.created_at))
            )
            return list(session.execute(stmt).scalars().all())
    
    # Competitor operations
    
    def create_competitor(self, **kwargs) -> Competitor:
        """Create a new competitor.
        
        Args:
            **kwargs: Competitor attributes
            
        Returns:
            Created Competitor instance
        """
        competitor = Competitor(**kwargs)
        return self.create(competitor)
    
    def get_competitor_by_username(self, username: str) -> Optional[Competitor]:
        """Get competitor by username.
        
        Args:
            username: Instagram username
            
        Returns:
            Competitor instance or None
        """
        with self.get_session() as session:
            stmt = select(Competitor).where(Competitor.username == username)
            return session.execute(stmt).scalar_one_or_none()
    
    def get_all_competitors(self) -> List[Competitor]:
        """Get all competitors.
        
        Returns:
            List of Competitor instances
        """
        with self.get_session() as session:
            stmt = select(Competitor).order_by(desc(Competitor.avg_engagement))
            return list(session.execute(stmt).scalars().all())
    
    def update_competitor(self, username: str, **kwargs) -> Optional[Competitor]:
        """Update competitor data.
        
        Args:
            username: Instagram username
            **kwargs: Fields to update
            
        Returns:
            Updated Competitor instance or None
        """
        with self.get_session() as session:
            stmt = select(Competitor).where(Competitor.username == username)
            competitor = session.execute(stmt).scalar_one_or_none()
            
            if competitor:
                for key, value in kwargs.items():
                    setattr(competitor, key, value)
                session.commit()
                session.refresh(competitor)
                session.expunge(competitor)
            
            return competitor
    
    # Hashtag operations
    
    def create_hashtag(self, **kwargs) -> Hashtag:
        """Create a new hashtag.
        
        Args:
            **kwargs: Hashtag attributes
            
        Returns:
            Created Hashtag instance
        """
        hashtag = Hashtag(**kwargs)
        return self.create(hashtag)
    
    def get_hashtag_by_tag(self, tag: str) -> Optional[Hashtag]:
        """Get hashtag by tag.
        
        Args:
            tag: Hashtag text
            
        Returns:
            Hashtag instance or None
        """
        with self.get_session() as session:
            stmt = select(Hashtag).where(Hashtag.tag == tag)
            return session.execute(stmt).scalar_one_or_none()
    
    def get_top_hashtags(self, limit: int = 20) -> List[Hashtag]:
        """Get top performing hashtags.
        
        Args:
            limit: Maximum number of hashtags to return
            
        Returns:
            List of Hashtag instances
        """
        with self.get_session() as session:
            stmt = (
                select(Hashtag)
                .order_by(desc(Hashtag.effectiveness_score))
                .limit(limit)
            )
            return list(session.execute(stmt).scalars().all())
    
    def update_hashtag(self, tag: str, **kwargs) -> Optional[Hashtag]:
        """Update hashtag data.
        
        Args:
            tag: Hashtag text
            **kwargs: Fields to update
            
        Returns:
            Updated Hashtag instance or None
        """
        with self.get_session() as session:
            stmt = select(Hashtag).where(Hashtag.tag == tag)
            hashtag = session.execute(stmt).scalar_one_or_none()
            
            if hashtag:
                for key, value in kwargs.items():
                    setattr(hashtag, key, value)
                session.commit()
                session.refresh(hashtag)
                session.expunge(hashtag)
            
            return hashtag
    
    # Aggregation methods
    
    def get_content_stats(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated content statistics for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with aggregated statistics
        """
        with self.get_session() as session:
            # Posts
            posts_stmt = select(
                func.count(Post.id),
                func.sum(Post.likes),
                func.sum(Post.comments),
                func.avg(Post.likes),
                func.avg(Post.comments)
            ).where(and_(Post.posted_at >= start_date, Post.posted_at <= end_date))
            posts_result = session.execute(posts_stmt).one()
            
            # Stories
            stories_stmt = select(
                func.count(Story.id),
                func.sum(Story.views)
            ).where(and_(Story.posted_at >= start_date, Story.posted_at <= end_date))
            stories_result = session.execute(stories_stmt).one()
            
            # Reels
            reels_stmt = select(
                func.count(Reel.id),
                func.sum(Reel.likes),
                func.sum(Reel.comments),
                func.sum(Reel.views)
            ).where(and_(Reel.posted_at >= start_date, Reel.posted_at <= end_date))
            reels_result = session.execute(reels_stmt).one()
            
            return {
                'posts': {
                    'count': posts_result[0] or 0,
                    'total_likes': posts_result[1] or 0,
                    'total_comments': posts_result[2] or 0,
                    'avg_likes': float(posts_result[3] or 0),
                    'avg_comments': float(posts_result[4] or 0),
                },
                'stories': {
                    'count': stories_result[0] or 0,
                    'total_views': stories_result[1] or 0,
                },
                'reels': {
                    'count': reels_result[0] or 0,
                    'total_likes': reels_result[1] or 0,
                    'total_comments': reels_result[2] or 0,
                    'total_views': reels_result[3] or 0,
                }
            }
    
    def calculate_engagement_rate(
        self, likes: int, comments: int, followers: int
    ) -> float:
        """Calculate engagement rate.
        
        Args:
            likes: Number of likes
            comments: Number of comments
            followers: Number of followers
            
        Returns:
            Engagement rate as percentage
        """
        if followers == 0:
            return 0.0
        return ((likes + comments) / followers) * 100
