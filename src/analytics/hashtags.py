"""Hashtag analytics and recommendations."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, Counter
from src.database.repository import Repository
from src.database.models import Hashtag, Post
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HashtagAnalyzer:
    """Analyzer for hashtag performance and recommendations."""
    
    def __init__(self, repository: Optional[Repository] = None):
        """
        Initialize hashtag analyzer.
        
        Args:
            repository: Repository instance (creates new one if not provided)
        """
        self.repository = repository or Repository()
    
    def analyze_hashtag_effectiveness(
        self,
        days: int = 30,
        end_date: Optional[datetime] = None,
        min_usage: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze hashtag effectiveness based on historical performance.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            min_usage: Minimum usage count to include hashtag
            
        Returns:
            Dictionary with hashtag effectiveness data
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Analyzing hashtag effectiveness from {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}")
            
            # Get posts in date range
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу'
                }
            
            # Collect hashtag statistics
            hashtag_stats = defaultdict(lambda: {
                'usage_count': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_reach': 0,
                'total_engagement': 0,
                'posts': []
            })
            
            for post in posts:
                if not post.hashtags:
                    continue
                
                hashtags = post.hashtags if isinstance(post.hashtags, list) else []
                
                for tag in hashtags:
                    # Clean hashtag
                    clean_tag = tag.lstrip('#').lower()
                    
                    hashtag_stats[clean_tag]['usage_count'] += 1
                    hashtag_stats[clean_tag]['total_likes'] += post.likes_count
                    hashtag_stats[clean_tag]['total_comments'] += post.comments_count
                    hashtag_stats[clean_tag]['total_reach'] += post.reach
                    hashtag_stats[clean_tag]['total_engagement'] += post.engagement_rate
                    hashtag_stats[clean_tag]['posts'].append(post)
            
            # Calculate effectiveness metrics
            hashtags_analysis = []
            
            for tag, stats in hashtag_stats.items():
                usage = stats['usage_count']
                
                # Skip if below minimum usage
                if usage < min_usage:
                    continue
                
                avg_likes = stats['total_likes'] / usage
                avg_comments = stats['total_comments'] / usage
                avg_reach = stats['total_reach'] / usage if stats['total_reach'] > 0 else 0
                avg_engagement = stats['total_engagement'] / usage
                
                # Calculate effectiveness score (0-100)
                effectiveness_score = min(100, (avg_engagement * 10))
                
                # Get best and worst posts
                posts_list = stats['posts']
                best_post = max(posts_list, key=lambda p: p.engagement_rate)
                worst_post = min(posts_list, key=lambda p: p.engagement_rate)
                
                hashtags_analysis.append({
                    'tag': tag,
                    'usage_count': usage,
                    'avg_likes': round(avg_likes, 0),
                    'avg_comments': round(avg_comments, 1),
                    'avg_reach': round(avg_reach, 0),
                    'avg_engagement_rate': round(avg_engagement, 2),
                    'effectiveness_score': round(effectiveness_score, 1),
                    'best_engagement': round(best_post.engagement_rate, 2),
                    'worst_engagement': round(worst_post.engagement_rate, 2),
                    'consistency': round((worst_post.engagement_rate / best_post.engagement_rate * 100) if best_post.engagement_rate > 0 else 0, 1)
                })
            
            # Sort by effectiveness score
            hashtags_analysis.sort(key=lambda x: x['effectiveness_score'], reverse=True)
            
            # Categorize hashtags
            high_performers = [h for h in hashtags_analysis if h['effectiveness_score'] >= 50]
            medium_performers = [h for h in hashtags_analysis if 30 <= h['effectiveness_score'] < 50]
            low_performers = [h for h in hashtags_analysis if h['effectiveness_score'] < 30]
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'total_unique_hashtags': len(hashtags_analysis),
                'all_hashtags': hashtags_analysis,
                'high_performers': high_performers,
                'medium_performers': medium_performers,
                'low_performers': low_performers,
                'recommendations': self._generate_effectiveness_recommendations(
                    high_performers, 
                    low_performers
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing hashtag effectiveness: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_trending_hashtags(
        self,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get trending hashtags from database.
        
        Args:
            limit: Maximum number of hashtags to return
            
        Returns:
            Dictionary with trending hashtags
        """
        try:
            logger.info("Getting trending hashtags")
            
            trending = self.repository.get_trending_hashtags(limit)
            
            if not trending:
                # Fall back to top performing
                trending = self.repository.get_top_hashtags(limit)
            
            hashtags_list = []
            for hashtag in trending:
                hashtags_list.append({
                    'tag': hashtag.tag,
                    'usage_count': hashtag.usage_count,
                    'avg_engagement_rate': round(hashtag.avg_engagement_rate, 2),
                    'avg_likes': round(hashtag.avg_likes, 0),
                    'avg_comments': round(hashtag.avg_comments, 1),
                    'avg_reach': round(hashtag.avg_reach, 0),
                    'is_trending': hashtag.is_trending,
                    'trend_score': round(hashtag.trend_score, 1),
                    'last_used': hashtag.last_used.isoformat() if hashtag.last_used else None
                })
            
            return {
                'status': 'success',
                'trending_hashtags': hashtags_list,
                'count': len(hashtags_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting trending hashtags: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def recommend_hashtags(
        self,
        context: Optional[str] = None,
        count: int = 10,
        exclude_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Recommend hashtags based on performance and context.
        
        Args:
            context: Context for recommendations (e.g., post caption or theme)
            count: Number of hashtags to recommend
            exclude_tags: Hashtags to exclude from recommendations
            
        Returns:
            Dictionary with hashtag recommendations
        """
        try:
            logger.info(f"Generating {count} hashtag recommendations")
            
            exclude_set = set(tag.lstrip('#').lower() for tag in (exclude_tags or []))
            
            # Get top performing hashtags
            top_hashtags = self.repository.get_top_hashtags(limit=50)
            
            if not top_hashtags:
                return {
                    'status': 'no_data',
                    'message': 'Недостатньо даних для рекомендацій'
                }
            
            # Filter and score hashtags
            recommendations = []
            
            for hashtag in top_hashtags:
                if hashtag.tag.lower() in exclude_set:
                    continue
                
                # Calculate recommendation score
                score = self._calculate_recommendation_score(hashtag)
                
                recommendations.append({
                    'tag': hashtag.tag,
                    'score': round(score, 1),
                    'avg_engagement_rate': round(hashtag.avg_engagement_rate, 2),
                    'usage_count': hashtag.usage_count,
                    'avg_likes': round(hashtag.avg_likes, 0),
                    'is_trending': hashtag.is_trending,
                    'reason': self._get_recommendation_reason(hashtag, score)
                })
            
            # Sort by score and limit
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            recommendations = recommendations[:count]
            
            # Group by category
            categorized = self._categorize_recommendations(recommendations)
            
            return {
                'status': 'success',
                'recommendations': recommendations,
                'categorized': categorized,
                'usage_tips': self._generate_usage_tips(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error recommending hashtags: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def analyze_hashtag_combinations(
        self,
        days: int = 30,
        end_date: Optional[datetime] = None,
        min_posts: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze which hashtag combinations work best together.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            min_posts: Minimum number of posts to consider a combination
            
        Returns:
            Dictionary with combination analysis
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info("Analyzing hashtag combinations")
            
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу'
                }
            
            # Find common pairs
            pair_stats = defaultdict(lambda: {
                'count': 0,
                'total_engagement': 0,
                'posts': []
            })
            
            for post in posts:
                if not post.hashtags or len(post.hashtags) < 2:
                    continue
                
                hashtags = [tag.lstrip('#').lower() for tag in post.hashtags]
                
                # Generate all pairs
                for i in range(len(hashtags)):
                    for j in range(i + 1, len(hashtags)):
                        pair = tuple(sorted([hashtags[i], hashtags[j]]))
                        pair_stats[pair]['count'] += 1
                        pair_stats[pair]['total_engagement'] += post.engagement_rate
                        pair_stats[pair]['posts'].append(post)
            
            # Calculate metrics for pairs
            combinations = []
            
            for pair, stats in pair_stats.items():
                if stats['count'] < min_posts:
                    continue
                
                avg_engagement = stats['total_engagement'] / stats['count']
                
                combinations.append({
                    'hashtags': list(pair),
                    'usage_count': stats['count'],
                    'avg_engagement_rate': round(avg_engagement, 2),
                    'display': f"#{pair[0]} + #{pair[1]}"
                })
            
            # Sort by engagement
            combinations.sort(key=lambda x: x['avg_engagement_rate'], reverse=True)
            
            # Get top combinations
            top_combinations = combinations[:10]
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'total_combinations': len(combinations),
                'top_combinations': top_combinations,
                'recommendations': self._generate_combination_recommendations(top_combinations)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing hashtag combinations: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_hashtag_usage_patterns(
        self,
        days: int = 90,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze hashtag usage patterns over time.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            
        Returns:
            Dictionary with usage pattern data
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info("Analyzing hashtag usage patterns")
            
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                return {
                    'status': 'no_data',
                    'message': 'Немає даних для аналізу'
                }
            
            # Calculate average hashtags per post
            posts_with_hashtags = [p for p in posts if p.hashtags]
            
            if not posts_with_hashtags:
                return {
                    'status': 'no_data',
                    'message': 'Немає постів з хештегами'
                }
            
            total_hashtags = sum(len(p.hashtags) for p in posts_with_hashtags)
            avg_hashtags_per_post = total_hashtags / len(posts_with_hashtags)
            
            # Find most frequently used hashtags
            all_hashtags = []
            for post in posts_with_hashtags:
                all_hashtags.extend([tag.lstrip('#').lower() for tag in post.hashtags])
            
            hashtag_frequency = Counter(all_hashtags)
            most_common = hashtag_frequency.most_common(20)
            
            # Analyze correlation between hashtag count and engagement
            engagement_by_count = defaultdict(list)
            
            for post in posts_with_hashtags:
                count_bucket = (len(post.hashtags) // 5) * 5  # Group by 5s
                engagement_by_count[count_bucket].append(post.engagement_rate)
            
            optimal_count_data = []
            for count, engagements in sorted(engagement_by_count.items()):
                avg_engagement = sum(engagements) / len(engagements)
                optimal_count_data.append({
                    'hashtag_count_range': f"{count}-{count+4}",
                    'posts_count': len(engagements),
                    'avg_engagement_rate': round(avg_engagement, 2)
                })
            
            # Find optimal count
            optimal = max(optimal_count_data, key=lambda x: x['avg_engagement_rate']) if optimal_count_data else None
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'statistics': {
                    'total_posts': len(posts),
                    'posts_with_hashtags': len(posts_with_hashtags),
                    'avg_hashtags_per_post': round(avg_hashtags_per_post, 1),
                    'unique_hashtags': len(hashtag_frequency)
                },
                'most_used': [
                    {'tag': tag, 'count': count} 
                    for tag, count in most_common
                ],
                'optimal_count': optimal,
                'engagement_by_count': optimal_count_data,
                'recommendations': self._generate_usage_pattern_recommendations(
                    avg_hashtags_per_post,
                    optimal
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing hashtag usage patterns: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _calculate_recommendation_score(self, hashtag: Hashtag) -> float:
        """Calculate recommendation score for a hashtag."""
        score = 0.0
        
        # Engagement rate (40%)
        score += hashtag.avg_engagement_rate * 4
        
        # Usage count (20%) - moderate usage is good
        usage_score = min(20, hashtag.usage_count * 2)
        score += usage_score
        
        # Trending bonus (20%)
        if hashtag.is_trending:
            score += 20
        
        # Reach (20%)
        reach_score = min(20, hashtag.avg_reach / 100)
        score += reach_score
        
        return min(100, score)
    
    def _get_recommendation_reason(self, hashtag: Hashtag, score: float) -> str:
        """Get reason for recommending a hashtag."""
        reasons = []
        
        if hashtag.avg_engagement_rate > 5:
            reasons.append('висока залученість')
        
        if hashtag.is_trending:
            reasons.append('в тренді')
        
        if hashtag.usage_count >= 5:
            reasons.append('перевірена ефективність')
        
        if hashtag.avg_reach > 1000:
            reasons.append('великий охоплення')
        
        if not reasons:
            reasons.append('гарна продуктивність')
        
        return ', '.join(reasons)
    
    def _categorize_recommendations(
        self, 
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize recommendations."""
        categorized = {
            'high_engagement': [],
            'trending': [],
            'consistent': []
        }
        
        for rec in recommendations:
            if rec['avg_engagement_rate'] > 5:
                categorized['high_engagement'].append(rec)
            
            if rec.get('is_trending'):
                categorized['trending'].append(rec)
            
            if rec['usage_count'] >= 5:
                categorized['consistent'].append(rec)
        
        return categorized
    
    def _generate_effectiveness_recommendations(
        self,
        high_performers: List[Dict[str, Any]],
        low_performers: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on effectiveness analysis."""
        recommendations = []
        
        if high_performers:
            top_tags = ', '.join([f"#{h['tag']}" for h in high_performers[:5]])
            recommendations.append(
                f"Використовуйте ці ефективні хештеги: {top_tags}"
            )
        
        if low_performers:
            bad_tags = ', '.join([f"#{h['tag']}" for h in low_performers[:3]])
            recommendations.append(
                f"Замініть неефективні хештеги: {bad_tags}"
            )
        
        if len(high_performers) < 5:
            recommendations.append(
                "Експериментуйте з новими хештегами для розширення охоплення"
            )
        
        return recommendations
    
    def _generate_usage_tips(
        self, 
        recommendations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate usage tips for hashtags."""
        tips = [
            "Використовуйте від 20 до 30 хештегів для максимального охоплення",
            "Комбінуйте популярні та нішеві хештеги",
            "Розміщуйте хештеги в першому коментарі для чистоти посту"
        ]
        
        if any(rec.get('is_trending') for rec in recommendations):
            tips.append("Швидко використовуйте трендові хештеги поки вони актуальні")
        
        return tips
    
    def _generate_combination_recommendations(
        self,
        top_combinations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for hashtag combinations."""
        recommendations = []
        
        if top_combinations:
            best = top_combinations[0]
            recommendations.append(
                f"Найкраща комбінація: {best['display']} "
                f"({best['avg_engagement_rate']}% залученості)"
            )
        
        if len(top_combinations) >= 3:
            recommendations.append(
                "Використовуйте перевірені комбінації з топ-списку"
            )
        
        return recommendations
    
    def _generate_usage_pattern_recommendations(
        self,
        avg_count: float,
        optimal: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on usage patterns."""
        recommendations = []
        
        if optimal:
            optimal_range = optimal['hashtag_count_range']
            recommendations.append(
                f"Оптимальна кількість хештегів: {optimal_range} "
                f"(залученість {optimal['avg_engagement_rate']}%)"
            )
        
        if avg_count < 15:
            recommendations.append(
                "Використовуйте більше хештегів - рекомендовано 20-30"
            )
        elif avg_count > 30:
            recommendations.append(
                "Зменшіть кількість хештегів - фокусуйтеся на якості"
            )
        
        return recommendations
    
    def close(self):
        """Close repository connection."""
        if self.repository:
            self.repository.close()
