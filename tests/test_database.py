"""Tests for database models and repository."""
import pytest
from datetime import datetime
from src.database.models import init_db, get_session, Post, Story, Reel, DailyStat
from src.database.repository import Repository


@pytest.fixture
def db_session():
    """Create a test database session."""
    init_db()
    session = get_session()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """Create a test repository."""
    return Repository(db_session)


def test_create_post(repository):
    """Test creating a post."""
    post_data = {
        'post_id': 'test123',
        'media_type': 'photo',
        'caption': 'Test post',
        'hashtags': ['#test', '#demo'],
        'posted_at': datetime.now(),
        'likes_count': 10,
        'comments_count': 2
    }
    
    post = repository.create_post(post_data)
    assert post.post_id == 'test123'
    assert post.likes_count == 10


def test_get_post_by_id(repository):
    """Test retrieving a post by ID."""
    post_data = {
        'post_id': 'test456',
        'media_type': 'video',
        'caption': 'Test video',
        'posted_at': datetime.now(),
    }
    
    repository.create_post(post_data)
    post = repository.get_post_by_id('test456')
    
    assert post is not None
    assert post.post_id == 'test456'
    assert post.media_type == 'video'


def test_create_story(repository):
    """Test creating a story."""
    story_data = {
        'story_id': 'story123',
        'media_type': 'photo',
        'posted_at': datetime.now(),
        'views_count': 100
    }
    
    story = repository.create_story(story_data)
    assert story.story_id == 'story123'
    assert story.views_count == 100


def test_create_daily_stat(repository):
    """Test creating/updating daily statistics."""
    date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stat_data = {
        'posts_count': 2,
        'stories_count': 5,
        'total_likes': 100,
        'avg_engagement_rate': 3.5
    }
    
    stat = repository.create_or_update_daily_stat(date, stat_data)
    assert stat.posts_count == 2
    assert stat.avg_engagement_rate == 3.5
