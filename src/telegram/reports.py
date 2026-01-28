"""Report generators for daily, weekly, and monthly Telegram reports."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.database.repository import Repository
from src.database.models import Post, DailyStat
from src.telegram.formatters import MessageFormatter
from src.ai.recommendations import RecommendationGenerator
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseReport:
    """Base class for report generation."""
    
    def __init__(self, repository: Optional[Repository] = None):
        """
        Initialize base report.
        
        Args:
            repository: Database repository instance
        """
        self.repository = repository or Repository()
        self.formatter = MessageFormatter()
    
    def close(self):
        """Close repository connection."""
        if self.repository:
            self.repository.close()


class DailyReport(BaseReport):
    """Generate daily performance reports."""
    
    async def generate(self, date: Optional[datetime] = None) -> str:
        """
        Generate daily report for specified date.
        
        Args:
            date: Date for report (defaults to today)
            
        Returns:
            Formatted report message
        """
        if date is None:
            date = datetime.now()
        
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info(f"Generating daily report for {date:%Y-%m-%d}")
        
        # Get daily statistics
        daily_stat = self.repository.get_daily_stat(date)
        
        # Get posts for the day
        end_date = date + timedelta(days=1)
        posts = self.repository.get_posts_by_date_range(date, end_date)
        
        # Get stories count
        stories = self.repository.get_stories_by_date(date)
        
        # Load targets
        targets = settings.load_targets().get('targets', {})
        posts_target = targets.get('posts_per_month', 20) / 30  # Daily target
        stories_target = targets.get('stories_per_day', 3)
        
        # Build report
        report_parts = []
        
        # Header
        header = self.formatter.format_header(
            f"Звіт за {self.formatter.format_date(date, 'long')}",
            self.formatter.EMOJI['calendar']
        )
        report_parts.append(header)
        
        # Content published
        section = self.formatter.format_section("Опубліковано", self.formatter.EMOJI['camera'])
        report_parts.append(section)
        
        posts_count = len(posts)
        stories_count = len(stories)
        
        posts_emoji = self.formatter.EMOJI['checkmark'] if posts_count >= posts_target else self.formatter.EMOJI['cross']
        stories_emoji = self.formatter.EMOJI['checkmark'] if stories_count >= stories_target else self.formatter.EMOJI['cross']
        
        report_parts.append(
            f"{self.formatter.EMOJI['camera']} Пости: <b>{posts_count}</b> {posts_emoji}\n"
            f"{self.formatter.EMOJI['video']} Сторіс: <b>{stories_count}</b> {stories_emoji}"
        )
        
        # Engagement statistics
        if daily_stat:
            section = self.formatter.format_section("Статистика залученості", self.formatter.EMOJI['chart'])
            report_parts.append(section)
            
            engagement_text = self.formatter.format_engagement_stats(
                likes=daily_stat.total_likes,
                comments=daily_stat.total_comments,
                saves=daily_stat.total_saves,
                engagement_rate=daily_stat.avg_engagement_rate
            )
            report_parts.append(engagement_text)
            
            # Reach and impressions
            if daily_stat.total_reach > 0:
                report_parts.append(
                    f"\n{self.formatter.EMOJI['eye']} Охоплення: <b>{self.formatter.format_number(daily_stat.total_reach)}</b>\n"
                    f"{self.formatter.EMOJI['chart']} Покази: <b>{self.formatter.format_number(daily_stat.total_impressions)}</b>"
                )
            
            # Followers change
            if daily_stat.followers_change != 0:
                change_text = self.formatter.format_change(
                    daily_stat.followers_count,
                    daily_stat.followers_count - daily_stat.followers_change
                )
                report_parts.append(
                    f"\n{self.formatter.EMOJI['star']} Підписники: <b>{self.formatter.format_number(daily_stat.followers_count)}</b> {change_text}"
                )
        
        # Best post of the day
        if posts:
            best_post = max(posts, key=lambda p: p.engagement_rate)
            section = self.formatter.format_section("Найкращий пост дня", self.formatter.EMOJI['trophy'])
            report_parts.append(section)
            
            post_summary = self.formatter.format_post_summary(best_post)
            report_parts.append(post_summary)
        
        # AI Recommendations
        try:
            rec_gen = RecommendationGenerator()
            recommendations_text = rec_gen.generate_general_recommendations(period_days=1)
            rec_gen.close()
            
            if recommendations_text:
                section = self.formatter.format_section("Рекомендації", self.formatter.EMOJI['bulb'])
                report_parts.append(section)
                
                # Parse recommendations (simple split by newlines)
                rec_lines = [line.strip() for line in recommendations_text.split('\n') if line.strip()]
                formatted_recs = self.formatter.format_recommendations(rec_lines[:3])  # Top 3
                report_parts.append(formatted_recs)
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        # Alerts for missed targets
        alerts = []
        if posts_count < posts_target:
            alerts.append("Не досягнуто денного ліміту постів")
        if stories_count < stories_target:
            alerts.append("Не досягнуто денного ліміту сторіс")
        
        if alerts:
            section = self.formatter.format_section("Попередження", self.formatter.EMOJI['warning'])
            report_parts.append(section)
            for alert in alerts:
                report_parts.append(self.formatter.format_alert(alert, 'warning'))
        
        # Footer
        report_parts.append(
            f"\n{self.formatter.EMOJI['rocket']} Продовжуйте у тому ж дусі!"
        )
        
        return "\n".join(report_parts)


class WeeklyReport(BaseReport):
    """Generate weekly performance reports."""
    
    async def generate(self, end_date: Optional[datetime] = None) -> str:
        """
        Generate weekly report.
        
        Args:
            end_date: End date of week (defaults to today)
            
        Returns:
            Formatted report message
        """
        if end_date is None:
            end_date = datetime.now()
        
        end_date = end_date.replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=6)).replace(hour=0, minute=0, second=0)
        
        logger.info(f"Generating weekly report for {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}")
        
        # Get weekly data
        posts = self.repository.get_posts_by_date_range(start_date, end_date)
        daily_stats = self.repository.get_daily_stats_range(start_date, end_date)
        
        # Previous week data for comparison
        prev_week_start = start_date - timedelta(days=7)
        prev_week_end = end_date - timedelta(days=7)
        prev_posts = self.repository.get_posts_by_date_range(prev_week_start, prev_week_end)
        prev_stats = self.repository.get_daily_stats_range(prev_week_start, prev_week_end)
        
        # Load targets
        targets = settings.load_targets().get('targets', {})
        weekly_posts_target = targets.get('posts_per_month', 20) / 4
        weekly_reels_target = targets.get('reels_per_week', 2)
        weekly_stories_target = targets.get('stories_per_day', 3) * 7
        
        # Build report
        report_parts = []
        
        # Header
        header = self.formatter.format_header(
            f"Тижневий звіт\n{self.formatter.format_date(start_date)} - {self.formatter.format_date(end_date)}",
            self.formatter.EMOJI['chart']
        )
        report_parts.append(header)
        
        # Target completion
        section = self.formatter.format_section("Виконання цілей", self.formatter.EMOJI['target'])
        report_parts.append(section)
        
        posts_count = len(posts)
        stories_count = sum(s.stories_count for s in daily_stats) if daily_stats else 0
        reels_count = sum(s.reels_count for s in daily_stats) if daily_stats else 0
        
        # Progress bars for each target
        posts_progress = self.formatter.format_target_progress(
            "Пости",
            posts_count,
            int(weekly_posts_target),
            self.formatter.EMOJI['camera']
        )
        report_parts.append(posts_progress)
        
        stories_progress = self.formatter.format_target_progress(
            "Сторіс",
            stories_count,
            int(weekly_stories_target),
            self.formatter.EMOJI['video']
        )
        report_parts.append(stories_progress)
        
        reels_progress = self.formatter.format_target_progress(
            "Reels",
            reels_count,
            weekly_reels_target,
            self.formatter.EMOJI['fire']
        )
        report_parts.append(reels_progress)
        
        # Top 3 posts
        if posts:
            section = self.formatter.format_section("Топ-3 пости тижня", self.formatter.EMOJI['trophy'])
            report_parts.append(section)
            
            top_posts = sorted(posts, key=lambda p: p.engagement_rate, reverse=True)[:3]
            for rank, post in enumerate(top_posts, 1):
                post_summary = self.formatter.format_post_summary(post, rank)
                report_parts.append(f"\n{post_summary}")
        
        # Comparison with last week
        if daily_stats and prev_stats:
            section = self.formatter.format_section("Порівняння з минулим тижнем", self.formatter.EMOJI['growth'])
            report_parts.append(section)
            
            # Calculate averages
            current_avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
            prev_avg_engagement = sum(s.avg_engagement_rate for s in prev_stats) / len(prev_stats) if prev_stats else 0
            
            current_total_likes = sum(s.total_likes for s in daily_stats)
            prev_total_likes = sum(s.total_likes for s in prev_stats) if prev_stats else 0
            
            current_total_comments = sum(s.total_comments for s in daily_stats)
            prev_total_comments = sum(s.total_comments for s in prev_stats) if prev_stats else 0
            
            # Format comparisons
            engagement_comp = self.formatter.format_comparison(
                "Залученість",
                current_avg_engagement,
                prev_avg_engagement,
                is_percentage=True
            )
            report_parts.append(engagement_comp)
            
            likes_comp = self.formatter.format_comparison(
                "Лайки",
                current_total_likes,
                prev_total_likes
            )
            report_parts.append(likes_comp)
            
            comments_comp = self.formatter.format_comparison(
                "Коментарі",
                current_total_comments,
                prev_total_comments
            )
            report_parts.append(comments_comp)
            
            posts_comp = self.formatter.format_comparison(
                "Пости",
                posts_count,
                len(prev_posts)
            )
            report_parts.append(posts_comp)
        
        # Engagement statistics
        if daily_stats:
            total_likes = sum(s.total_likes for s in daily_stats)
            total_comments = sum(s.total_comments for s in daily_stats)
            total_saves = sum(s.total_saves for s in daily_stats)
            avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
            
            section = self.formatter.format_section("Статистика залученості", self.formatter.EMOJI['chart'])
            report_parts.append(section)
            
            engagement_text = self.formatter.format_engagement_stats(
                likes=total_likes,
                comments=total_comments,
                saves=total_saves,
                engagement_rate=avg_engagement
            )
            report_parts.append(engagement_text)
        
        # AI Recommendations
        try:
            rec_gen = RecommendationGenerator()
            recommendations_text = rec_gen.generate_general_recommendations(period_days=7)
            rec_gen.close()
            
            if recommendations_text:
                section = self.formatter.format_section("Рекомендації на наступний тиждень", self.formatter.EMOJI['bulb'])
                report_parts.append(section)
                
                rec_lines = [line.strip() for line in recommendations_text.split('\n') if line.strip()]
                formatted_recs = self.formatter.format_recommendations(rec_lines[:5])
                report_parts.append(formatted_recs)
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        # Footer
        report_parts.append(
            f"\n{self.formatter.EMOJI['star']} Чудова робота! Продовжуймо у наступному тижні!"
        )
        
        return "\n".join(report_parts)


class MonthlyReport(BaseReport):
    """Generate monthly performance reports."""
    
    async def generate(self, month: Optional[datetime] = None) -> str:
        """
        Generate monthly report.
        
        Args:
            month: Month for report (defaults to current month)
            
        Returns:
            Formatted report message
        """
        if month is None:
            month = datetime.now()
        
        # Get first and last day of month
        start_date = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last day of month
        if month.month == 12:
            end_date = start_date.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=month.month + 1, day=1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
        logger.info(f"Generating monthly report for {start_date:%B %Y}")
        
        # Get monthly data
        posts = self.repository.get_posts_by_date_range(start_date, end_date)
        daily_stats = self.repository.get_daily_stats_range(start_date, end_date)
        
        # Previous month data
        if start_date.month == 1:
            prev_month_start = start_date.replace(year=start_date.year - 1, month=12, day=1)
        else:
            prev_month_start = start_date.replace(month=start_date.month - 1, day=1)
        
        if prev_month_start.month == 12:
            prev_month_end = prev_month_start.replace(year=prev_month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            prev_month_end = prev_month_start.replace(month=prev_month_start.month + 1, day=1) - timedelta(days=1)
        
        prev_posts = self.repository.get_posts_by_date_range(prev_month_start, prev_month_end)
        prev_stats = self.repository.get_daily_stats_range(prev_month_start, prev_month_end)
        
        # Load targets
        targets = settings.load_targets().get('targets', {})
        monthly_posts_target = targets.get('posts_per_month', 20)
        min_engagement_rate = targets.get('min_engagement_rate', 3.5)
        
        # Build report
        report_parts = []
        
        # Header
        months_ua = {
            1: 'Січень', 2: 'Лютий', 3: 'Березень', 4: 'Квітень',
            5: 'Травень', 6: 'Червень', 7: 'Липень', 8: 'Серпень',
            9: 'Вересень', 10: 'Жовтень', 11: 'Листопад', 12: 'Грудень'
        }
        month_name = months_ua[start_date.month]
        
        header = self.formatter.format_header(
            f"Місячний звіт\n{month_name} {start_date.year}",
            self.formatter.EMOJI['chart']
        )
        report_parts.append(header)
        
        # Summary statistics
        section = self.formatter.format_section("Загальна статистика", self.formatter.EMOJI['book'])
        report_parts.append(section)
        
        posts_count = len(posts)
        stories_count = sum(s.stories_count for s in daily_stats) if daily_stats else 0
        reels_count = sum(s.reels_count for s in daily_stats) if daily_stats else 0
        
        report_parts.append(
            f"{self.formatter.EMOJI['camera']} Пости: <b>{posts_count}</b>\n"
            f"{self.formatter.EMOJI['video']} Сторіс: <b>{stories_count}</b>\n"
            f"{self.formatter.EMOJI['fire']} Reels: <b>{reels_count}</b>"
        )
        
        # Target achievement
        posts_target_met = posts_count >= monthly_posts_target
        target_emoji = self.formatter.EMOJI['checkmark'] if posts_target_met else self.formatter.EMOJI['cross']
        
        report_parts.append(
            f"\n{self.formatter.EMOJI['target']} Ціль постів: {target_emoji} "
            f"<b>{posts_count}/{monthly_posts_target}</b>"
        )
        
        # Engagement statistics
        if daily_stats:
            total_likes = sum(s.total_likes for s in daily_stats)
            total_comments = sum(s.total_comments for s in daily_stats)
            total_saves = sum(s.total_saves for s in daily_stats)
            total_reach = sum(s.total_reach for s in daily_stats)
            total_impressions = sum(s.total_impressions for s in daily_stats)
            avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
            
            section = self.formatter.format_section("Залученість", self.formatter.EMOJI['heart'])
            report_parts.append(section)
            
            engagement_text = self.formatter.format_engagement_stats(
                likes=total_likes,
                comments=total_comments,
                saves=total_saves,
                engagement_rate=avg_engagement
            )
            report_parts.append(engagement_text)
            
            if total_reach > 0:
                report_parts.append(
                    f"\n{self.formatter.EMOJI['eye']} Охоплення: <b>{self.formatter.format_number(total_reach)}</b>\n"
                    f"{self.formatter.EMOJI['chart']} Покази: <b>{self.formatter.format_number(total_impressions)}</b>"
                )
        
        # Follower growth
        if daily_stats:
            first_stat = daily_stats[0]
            last_stat = daily_stats[-1]
            
            follower_change = last_stat.followers_count - first_stat.followers_count
            
            section = self.formatter.format_section("Ріст аудиторії", self.formatter.EMOJI['growth'])
            report_parts.append(section)
            
            change_text = self.formatter.format_change(
                last_stat.followers_count,
                first_stat.followers_count
            )
            
            report_parts.append(
                f"{self.formatter.EMOJI['star']} Підписники на кінець місяця: "
                f"<b>{self.formatter.format_number(last_stat.followers_count)}</b>\n"
                f"Зміна за місяць: {change_text}"
            )
        
        # Top performing posts
        if posts:
            section = self.formatter.format_section("Топ-5 постів місяця", self.formatter.EMOJI['medal'])
            report_parts.append(section)
            
            top_posts = sorted(posts, key=lambda p: p.engagement_rate, reverse=True)[:5]
            for rank, post in enumerate(top_posts, 1):
                post_summary = self.formatter.format_post_summary(post, rank)
                report_parts.append(f"\n{post_summary}")
        
        # Trends and comparison
        if daily_stats and prev_stats:
            section = self.formatter.format_section("Тренди та порівняння", self.formatter.EMOJI['growth'])
            report_parts.append(section)
            
            current_avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
            prev_avg_engagement = sum(s.avg_engagement_rate for s in prev_stats) / len(prev_stats) if prev_stats else 0
            
            engagement_comp = self.formatter.format_comparison(
                "Середня залученість",
                current_avg_engagement,
                prev_avg_engagement,
                is_percentage=True
            )
            report_parts.append(engagement_comp)
            
            posts_comp = self.formatter.format_comparison(
                "Кількість постів",
                posts_count,
                len(prev_posts)
            )
            report_parts.append(posts_comp)
        
        # AI Recommendations
        try:
            rec_gen = RecommendationGenerator()
            recommendations_text = rec_gen.generate_general_recommendations(period_days=30)
            rec_gen.close()
            
            if recommendations_text:
                section = self.formatter.format_section("Рекомендації на наступний місяць", self.formatter.EMOJI['bulb'])
                report_parts.append(section)
                
                rec_lines = [line.strip() for line in recommendations_text.split('\n') if line.strip()]
                formatted_recs = self.formatter.format_recommendations(rec_lines[:5])
                report_parts.append(formatted_recs)
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        # Performance insights
        section = self.formatter.format_section("Інсайти", self.formatter.EMOJI['bulb'])
        report_parts.append(section)
        
        insights = []
        
        if daily_stats:
            avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
            if avg_engagement >= min_engagement_rate:
                insights.append(f"{self.formatter.EMOJI['checkmark']} Відмінна залученість аудиторії!")
            else:
                insights.append(f"{self.formatter.EMOJI['warning']} Залученість нижче цільової ({min_engagement_rate}%)")
        
        if posts_count >= monthly_posts_target:
            insights.append(f"{self.formatter.EMOJI['checkmark']} Виконано місячну ціль по постам!")
        else:
            missing = monthly_posts_target - posts_count
            insights.append(f"{self.formatter.EMOJI['cross']} Не вистачає {missing} постів до цілі")
        
        if insights:
            report_parts.append("\n".join(insights))
        
        # Footer
        report_parts.append(
            f"\n{self.formatter.EMOJI['rocket']} Дякуємо за відмінну роботу! "
            f"Продовжуймо розвиватись!"
        )
        
        return "\n".join(report_parts)
