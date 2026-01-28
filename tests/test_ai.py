"""Tests for AI analyzer."""
import pytest
from unittest.mock import Mock, patch
from src.ai.analyzer import AIAnalyzer


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch('src.ai.analyzer.openai') as mock:
        yield mock


def test_ai_analyzer_init():
    """Test AIAnalyzer initialization."""
    analyzer = AIAnalyzer(api_key='test', model='gpt-4')
    assert analyzer.api_key == 'test'
    assert analyzer.model == 'gpt-4'


def test_extract_score():
    """Test score extraction from AI response."""
    analyzer = AIAnalyzer(api_key='test')
    
    text1 = "ОЦІНКА: 7/10"
    assert analyzer._extract_score(text1) == 7.0
    
    text2 = "Оцінка контенту: 8"
    assert analyzer._extract_score(text2) == 8.0


def test_extract_hashtags():
    """Test hashtag extraction from AI response."""
    analyzer = AIAnalyzer(api_key='test')
    
    text = "Рекомендовані хештеги: #marketing #smm #instagram #digital"
    hashtags = analyzer._extract_hashtags(text)
    
    assert '#marketing' in hashtags
    assert '#smm' in hashtags
    assert len(hashtags) <= 15
