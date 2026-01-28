"""Competitor analysis for Instagram accounts."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.database.repository import Repository
from src.database.models import Competitor
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CompetitorAnalyzer:
    """Analyzer for competitor performance and benchmarking."""
    
    def __init__(self, repository: Optional[Repository] = None):
        """
        Initialize competitor analyzer.
        
        Args:
            repository: Repository instance (creates new one if not provided)
        """
        self.repository = repository or Repository()
    
    def compare_with_competitors(
        self, 
        days: int = 30,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Compare own performance with competitors.
        
        Args:
            days: Number of days to analyze
            end_date: End date for analysis
            
        Returns:
            Dictionary with comparison data
        """
        try:
            end_date = end_date or datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logger.info("Comparing with competitors")
            
            # Get own metrics
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            
            if not posts:
                own_metrics = {
                    'posts_count': 0,
                    'avg_engagement_rate': 0,
                    'avg_likes': 0,
                    'avg_comments': 0
                }
            else:
                own_metrics = {
                    'posts_count': len(posts),
                    'avg_engagement_rate': round(sum(p.engagement_rate for p in posts) / len(posts), 2),
                    'avg_likes': round(sum(p.likes_count for p in posts) / len(posts), 0),
                    'avg_comments': round(sum(p.comments_count for p in posts) / len(posts), 0)
                }
            
            # Get competitors data
            competitors = self.repository.get_all_competitors()
            
            if not competitors:
                return {
                    'status': 'no_competitors',
                    'message': 'Немає даних про конкурентів',
                    'own_metrics': own_metrics
                }
            
            # Format competitor data
            competitors_data = []
            for comp in competitors:
                competitors_data.append({
                    'username': comp.username,
                    'full_name': comp.full_name,
                    'followers_count': comp.followers_count,
                    'posts_count': comp.posts_count,
                    'avg_engagement_rate': round(comp.avg_engagement_rate, 2),
                    'avg_likes': round(comp.avg_likes, 0),
                    'avg_comments': round(comp.avg_comments, 0),
                    'posting_frequency': round(comp.posting_frequency, 1) if comp.posting_frequency else 0,
                    'last_analyzed': comp.last_analyzed.isoformat() if comp.last_analyzed else None
                })
            
            # Calculate averages across competitors
            if competitors_data:
                avg_competitor_engagement = sum(c['avg_engagement_rate'] for c in competitors_data) / len(competitors_data)
                avg_competitor_likes = sum(c['avg_likes'] for c in competitors_data) / len(competitors_data)
                avg_competitor_comments = sum(c['avg_comments'] for c in competitors_data) / len(competitors_data)
                avg_posting_frequency = sum(c['posting_frequency'] for c in competitors_data) / len(competitors_data)
            else:
                avg_competitor_engagement = 0
                avg_competitor_likes = 0
                avg_competitor_comments = 0
                avg_posting_frequency = 0
            
            competitor_averages = {
                'avg_engagement_rate': round(avg_competitor_engagement, 2),
                'avg_likes': round(avg_competitor_likes, 0),
                'avg_comments': round(avg_competitor_comments, 0),
                'avg_posting_frequency': round(avg_posting_frequency, 1)
            }
            
            # Calculate gaps
            gaps = self._calculate_gaps(own_metrics, competitor_averages)
            
            # Generate insights
            insights = self._generate_comparison_insights(own_metrics, competitor_averages, gaps)
            
            return {
                'status': 'success',
                'period': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'own_metrics': own_metrics,
                'competitors': competitors_data,
                'competitor_averages': competitor_averages,
                'gaps': gaps,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error comparing with competitors: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def find_competitor_gaps(self) -> Dict[str, Any]:
        """
        Find gaps and opportunities compared to competitors.
        
        Returns:
            Dictionary with gap analysis
        """
        try:
            logger.info("Finding competitor gaps")
            
            comparison = self.compare_with_competitors(days=30)
            
            if comparison['status'] != 'success':
                return comparison
            
            own = comparison['own_metrics']
            competitors_avg = comparison['competitor_averages']
            
            opportunities = []
            strengths = []
            
            # Analyze engagement rate
            if own['avg_engagement_rate'] < competitors_avg['avg_engagement_rate']:
                gap = competitors_avg['avg_engagement_rate'] - own['avg_engagement_rate']
                opportunities.append({
                    'metric': 'Рівень залученості',
                    'gap': round(gap, 2),
                    'type': 'percentage',
                    'recommendation': f"Підвищіть залученість на {gap:.1f}% до рівня конкурентів"
                })
            else:
                strengths.append({
                    'metric': 'Рівень залученості',
                    'advantage': round(own['avg_engagement_rate'] - competitors_avg['avg_engagement_rate'], 2),
                    'message': 'Ваша залученість вища за конкурентів!'
                })
            
            # Analyze likes
            if own['avg_likes'] < competitors_avg['avg_likes']:
                gap = competitors_avg['avg_likes'] - own['avg_likes']
                opportunities.append({
                    'metric': 'Середня кількість лайків',
                    'gap': int(gap),
                    'type': 'count',
                    'recommendation': f"Збільшіть лайки на {int(gap)} до рівня конкурентів"
                })
            else:
                strengths.append({
                    'metric': 'Лайки',
                    'advantage': int(own['avg_likes'] - competitors_avg['avg_likes']),
                    'message': 'Ви отримуєте більше лайків!'
                })
            
            # Analyze comments
            if own['avg_comments'] < competitors_avg['avg_comments']:
                gap = competitors_avg['avg_comments'] - own['avg_comments']
                opportunities.append({
                    'metric': 'Середня кількість коментарів',
                    'gap': int(gap),
                    'type': 'count',
                    'recommendation': f"Збільшіть коментарі на {int(gap)} до рівня конкурентів"
                })
            else:
                strengths.append({
                    'metric': 'Коментарі',
                    'advantage': int(own['avg_comments'] - competitors_avg['avg_comments']),
                    'message': 'Ви отримуєте більше коментарів!'
                })
            
            return {
                'status': 'success',
                'opportunities': opportunities,
                'strengths': strengths,
                'priority_actions': self._prioritize_actions(opportunities)
            }
            
        except Exception as e:
            logger.error(f"Error finding competitor gaps: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def benchmark_performance(self) -> Dict[str, Any]:
        """
        Benchmark performance against competitors with detailed metrics.
        
        Returns:
            Dictionary with benchmark data
        """
        try:
            logger.info("Benchmarking performance")
            
            comparison = self.compare_with_competitors(days=30)
            
            if comparison['status'] != 'success':
                return comparison
            
            own = comparison['own_metrics']
            competitors = comparison['competitors']
            
            if not competitors:
                return {
                    'status': 'no_competitors',
                    'message': 'Немає даних для бенчмаркінгу'
                }
            
            # Calculate rankings
            all_accounts = competitors + [{'username': 'Ви', **own}]
            
            # Rank by engagement rate
            by_engagement = sorted(all_accounts, key=lambda x: x['avg_engagement_rate'], reverse=True)
            engagement_rank = next(i + 1 for i, acc in enumerate(by_engagement) if acc['username'] == 'Ви')
            
            # Rank by likes
            by_likes = sorted(all_accounts, key=lambda x: x['avg_likes'], reverse=True)
            likes_rank = next(i + 1 for i, acc in enumerate(by_likes) if acc['username'] == 'Ви')
            
            # Rank by comments
            by_comments = sorted(all_accounts, key=lambda x: x['avg_comments'], reverse=True)
            comments_rank = next(i + 1 for i, acc in enumerate(by_comments) if acc['username'] == 'Ви')
            
            total_accounts = len(all_accounts)
            
            # Calculate percentile
            engagement_percentile = round((total_accounts - engagement_rank + 1) / total_accounts * 100, 0)
            
            # Determine performance level
            if engagement_percentile >= 75:
                performance_level = 'Відмінно'
            elif engagement_percentile >= 50:
                performance_level = 'Добре'
            elif engagement_percentile >= 25:
                performance_level = 'Задовільно'
            else:
                performance_level = 'Потребує покращення'
            
            return {
                'status': 'success',
                'rankings': {
                    'engagement': {
                        'rank': engagement_rank,
                        'total': total_accounts,
                        'percentile': engagement_percentile
                    },
                    'likes': {
                        'rank': likes_rank,
                        'total': total_accounts
                    },
                    'comments': {
                        'rank': comments_rank,
                        'total': total_accounts
                    }
                },
                'performance_level': performance_level,
                'top_performers': {
                    'by_engagement': by_engagement[:3],
                    'by_likes': by_likes[:3],
                    'by_comments': by_comments[:3]
                },
                'recommendations': self._generate_benchmark_recommendations(
                    engagement_rank, 
                    total_accounts,
                    performance_level
                )
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking performance: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def analyze_competitor_content_strategy(
        self, 
        competitor_username: str
    ) -> Dict[str, Any]:
        """
        Analyze specific competitor's content strategy.
        
        Args:
            competitor_username: Competitor username to analyze
            
        Returns:
            Dictionary with competitor strategy analysis
        """
        try:
            logger.info(f"Analyzing competitor strategy: @{competitor_username}")
            
            competitor = self.repository.get_competitor(competitor_username)
            
            if not competitor:
                return {
                    'status': 'not_found',
                    'message': f'Конкурент @{competitor_username} не знайдений'
                }
            
            analysis = {
                'username': competitor.username,
                'full_name': competitor.full_name,
                'followers_count': competitor.followers_count,
                'posts_count': competitor.posts_count,
                'metrics': {
                    'avg_engagement_rate': round(competitor.avg_engagement_rate, 2),
                    'avg_likes': round(competitor.avg_likes, 0),
                    'avg_comments': round(competitor.avg_comments, 0),
                    'posting_frequency': round(competitor.posting_frequency, 1) if competitor.posting_frequency else 0
                },
                'best_posting_times': competitor.best_posting_times or [],
                'popular_hashtags': competitor.popular_hashtags or [],
                'top_post': {
                    'post_id': competitor.top_post_id,
                    'engagement': round(competitor.top_post_engagement, 2)
                } if competitor.top_post_id else None,
                'last_analyzed': competitor.last_analyzed.isoformat() if competitor.last_analyzed else None
            }
            
            # Generate strategy insights
            insights = []
            
            if competitor.avg_engagement_rate > 5:
                insights.append({
                    'type': 'high_engagement',
                    'message': f'@{competitor_username} має дуже високу залученість ({competitor.avg_engagement_rate:.1f}%)'
                })
            
            if competitor.posting_frequency and competitor.posting_frequency > 1:
                insights.append({
                    'type': 'high_frequency',
                    'message': f'Публікує {competitor.posting_frequency:.1f} постів на день - активна стратегія'
                })
            elif competitor.posting_frequency and competitor.posting_frequency < 0.5:
                insights.append({
                    'type': 'low_frequency',
                    'message': f'Публікує рідко ({competitor.posting_frequency:.1f} постів/день) - фокус на якість'
                })
            
            if competitor.popular_hashtags:
                top_hashtags = competitor.popular_hashtags[:5]
                insights.append({
                    'type': 'hashtags',
                    'message': f'Найпопулярніші хештеги: {", ".join(f"#{tag}" for tag in top_hashtags)}'
                })
            
            analysis['insights'] = insights
            
            return {
                'status': 'success',
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing competitor content strategy: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_all_competitors_overview(self) -> Dict[str, Any]:
        """
        Get overview of all tracked competitors.
        
        Returns:
            Dictionary with all competitors overview
        """
        try:
            logger.info("Getting all competitors overview")
            
            competitors = self.repository.get_all_competitors()
            
            if not competitors:
                return {
                    'status': 'no_competitors',
                    'message': 'Немає доданих конкурентів для відстеження'
                }
            
            competitors_list = []
            for comp in competitors:
                competitors_list.append({
                    'username': comp.username,
                    'full_name': comp.full_name,
                    'followers_count': comp.followers_count,
                    'posts_count': comp.posts_count,
                    'avg_engagement_rate': round(comp.avg_engagement_rate, 2),
                    'avg_likes': round(comp.avg_likes, 0),
                    'avg_comments': round(comp.avg_comments, 0),
                    'posting_frequency': round(comp.posting_frequency, 1) if comp.posting_frequency else 0,
                    'last_analyzed': comp.last_analyzed.isoformat() if comp.last_analyzed else None
                })
            
            # Sort by engagement rate
            competitors_list.sort(key=lambda x: x['avg_engagement_rate'], reverse=True)
            
            # Calculate market statistics
            avg_engagement = sum(c['avg_engagement_rate'] for c in competitors_list) / len(competitors_list)
            avg_followers = sum(c['followers_count'] for c in competitors_list) / len(competitors_list)
            
            return {
                'status': 'success',
                'total_competitors': len(competitors_list),
                'competitors': competitors_list,
                'market_stats': {
                    'avg_engagement_rate': round(avg_engagement, 2),
                    'avg_followers': int(avg_followers),
                    'top_engagement': competitors_list[0]['avg_engagement_rate'] if competitors_list else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting competitors overview: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _calculate_gaps(
        self, 
        own_metrics: Dict[str, float], 
        competitor_averages: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate performance gaps."""
        gaps = {}
        
        for metric in ['avg_engagement_rate', 'avg_likes', 'avg_comments']:
            own_value = own_metrics.get(metric, 0)
            comp_value = competitor_averages.get(metric, 0)
            
            if comp_value > 0:
                gap_value = comp_value - own_value
                gap_percent = (gap_value / comp_value) * 100
                
                gaps[metric] = {
                    'absolute': round(gap_value, 2),
                    'percent': round(gap_percent, 1),
                    'status': 'behind' if gap_value > 0 else 'ahead'
                }
            else:
                gaps[metric] = {
                    'absolute': 0,
                    'percent': 0,
                    'status': 'no_data'
                }
        
        return gaps
    
    def _generate_comparison_insights(
        self,
        own_metrics: Dict[str, float],
        competitor_averages: Dict[str, float],
        gaps: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate insights from comparison."""
        insights = []
        
        # Engagement insight
        eng_gap = gaps.get('avg_engagement_rate', {})
        if eng_gap.get('status') == 'behind':
            insights.append({
                'type': 'warning',
                'message': f"Ваша залученість на {eng_gap['percent']:.1f}% нижча за конкурентів"
            })
        elif eng_gap.get('status') == 'ahead':
            insights.append({
                'type': 'positive',
                'message': f"Ваша залученість на {abs(eng_gap['percent']):.1f}% вища за конкурентів!"
            })
        
        # Likes insight
        likes_gap = gaps.get('avg_likes', {})
        if likes_gap.get('status') == 'behind' and likes_gap.get('percent', 0) > 20:
            insights.append({
                'type': 'info',
                'message': f"Працюйте над збільшенням лайків - відстаєте на {likes_gap['absolute']:.0f} в середньому"
            })
        
        # Comments insight
        comments_gap = gaps.get('avg_comments', {})
        if comments_gap.get('status') == 'behind' and comments_gap.get('percent', 0) > 20:
            insights.append({
                'type': 'info',
                'message': f"Стимулюйте більше коментарів - відстаєте на {comments_gap['absolute']:.0f} в середньому"
            })
        
        return insights
    
    def _prioritize_actions(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """Prioritize actions based on opportunities."""
        if not opportunities:
            return ['Продовжуйте працювати над поточною стратегією']
        
        # Sort by gap size
        sorted_opps = sorted(opportunities, key=lambda x: x.get('gap', 0), reverse=True)
        
        actions = []
        for opp in sorted_opps[:3]:  # Top 3 priorities
            actions.append(opp['recommendation'])
        
        return actions
    
    def _generate_benchmark_recommendations(
        self,
        rank: int,
        total: int,
        performance_level: str
    ) -> List[str]:
        """Generate recommendations based on benchmark."""
        recommendations = []
        
        if performance_level == 'Відмінно':
            recommendations.append('Чудова робота! Підтримуйте високий рівень якості контенту')
            recommendations.append('Поділіться своїми успішними практиками з командою')
        elif performance_level == 'Добре':
            recommendations.append('Хороші результати, але є простір для покращення')
            recommendations.append('Проаналізуйте стратегії лідерів у вашій ніші')
        elif performance_level == 'Задовільно':
            recommendations.append('Потрібно активно працювати над покращенням залученості')
            recommendations.append('Вивчіть успішні приклади конкурентів')
            recommendations.append('Експериментуйте з різними типами контенту')
        else:
            recommendations.append('Необхідна серйозна робота над контент-стратегією')
            recommendations.append('Дослідіть, що працює у ваших конкурентів')
            recommendations.append('Отримайте професійну консультацію з SMM')
        
        return recommendations
    
    def close(self):
        """Close repository connection."""
        if self.repository:
            self.repository.close()
