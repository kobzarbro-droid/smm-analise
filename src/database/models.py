"""SQLAlchemy models for SMM Analytics System."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Text, Float, DateTime, Date, Enum,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class PostType(enum.Enum):
    """Post type enumeration."""
    PHOTO = "photo"
    VIDEO = "video"
    CAROUSEL = "carousel"


class ContentType(enum.Enum):
    """Content type enumeration."""
    POST = "post"
    STORY = "story"
    REEL = "reel"


class Post(Base):
    """Instagram post model."""
    
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instagram_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    post_type: Mapped[PostType] = mapped_column(Enum(PostType), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ai_recommendations: Mapped[list["AIRecommendation"]] = relationship(
        "AIRecommendation",
        back_populates="post",
        foreign_keys="AIRecommendation.content_id",
        primaryjoin="and_(Post.id==AIRecommendation.content_id, AIRecommendation.content_type=='POST')",
        overlaps="story,reel,ai_recommendations"
    )
    
    __table_args__ = (
        Index("idx_posts_posted_at", "posted_at"),
        Index("idx_posts_instagram_id", "instagram_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, instagram_id={self.instagram_id}, posted_at={self.posted_at})>"


class Story(Base):
    """Instagram story model."""
    
    __tablename__ = "stories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instagram_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ai_recommendations: Mapped[list["AIRecommendation"]] = relationship(
        "AIRecommendation",
        back_populates="story",
        foreign_keys="AIRecommendation.content_id",
        primaryjoin="and_(Story.id==AIRecommendation.content_id, AIRecommendation.content_type=='STORY')",
        overlaps="post,reel,ai_recommendations"
    )
    
    __table_args__ = (
        Index("idx_stories_posted_at", "posted_at"),
        Index("idx_stories_instagram_id", "instagram_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Story(id={self.id}, instagram_id={self.instagram_id}, posted_at={self.posted_at})>"


class Reel(Base):
    """Instagram reel model."""
    
    __tablename__ = "reels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instagram_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    plays: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ai_recommendations: Mapped[list["AIRecommendation"]] = relationship(
        "AIRecommendation",
        back_populates="reel",
        foreign_keys="AIRecommendation.content_id",
        primaryjoin="and_(Reel.id==AIRecommendation.content_id, AIRecommendation.content_type=='REEL')",
        overlaps="post,story,ai_recommendations"
    )
    
    __table_args__ = (
        Index("idx_reels_posted_at", "posted_at"),
        Index("idx_reels_instagram_id", "instagram_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Reel(id={self.id}, instagram_id={self.instagram_id}, posted_at={self.posted_at})>"


class DailyStat(Base):
    """Daily aggregated statistics model."""
    
    __tablename__ = "daily_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(Date, unique=True, nullable=False, index=True)
    posts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stories_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reels_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_daily_stats_date", "date"),
        CheckConstraint("engagement_rate >= 0.0", name="check_engagement_rate_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<DailyStat(id={self.id}, date={self.date}, engagement_rate={self.engagement_rate})>"


class AIRecommendation(Base):
    """AI-generated recommendations for content."""
    
    __tablename__ = "ai_recommendations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships (viewonly to avoid conflicts)
    post: Mapped[Optional["Post"]] = relationship(
        "Post",
        back_populates="ai_recommendations",
        foreign_keys=[content_id],
        primaryjoin="and_(AIRecommendation.content_id==Post.id, AIRecommendation.content_type=='POST')",
        viewonly=True,
        overlaps="story,reel,ai_recommendations"
    )
    
    story: Mapped[Optional["Story"]] = relationship(
        "Story",
        back_populates="ai_recommendations",
        foreign_keys=[content_id],
        primaryjoin="and_(AIRecommendation.content_id==Story.id, AIRecommendation.content_type=='STORY')",
        viewonly=True,
        overlaps="post,reel,ai_recommendations"
    )
    
    reel: Mapped[Optional["Reel"]] = relationship(
        "Reel",
        back_populates="ai_recommendations",
        foreign_keys=[content_id],
        primaryjoin="and_(AIRecommendation.content_id==Reel.id, AIRecommendation.content_type=='REEL')",
        viewonly=True,
        overlaps="post,story,ai_recommendations"
    )
    
    __table_args__ = (
        Index("idx_ai_recommendations_content", "content_id", "content_type"),
        CheckConstraint("score >= 0.0 AND score <= 10.0", name="check_score_range"),
    )
    
    def __repr__(self) -> str:
        return f"<AIRecommendation(id={self.id}, content_type={self.content_type}, score={self.score})>"


class Competitor(Base):
    """Competitor tracking model."""
    
    __tablename__ = "competitors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    followers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_engagement: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_competitors_username", "username"),
        Index("idx_competitors_last_checked", "last_checked"),
        CheckConstraint("followers >= 0", name="check_followers_positive"),
        CheckConstraint("posts_count >= 0", name="check_posts_count_positive"),
        CheckConstraint("avg_engagement >= 0.0", name="check_avg_engagement_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<Competitor(id={self.id}, username={self.username}, followers={self.followers})>"


class Hashtag(Base):
    """Hashtag performance tracking model."""
    
    __tablename__ = "hashtags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_likes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_comments: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_hashtags_tag", "tag"),
        Index("idx_hashtags_effectiveness", "effectiveness_score"),
        CheckConstraint("usage_count >= 0", name="check_usage_count_positive"),
        CheckConstraint("avg_likes >= 0.0", name="check_avg_likes_positive"),
        CheckConstraint("avg_comments >= 0.0", name="check_avg_comments_positive"),
        CheckConstraint("effectiveness_score >= 0.0", name="check_effectiveness_score_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<Hashtag(id={self.id}, tag={self.tag}, effectiveness_score={self.effectiveness_score})>"
