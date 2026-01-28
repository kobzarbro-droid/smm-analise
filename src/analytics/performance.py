"""Performance metrics analysis for Instagram content."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from sqlalchemy import func
from src.database.repository import Repository
from src.database.models import Post, Reel, DailyStat
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceAnalyzer:
    """Analyzer for content performance metrics and trends."""
    
    def __init__(self, repository: Optional[Repository] = None):
        """
        Initialize performance analyzer.
        
        Args:
            repository: Repository instance (creates new one if not provided)
        """
        self.repository = repository or Repository()
    
    def analyze_engagement_trends(
        self, 
        days: int = 30,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze engagement trends over time.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis (defaults to today)
            
        Returns:
            Dictionary with engagement trend data
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Analyzing engagement trends from {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}")
            
            # Get posts in date range
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу',
                    'period': {'start': start_date, 'end': end_date}
                }
            
            # Group by date
            daily_data = defaultdict(lambda: {
                'posts': [],
                'total_likes': 0,
                'total_comments': 0,
                'total_engagement': 0,
                'avg_engagement_rate': 0
            })
            
            for post in posts:
                date_key = post.posted_at.date()
                daily_data[date_key]['posts'].append(post)
                daily_data[date_key]['total_likes'] += post.likes_count
                daily_data[date_key]['total_comments'] += post.comments_count
            
            # Calculate daily metrics
            timeline = []
            for date in sorted(daily_data.keys()):
                data = daily_data[date]
                posts_list = data['posts']
                
                avg_engagement = sum(p.engagement_rate for p in posts_list) / len(posts_list)
                
                timeline.append({
                    'date': date.isoformat(),
                    'posts_count': len(posts_list),
                    'total_likes': data['total_likes'],
                    'total_comments': data['total_comments'],
                    'avg_engagement_rate': round(avg_engagement, 2)
                })
            
            # Calculate trend direction
            if len(timeline) >= 2:
                recent_avg = sum(d['avg_engagement_rate'] for d in timeline[-7:]) / min(7, len(timeline[-7:]))
                older_avg = sum(d['avg_engagement_rate'] for d in timeline[:7]) / min(7, len(timeline[:7]))
                trend_direction = 'зростання' if recent_avg > older_avg else 'спадання' if recent_avg < older_avg else 'стабільно'
                trend_change = round(((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0, 1)
            else:
                trend_direction = 'недостатньо даних'
                trend_change = 0
            
            # Overall statistics
            total_posts = len(posts)
            avg_engagement = sum(p.engagement_rate for p in posts) / total_posts
            total_likes = sum(p.likes_count for p in posts)
            total_comments = sum(p.comments_count for p in posts)
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'timeline': timeline,
                'summary': {
                    'total_posts': total_posts,
                    'avg_engagement_rate': round(avg_engagement, 2),
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'avg_likes_per_post': round(total_likes / total_posts, 0),
                    'avg_comments_per_post': round(total_comments / total_posts, 0)
                },
                'trend': {
                    'direction': trend_direction,
                    'change_percent': trend_change
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing engagement trends: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def find_best_posting_times(
        self, 
        days: int = 90,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Find best posting times based on historical performance.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            
        Returns:
            Dictionary with best posting times by hour and day of week
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Analyzing posting times from {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}")
            
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу'
                }
            
            # Group by hour and day of week
            hour_stats = defaultdict(lambda: {'posts': [], 'total_engagement': 0})
            weekday_stats = defaultdict(lambda: {'posts': [], 'total_engagement': 0})
            
            for post in posts:
                hour = post.posted_at.hour
                weekday = post.posted_at.weekday()
                
                hour_stats[hour]['posts'].append(post)
                hour_stats[hour]['total_engagement'] += post.engagement_rate
                
                weekday_stats[weekday]['posts'].append(post)
                weekday_stats[weekday]['total_engagement'] += post.engagement_rate
            
            # Calculate average engagement by hour
            hours_data = []
            for hour in range(24):
                if hour in hour_stats:
                    data = hour_stats[hour]
                    avg_engagement = data['total_engagement'] / len(data['posts'])
                    hours_data.append({
                        'hour': hour,
                        'posts_count': len(data['posts']),
                        'avg_engagement_rate': round(avg_engagement, 2)
                    })
            
            # Sort and get top hours
            best_hours = sorted(hours_data, key=lambda x: x['avg_engagement_rate'], reverse=True)[:5]
            
            # Calculate average engagement by weekday
            weekday_names = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця', 'Субота', 'Неділя']
            weekdays_data = []
            
            for day in range(7):
                if day in weekday_stats:
                    data = weekday_stats[day]
                    avg_engagement = data['total_engagement'] / len(data['posts'])
                    weekdays_data.append({
                        'day': day,
                        'day_name': weekday_names[day],
                        'posts_count': len(data['posts']),
                        'avg_engagement_rate': round(avg_engagement, 2)
                    })
            
            # Sort and get best days
            best_days = sorted(weekdays_data, key=lambda x: x['avg_engagement_rate'], reverse=True)[:3]
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'best_hours': best_hours,
                'best_days': best_days,
                'all_hours': sorted(hours_data, key=lambda x: x['hour']),
                'all_days': weekdays_data,
                'recommendations': self._generate_timing_recommendations(best_hours, best_days)
            }
            
        except Exception as e:
            logger.error(f"Error finding best posting times: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def analyze_content_type_performance(
        self,
        days: int = 30,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance by content type (photo, video, carousel).
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            
        Returns:
            Dictionary with content type performance data
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Analyzing content types from {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}")
            
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу'
                }
            
            # Group by media type
            type_stats = defaultdict(lambda: {
                'posts': [],
                'total_likes': 0,
                'total_comments': 0,
                'total_saves': 0,
                'total_reach': 0
            })
            
            for post in posts:
                media_type = post.media_type or 'photo'
                type_stats[media_type]['posts'].append(post)
                type_stats[media_type]['total_likes'] += post.likes_count
                type_stats[media_type]['total_comments'] += post.comments_count
                type_stats[media_type]['total_saves'] += post.saves_count
                type_stats[media_type]['total_reach'] += post.reach
            
            # Calculate metrics for each type
            type_names = {
                'photo': 'Фото',
                'video': 'Відео',
                'carousel': 'Карусель'
            }
            
            content_types = []
            for media_type, data in type_stats.items():
                posts_list = data['posts']
                count = len(posts_list)
                
                avg_engagement = sum(p.engagement_rate for p in posts_list) / count
                avg_likes = data['total_likes'] / count
                avg_comments = data['total_comments'] / count
                avg_saves = data['total_saves'] / count
                avg_reach = data['total_reach'] / count if data['total_reach'] > 0 else 0
                
                content_types.append({
                    'type': media_type,
                    'type_name': type_names.get(media_type, media_type.capitalize()),
                    'count': count,
                    'avg_engagement_rate': round(avg_engagement, 2),
                    'avg_likes': round(avg_likes, 0),
                    'avg_comments': round(avg_comments, 0),
                    'avg_saves': round(avg_saves, 0),
                    'avg_reach': round(avg_reach, 0),
                    'total_likes': data['total_likes'],
                    'total_comments': data['total_comments']
                })
            
            # Sort by engagement rate
            content_types.sort(key=lambda x: x['avg_engagement_rate'], reverse=True)
            
            # Find best performing type
            best_type = content_types[0] if content_types else None
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'content_types': content_types,
                'best_performing_type': best_type,
                'recommendations': self._generate_content_type_recommendations(content_types)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content type performance: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_top_performing_posts(
        self,
        limit: int = 10,
        days: int = 30,
        end_date: Optional[datetime] = None,
        metric: str = 'engagement_rate'
    ) -> Dict[str, Any]:
        """
        Get top performing posts.
        
        Args:
            limit: Number of posts to return
            days: Number of days to analyze
            end_date: End date for analysis
            metric: Metric to sort by (engagement_rate, likes_count, comments_count)
            
        Returns:
            Dictionary with top performing posts
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Getting top {limit} posts by {metric}")
            
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу'
                }
            
            # Sort by specified metric
            metric_map = {
                'engagement_rate': lambda p: p.engagement_rate,
                'likes_count': lambda p: p.likes_count,
                'comments_count': lambda p: p.comments_count,
                'saves_count': lambda p: p.saves_count,
                'reach': lambda p: p.reach
            }
            
            sort_func = metric_map.get(metric, lambda p: p.engagement_rate)
            sorted_posts = sorted(posts, key=sort_func, reverse=True)[:limit]
            
            # Format posts data
            top_posts = []
            for post in sorted_posts:
                top_posts.append({
                    'post_id': post.post_id,
                    'posted_at': post.posted_at.isoformat(),
                    'media_type': post.media_type,
                    'caption': post.caption[:100] + '...' if post.caption and len(post.caption) > 100 else post.caption,
                    'hashtags': post.hashtags,
                    'likes_count': post.likes_count,
                    'comments_count': post.comments_count,
                    'saves_count': post.saves_count,
                    'reach': post.reach,
                    'engagement_rate': round(post.engagement_rate, 2),
                    'thumbnail_url': post.thumbnail_url
                })
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'metric': metric,
                'top_posts': top_posts
            }
            
        except Exception as e:
            logger.error(f"Error getting top performing posts: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_performance_insights(
        self,
        days: int = 30,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance insights.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            
        Returns:
            Dictionary with comprehensive insights and recommendations
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info("Generating performance insights")
            
            # Get engagement trends
            trends = self.analyze_engagement_trends(days, end_date)
            
            # Get best posting times
            timing = self.find_best_posting_times(min(days * 2, 90), end_date)
            
            # Get content type performance
            content = self.analyze_content_type_performance(days, end_date)
            
            # Get top posts
            top_posts = self.get_top_performing_posts(5, days, end_date)
            
            # Generate insights
            insights = []
            
            if trends.get('status') == 'success':
                trend_data = trends.get('trend', {})
                summary = trends.get('summary', {})
                
                if trend_data.get('direction') == 'зростання':
                    insights.append({
                        'type': 'positive',
                        'title': 'Зростання залученості',
                        'message': f"Ваша залученість зросла на {trend_data.get('change_percent', 0)}% за останній період. Продовжуйте в тому ж дусі!"
                    })
                elif trend_data.get('direction') == 'спадання':
                    insights.append({
                        'type': 'warning',
                        'title': 'Зниження залученості',
                        'message': f"Залученість знизилась на {abs(trend_data.get('change_percent', 0))}%. Спробуйте змінити контент-стратегію."
                    })
                
                avg_engagement = summary.get('avg_engagement_rate', 0)
                if avg_engagement > 5:
                    insights.append({
                        'type': 'positive',
                        'title': 'Відмінна залученість',
                        'message': f"Середній рівень залученості {avg_engagement}% - це чудовий результат!"
                    })
                elif avg_engagement < 2:
                    insights.append({
                        'type': 'warning',
                        'title': 'Низька залученість',
                        'message': f"Середній рівень залученості {avg_engagement}% - потрібно покращити контент."
                    })
            
            if timing.get('status') == 'success' and timing.get('best_hours'):
                best_hour = timing['best_hours'][0]
                insights.append({
                    'type': 'info',
                    'title': 'Кращий час для публікацій',
                    'message': f"Найвища залученість о {best_hour['hour']:02d}:00 ({best_hour['avg_engagement_rate']}%)"
                })
            
            if content.get('status') == 'success' and content.get('best_performing_type'):
                best = content['best_performing_type']
                insights.append({
                    'type': 'info',
                    'title': 'Кращий тип контенту',
                    'message': f"{best['type_name']} показує найкращі результати ({best['avg_engagement_rate']}% залученості)"
                })
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'insights': insights,
                'trends': trends,
                'timing': timing,
                'content_types': content,
                'top_posts': top_posts
            }
            
        except Exception as e:
            logger.error(f"Error generating performance insights: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _generate_timing_recommendations(
        self, 
        best_hours: List[Dict[str, Any]], 
        best_days: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for posting times."""
        recommendations = []
        
        if best_hours:
            top_hours = [f"{h['hour']:02d}:00" for h in best_hours[:3]]
            recommendations.append(
                f"Публікуйте пости в годинах: {', '.join(top_hours)} для максимальної залученості"
            )
        
        if best_days:
            top_days = [d['day_name'] for d in best_days[:2]]
            recommendations.append(
                f"Найкращі дні для публікацій: {', '.join(top_days)}"
            )
        
        return recommendations
    
    def _generate_content_type_recommendations(
        self, 
        content_types: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for content types."""
        recommendations = []
        
        if not content_types:
            return recommendations
        
        best = content_types[0]
        recommendations.append(
            f"Фокусуйтеся на {best['type_name']}: найвища залученість {best['avg_engagement_rate']}%"
        )
        
        # Find underperforming types
        if len(content_types) > 1:
            worst = content_types[-1]
            if worst['avg_engagement_rate'] < best['avg_engagement_rate'] * 0.5:
                recommendations.append(
                    f"Покращіть якість {worst['type_name']} або зменште їх кількість"
                )
        
        return recommendations
    
    def close(self):
        """Close repository connection."""
        if self.repository:
            self.repository.close()
