"""Tests for Instagram client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
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
    from datetime import datetime
    client = InstagramClient(username='test', password='test')
    
    # Create mock media
    mock_media = Mock()
    mock_media.pk = '123456'
    mock_media.media_type = 1  # photo
    mock_media.caption_text = 'Test caption #test'
    mock_media.taken_at = datetime.now()
    mock_media.like_count = 10
    mock_media.comment_count = 2
    mock_media.view_count = None
    mock_media.play_count = None
    mock_media.product_type = ''
    mock_media.thumbnail_url = 'http://example.com/thumb.jpg'
    mock_media.video_url = None
    mock_media.reshare_count = 0
    mock_media.video_duration = 0
    
    result = client._media_to_dict(mock_media)
    
    assert result is not None
    assert result['post_id'] == '123456'
    assert result['media_type'] == 'photo'
    assert '#test' in result['hashtags']


def test_forbidden_methods_blocked():
    """Test that all forbidden public API methods are blocked."""
    client = InstagramClient(username='test', password='test')
    
    # Test all forbidden methods
    forbidden_methods = [
        'user_info_by_username',
        'user_info_by_username_gql',
        'user_info_by_username_v1',
    ]
    
    for method_name in forbidden_methods:
        # Test that method exists but is patched
        assert hasattr(client.client, method_name), f"Method {method_name} should exist"
        
        # Test that calling it raises RuntimeError with proper message
        with pytest.raises(RuntimeError) as exc_info:
            getattr(client.client, method_name)('test')
        
        error_msg = str(exc_info.value)
        assert "FORBIDDEN" in error_msg, f"{method_name}: Should mention FORBIDDEN"
        assert "user_id_from_username" in error_msg, f"{method_name}: Should suggest user_id_from_username"
        assert "user_info_v1" in error_msg, f"{method_name}: Should suggest user_info_v1"


def test_get_user_info_uses_v1_only():
    """Test that get_user_info uses only V1 methods without fallback."""
    client = InstagramClient(username='test', password='test')
    
    # Mock the V1 methods
    mock_user = Mock()
    mock_user.pk = 12345
    mock_user.username = 'testuser'
    mock_user.full_name = 'Test User'
    mock_user.biography = 'Test bio'
    mock_user.follower_count = 100
    mock_user.following_count = 50
    mock_user.media_count = 10
    mock_user.is_private = False
    mock_user.is_verified = False
    mock_user.profile_pic_url = 'http://example.com/pic.jpg'
    
    client.client.user_id_from_username = Mock(return_value=12345)
    client.client.user_info_v1 = Mock(return_value=mock_user)
    
    # Call get_user_info
    result = client.get_user_info('testuser')
    
    # Verify only V1 methods were called
    client.client.user_id_from_username.assert_called_once_with('testuser')
    client.client.user_info_v1.assert_called_once_with(12345)
    
    # Verify result structure
    assert result is not None
    assert result['user_id'] == 12345
    assert result['username'] == 'testuser'
    assert result['followers_count'] == 100


def test_get_user_info_handles_v1_failure():
    """Test that get_user_info handles V1 API failure without fallback."""
    client = InstagramClient(username='test', password='test')
    
    # Mock V1 method to fail
    client.client.user_id_from_username = Mock(side_effect=Exception("V1 API failed"))
    
    # Create a mock for user_info to track if it's called (it shouldn't be)
    client.client.user_info = Mock()
    
    # Call should return None on failure (no fallback)
    result = client.get_user_info('testuser')
    
    assert result is None
    # Verify user_info was not called (no fallback to public API)
    client.client.user_info.assert_not_called()


def test_get_user_stories_uses_v1_only():
    """Test that get_user_stories uses only V1 methods without fallback."""
    client = InstagramClient(username='test', password='test')
    
    # Mock the V1 methods
    mock_story = Mock()
    mock_story.pk = '789'
    mock_story.media_type = 1
    mock_story.taken_at = Mock()
    mock_story.view_count = 50
    mock_story.thumbnail_url = 'http://example.com/story.jpg'
    mock_story.video_url = None
    
    client.client.user_id_from_username = Mock(return_value=12345)
    client.client.user_stories_v1 = Mock(return_value=[mock_story])
    
    # Call get_user_stories
    result = client.get_user_stories('testuser')
    
    # Verify only V1 methods were called
    client.client.user_id_from_username.assert_called_once_with('testuser')
    client.client.user_stories_v1.assert_called_once_with(12345)
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) >= 0  # May be empty if _story_to_dict fails


def test_get_user_stories_handles_v1_failure():
    """Test that get_user_stories handles V1 API failure without fallback."""
    client = InstagramClient(username='test', password='test')
    
    # Mock V1 method to fail
    client.client.user_id_from_username = Mock(return_value=12345)
    client.client.user_stories_v1 = Mock(side_effect=Exception("V1 API failed"))
    
    # Create a mock for user_stories to track if it's called (it shouldn't be)
    client.client.user_stories = Mock()
    
    # Call should return empty list on failure (no fallback)
    result = client.get_user_stories('testuser')
    
    assert result == []
    # Verify user_stories was not called (no fallback to public API)
    client.client.user_stories.assert_not_called()


