"""Message formatting utilities for Telegram bot."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.database.models import Post


class MessageFormatter:
    """Format messages for Telegram with Ukrainian text and emoji."""
    
    # Emoji constants
    EMOJI = {
        'chart': '📊',
        'growth': '📈',
        'decline': '📉',
        'comment': '💬',
        'heart': '❤️',
        'fire': '🔥',
        'trophy': '🏆',
        'star': '⭐',
        'target': '🎯',
        'calendar': '📅',
        'clock': '🕐',
        'checkmark': '✅',
        'cross': '❌',
        'warning': '⚠️',
        'camera': '📷',
        'video': '🎬',
        'book': '📖',
        'bulb': '💡',
        'rocket': '🚀',
        'medal': '🥇',
        'up': '⬆️',
        'down': '⬇️',
        'eye': '👁️',
        'save': '💾',
        'share': '📤',
        'hashtag': '#️⃣'
    }
    
    @staticmethod
    def progress_bar(current: int, target: int, length: int = 10) -> str:
        """
        Create a visual progress bar.
        
        Args:
            current: Current value
            target: Target value
            length: Length of progress bar
            
        Returns:
            Progress bar string
        """
        if target <= 0:
            return '░' * length
        
        percentage = min(current / target, 1.0)
        filled = int(percentage * length)
        empty = length - filled
        
        return '█' * filled + '░' * empty
    
    @staticmethod
    def format_number(number: int) -> str:
        """
        Format large numbers with K/M suffixes.
        
        Args:
            number: Number to format
            
        Returns:
            Formatted string
        """
        if number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.1f}K"
        return str(number)
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """
        Format percentage with color indicator.
        
        Args:
            value: Percentage value
            
        Returns:
            Formatted percentage string
        """
        return f"{value:.2f}%"
    
    @staticmethod
    def format_date(date: datetime, format_type: str = 'short') -> str:
        """
        Format date in Ukrainian.
        
        Args:
            date: Date to format
            format_type: 'short' or 'long'
            
        Returns:
            Formatted date string
        """
        months_ua = {
            1: 'січня', 2: 'лютого', 3: 'березня', 4: 'квітня',
            5: 'травня', 6: 'червня', 7: 'липня', 8: 'серпня',
            9: 'вересня', 10: 'жовтня', 11: 'листопада', 12: 'грудня'
        }
        
        if format_type == 'long':
            return f"{date.day} {months_ua[date.month]} {date.year}"
        return f"{date:%d.%m.%Y}"
    
    @staticmethod
    def format_time(date: datetime) -> str:
        """Format time in HH:MM format."""
        return f"{date:%H:%M}"
    
    @staticmethod
    def format_change(current: int, previous: int) -> str:
        """
        Format change with arrow and percentage.
        
        Args:
            current: Current value
            previous: Previous value
            
        Returns:
            Formatted change string
        """
        if previous == 0:
            return f"{MessageFormatter.EMOJI['up']} +{current}"
        
        change = current - previous
        percentage = (change / previous) * 100
        
        if change > 0:
            emoji = MessageFormatter.EMOJI['up']
            return f"{emoji} +{change} (+{percentage:.1f}%)"
        elif change < 0:
            emoji = MessageFormatter.EMOJI['down']
            return f"{emoji} {change} ({percentage:.1f}%)"
        else:
            return "без змін"
    
    @classmethod
    def format_post_summary(cls, post: Post, rank: Optional[int] = None) -> str:
        """
        Format post summary for reports.
        
        Args:
            post: Post object
            rank: Optional rank number
            
        Returns:
            Formatted post summary
        """
        rank_emoji = {1: cls.EMOJI['medal'], 2: '🥈', 3: '🥉'}.get(rank, cls.EMOJI['trophy'])
        rank_text = f"{rank_emoji} " if rank else ""
        
        # Format caption (first 50 chars)
        caption = post.caption or "Без опису"
        if len(caption) > 50:
            caption = caption[:47] + "..."
        
        # Format metrics
        likes = cls.format_number(post.likes_count)
        comments = cls.format_number(post.comments_count)
        engagement = cls.format_percentage(post.engagement_rate)
        
        return (
            f"{rank_text}<b>{caption}</b>\n"
            f"{cls.EMOJI['heart']} {likes} "
            f"{cls.EMOJI['comment']} {comments} "
            f"{cls.EMOJI['chart']} {engagement}\n"
            f"{cls.EMOJI['calendar']} {cls.format_date(post.posted_at)}"
        )
    
    @classmethod
    def format_target_progress(cls, name: str, current: int, target: int, 
                               emoji: str = '📊') -> str:
        """
        Format target progress with progress bar.
        
        Args:
            name: Target name in Ukrainian
            current: Current value
            target: Target value
            emoji: Emoji for the target
            
        Returns:
            Formatted progress string
        """
        percentage = (current / target * 100) if target > 0 else 0
        progress = cls.progress_bar(current, target)
        status = cls.EMOJI['checkmark'] if current >= target else ""
        
        return (
            f"{emoji} <b>{name}</b> {status}\n"
            f"{progress} {current}/{target} ({percentage:.0f}%)"
        )
    
    @classmethod
    def format_engagement_stats(cls, likes: int, comments: int, saves: int,
                                engagement_rate: float) -> str:
        """
        Format engagement statistics.
        
        Args:
            likes: Number of likes
            comments: Number of comments
            saves: Number of saves
            engagement_rate: Engagement rate
            
        Returns:
            Formatted stats string
        """
        return (
            f"{cls.EMOJI['heart']} Лайки: <b>{cls.format_number(likes)}</b>\n"
            f"{cls.EMOJI['comment']} Коментарі: <b>{cls.format_number(comments)}</b>\n"
            f"{cls.EMOJI['save']} Збереження: <b>{cls.format_number(saves)}</b>\n"
            f"{cls.EMOJI['chart']} Залученість: <b>{cls.format_percentage(engagement_rate)}</b>"
        )
    
    @classmethod
    def format_recommendations(cls, recommendations: List[str]) -> str:
        """
        Format AI recommendations list.
        
        Args:
            recommendations: List of recommendation strings
            
        Returns:
            Formatted recommendations
        """
        if not recommendations:
            return f"{cls.EMOJI['bulb']} Рекомендацій поки немає"
        
        formatted = f"{cls.EMOJI['bulb']} <b>Рекомендації AI:</b>\n\n"
        for i, rec in enumerate(recommendations, 1):
            formatted += f"{i}. {rec}\n"
        
        return formatted.strip()
    
    @classmethod
    def escape_html(cls, text: str) -> str:
        """
        Escape HTML special characters for Telegram.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        if not text:
            return ""
        
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    @classmethod
    def format_header(cls, title: str, emoji: str = '📊') -> str:
        """
        Format report header.
        
        Args:
            title: Header title
            emoji: Header emoji
            
        Returns:
            Formatted header
        """
        line = "═" * 25
        return f"{line}\n{emoji} <b>{title}</b> {emoji}\n{line}"
    
    @classmethod
    def format_section(cls, title: str, emoji: str = '▪️') -> str:
        """
        Format section title.
        
        Args:
            title: Section title
            emoji: Section emoji
            
        Returns:
            Formatted section
        """
        return f"\n{emoji} <b>{title}</b>"
    
    @classmethod
    def format_comparison(cls, label: str, current: float, previous: float,
                         is_percentage: bool = False) -> str:
        """
        Format comparison between two values.
        
        Args:
            label: Label for the metric
            current: Current value
            previous: Previous value
            is_percentage: Whether values are percentages
            
        Returns:
            Formatted comparison
        """
        if is_percentage:
            current_str = cls.format_percentage(current)
            previous_str = cls.format_percentage(previous)
        else:
            current_str = cls.format_number(int(current))
            previous_str = cls.format_number(int(previous))
        
        change = current - previous
        if change > 0:
            change_emoji = cls.EMOJI['up']
            change_text = f"+{cls.format_number(int(change))}" if not is_percentage else f"+{change:.2f}%"
        elif change < 0:
            change_emoji = cls.EMOJI['down']
            change_text = f"{cls.format_number(int(change))}" if not is_percentage else f"{change:.2f}%"
        else:
            change_emoji = "➡️"
            change_text = "без змін"
        
        return (
            f"{label}: <b>{current_str}</b> "
            f"(було: {previous_str}) {change_emoji} {change_text}"
        )
    
    @classmethod
    def format_alert(cls, message: str, level: str = 'warning') -> str:
        """
        Format alert message.
        
        Args:
            message: Alert message
            level: Alert level ('warning', 'error', 'info')
            
        Returns:
            Formatted alert
        """
        emoji_map = {
            'warning': cls.EMOJI['warning'],
            'error': cls.EMOJI['cross'],
            'info': 'ℹ️'
        }
        
        emoji = emoji_map.get(level, cls.EMOJI['warning'])
        return f"{emoji} <b>Увага:</b> {message}"
