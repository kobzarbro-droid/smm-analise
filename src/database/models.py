"""Database models for SMM analytics."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from config.settings import settings

Base = declarative_base()


class Post(Base):
    """Instagram post model."""
    
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), unique=True, nullable=False, index=True)
    media_type = Column(String(20))  # photo, video, carousel
    caption = Column(Text)
    hashtags = Column(JSON)  # List of hashtags
    posted_at = Column(DateTime, nullable=False, index=True)
    
    # Metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    
    # Media
    thumbnail_url = Column(String(500))
    media_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ai_recommendations = relationship("AIRecommendation", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post {self.post_id} - {self.posted_at:%Y-%m-%d}>"


class Story(Base):
    """Instagram story model."""
    
    __tablename__ = 'stories'
    
    id = Column(Integer, primary_key=True)
    story_id = Column(String(50), unique=True, nullable=False, index=True)
    media_type = Column(String(20))  # photo, video
    posted_at = Column(DateTime, nullable=False, index=True)
    expires_at = Column(DateTime)
    
    # Metrics
    views_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    
    # Media
    thumbnail_url = Column(String(500))
    media_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Story {self.story_id} - {self.posted_at:%Y-%m-%d}>"


class Reel(Base):
    """Instagram reel model."""
    
    __tablename__ = 'reels'
    
    id = Column(Integer, primary_key=True)
    reel_id = Column(String(50), unique=True, nullable=False, index=True)
    caption = Column(Text)
    hashtags = Column(JSON)
    posted_at = Column(DateTime, nullable=False, index=True)
    
    # Metrics
    plays_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    
    # Media
    thumbnail_url = Column(String(500))
    video_url = Column(String(500))
    duration = Column(Integer)  # Duration in seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Reel {self.reel_id} - {self.posted_at:%Y-%m-%d}>"


class DailyStat(Base):
    """Daily aggregated statistics."""
    
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True, nullable=False, index=True)
    
    # Counts
    posts_count = Column(Integer, default=0)
    stories_count = Column(Integer, default=0)
    reels_count = Column(Integer, default=0)
    
    # Aggregated metrics
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_saves = Column(Integer, default=0)
    total_reach = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    
    # Followers
    followers_count = Column(Integer, default=0)
    followers_change = Column(Integer, default=0)
    
    # Calculated metrics
    avg_engagement_rate = Column(Float, default=0.0)
    
    # Plan completion
    posts_target_met = Column(Boolean, default=False)
    stories_target_met = Column(Boolean, default=False)
    reels_target_met = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DailyStat {self.date:%Y-%m-%d}>"


class AIRecommendation(Base):
    """AI-generated recommendations for content."""
    
    __tablename__ = 'ai_recommendations'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=True)
    recommendation_type = Column(String(50))  # caption, hashtags, timing, general
    
    # Original and improved content
    original_text = Column(Text)
    improved_text = Column(Text)
    
    # Analysis
    analysis = Column(Text)
    score = Column(Float)  # Quality score 0-10
    suggestions = Column(JSON)  # List of suggestions
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    applied = Column(Boolean, default=False)
    
    # Relationships
    post = relationship("Post", back_populates="ai_recommendations")
    
    def __repr__(self):
        return f"<AIRecommendation {self.recommendation_type} - Score: {self.score}>"


class Competitor(Base):
    """Competitor account tracking."""
    
    __tablename__ = 'competitors'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200))
    
    # Metrics
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    
    # Recent activity (stored as JSON for flexibility)
    recent_posts = Column(JSON)  # Last 10 posts data
    avg_engagement_rate = Column(Float, default=0.0)
    avg_likes = Column(Float, default=0.0)
    avg_comments = Column(Float, default=0.0)
    
    # Top performing content
    top_post_id = Column(String(50))
    top_post_engagement = Column(Float, default=0.0)
    
    # Analysis
    posting_frequency = Column(Float)  # Posts per day
    best_posting_times = Column(JSON)  # List of optimal hours
    popular_hashtags = Column(JSON)  # Most used hashtags
    
    # Metadata
    last_analyzed = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Competitor @{self.username}>"


class Hashtag(Base):
    """Hashtag performance tracking."""
    
    __tablename__ = 'hashtags'
    
    id = Column(Integer, primary_key=True)
    tag = Column(String(100), unique=True, nullable=False, index=True)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    # Performance metrics
    avg_likes = Column(Float, default=0.0)
    avg_comments = Column(Float, default=0.0)
    avg_reach = Column(Float, default=0.0)
    avg_engagement_rate = Column(Float, default=0.0)
    
    # Best/worst performing posts with this hashtag
    best_post_id = Column(String(50))
    best_post_engagement = Column(Float, default=0.0)
    worst_post_id = Column(String(50))
    worst_post_engagement = Column(Float, default=0.0)
    
    # Trending info
    is_trending = Column(Boolean, default=False)
    trend_score = Column(Float, default=0.0)
    
    # Metadata
    last_used = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Hashtag #{self.tag}>"


# Database initialization
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings.ensure_directories()
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
        )
    return _engine


def init_db():
    """Initialize database and create all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def get_session() -> Session:
    """Get database session."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal()
