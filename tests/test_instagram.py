"""Tests for Instagram client."""
import pytest
from unittest.mock import Mock, patch
from src.instagram.client import InstagramClient


@pytest.fixture
def mock_instagrapi_client():
    """Mock instagrapi client."""
    with patch('src.instagram.client.Client') as mock:
        yield mock


def test_instagram_client_init():
    """Test InstagramClient initialization."""
    client = InstagramClient(username='test', password='test')
    assert client.username == 'test'
    assert client.client is not None


def test_instagram_client_media_to_dict():
    """Test converting media to dictionary."""
    client = InstagramClient(username='test', password='test')
    
    # Create mock media
    mock_media = Mock()
    mock_media.pk = '123456'
    mock_media.media_type = 1  # photo
    mock_media.caption_text = 'Test caption #test'
    mock_media.taken_at = pytest.lazy_fixture
    mock_media.like_count = 10
    mock_media.comment_count = 2
    mock_media.view_count = None
    mock_media.thumbnail_url = 'http://example.com/thumb.jpg'
    mock_media.video_url = None
    
    result = client._media_to_dict(mock_media)
    
    assert result is not None
    assert result['post_id'] == '123456'
    assert result['media_type'] == 'photo'
    assert '#test' in result['hashtags']
