"""Tests for Telegram bot module."""
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.telegram.formatters import MessageFormatter
from src.telegram.bot import TelegramBot


class TestMessageFormatter(unittest.TestCase):
    """Test message formatting utilities."""
    
    def setUp(self):
        self.formatter = MessageFormatter()
    
    def test_progress_bar(self):
        """Test progress bar generation."""
        # Test various percentages
        self.assertEqual(self.formatter.progress_bar(0, 10), '░' * 10)
        self.assertEqual(self.formatter.progress_bar(5, 10), '█' * 5 + '░' * 5)
        self.assertEqual(self.formatter.progress_bar(10, 10), '█' * 10)
        
        # Test edge cases
        self.assertEqual(self.formatter.progress_bar(0, 0), '░' * 10)
        self.assertEqual(self.formatter.progress_bar(15, 10), '█' * 10)  # Over 100%
    
    def test_format_number(self):
        """Test number formatting."""
        self.assertEqual(self.formatter.format_number(100), '100')
        self.assertEqual(self.formatter.format_number(1234), '1.2K')
        self.assertEqual(self.formatter.format_number(12345), '12.3K')
        self.assertEqual(self.formatter.format_number(1234567), '1.2M')
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        self.assertEqual(self.formatter.format_percentage(3.456), '3.46%')
        self.assertEqual(self.formatter.format_percentage(100.0), '100.00%')
    
    def test_format_date(self):
        """Test date formatting."""
        date = datetime(2024, 1, 15)
        
        # Short format
        self.assertEqual(self.formatter.format_date(date, 'short'), '15.01.2024')
        
        # Long format (Ukrainian)
        self.assertIn('січня', self.formatter.format_date(date, 'long'))
        self.assertIn('2024', self.formatter.format_date(date, 'long'))
    
    def test_format_time(self):
        """Test time formatting."""
        date = datetime(2024, 1, 15, 14, 30)
        self.assertEqual(self.formatter.format_time(date), '14:30')
    
    def test_format_change(self):
        """Test change formatting."""
        # Positive change
        result = self.formatter.format_change(150, 100)
        self.assertIn('+50', result)
        self.assertIn('⬆️', result)
        
        # Negative change
        result = self.formatter.format_change(90, 100)
        self.assertIn('-10', result)
        self.assertIn('⬇️', result)
        
        # No change
        result = self.formatter.format_change(100, 100)
        self.assertIn('без змін', result)
    
    def test_emoji_constants(self):
        """Test emoji constants are available."""
        self.assertIn('chart', self.formatter.EMOJI)
        self.assertIn('heart', self.formatter.EMOJI)
        self.assertIn('trophy', self.formatter.EMOJI)
        self.assertEqual(self.formatter.EMOJI['chart'], '📊')
        self.assertEqual(self.formatter.EMOJI['heart'], '❤️')
    
    def test_format_header(self):
        """Test header formatting."""
        header = self.formatter.format_header('Test Report', '📊')
        self.assertIn('Test Report', header)
        self.assertIn('📊', header)
        self.assertIn('═', header)
        self.assertIn('<b>', header)
    
    def test_format_section(self):
        """Test section formatting."""
        section = self.formatter.format_section('Test Section', '🏆')
        self.assertIn('Test Section', section)
        self.assertIn('🏆', section)
        self.assertIn('<b>', section)
    
    def test_format_target_progress(self):
        """Test target progress formatting."""
        progress = self.formatter.format_target_progress('Пости', 15, 20, '📷')
        self.assertIn('Пости', progress)
        self.assertIn('15/20', progress)
        self.assertIn('75%', progress)
        self.assertIn('📷', progress)
    
    def test_format_engagement_stats(self):
        """Test engagement stats formatting."""
        stats = self.formatter.format_engagement_stats(1234, 56, 78, 4.5)
        self.assertIn('Лайки', stats)
        self.assertIn('Коментарі', stats)
        self.assertIn('Збереження', stats)
        self.assertIn('Залученість', stats)
        self.assertIn('4.50%', stats)
    
    def test_format_recommendations(self):
        """Test recommendations formatting."""
        recs = ['Rec 1', 'Rec 2', 'Rec 3']
        formatted = self.formatter.format_recommendations(recs)
        self.assertIn('Рекомендації AI', formatted)
        self.assertIn('1. Rec 1', formatted)
        self.assertIn('2. Rec 2', formatted)
        
        # Empty recommendations
        empty = self.formatter.format_recommendations([])
        self.assertIn('поки немає', empty)
    
    def test_escape_html(self):
        """Test HTML escaping."""
        text = "Test <tag> & \"quote\""
        escaped = self.formatter.escape_html(text)
        self.assertIn('&lt;', escaped)
        self.assertIn('&gt;', escaped)
        self.assertIn('&amp;', escaped)


class TestTelegramBot(unittest.TestCase):
    """Test Telegram bot functionality."""
    
    def test_bot_initialization(self):
        """Test bot can be initialized."""
        bot = TelegramBot(token='test_token', chat_id='test_chat')
        self.assertEqual(bot.token, 'test_token')
        self.assertEqual(bot.chat_id, 'test_chat')
        self.assertIsNotNone(bot.formatter)
    
    def test_bot_requires_credentials(self):
        """Test bot requires token and chat_id."""
        # Test empty token raises ValueError
        with self.assertRaises(ValueError) as ctx:
            TelegramBot(token='', chat_id='test_chat')
        self.assertIn('TELEGRAM_BOT_TOKEN', str(ctx.exception))
        
        # Test empty chat_id raises ValueError
        with self.assertRaises(ValueError) as ctx:
            TelegramBot(token='test_token', chat_id='')
        self.assertIn('TELEGRAM_CHAT_ID', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
