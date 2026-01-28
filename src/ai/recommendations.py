"""Recommendation generator for AI analysis results."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.ai.analyzer import AIAnalyzer
from src.database.repository import Repository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecommendationGenerator:
    """Generate and store AI recommendations."""
    
    def __init__(self, analyzer: Optional[AIAnalyzer] = None):
        """
        Initialize recommendation generator.
        
        Args:
            analyzer: AIAnalyzer instance (creates new one if not provided)
        """
        self.analyzer = analyzer or AIAnalyzer()
        self.repository = Repository()
    
    def generate_for_post(
        self,
        post_id: str,
        force_regenerate: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Generate recommendations for a specific post.
        
        Args:
            post_id: Instagram post ID
            force_regenerate: Force new analysis even if exists
            
        Returns:
            Recommendation dictionary
        """
        logger.info(f"Generating recommendations for post: {post_id}")
        
        # Get post from database
        post = self.repository.get_post_by_id(post_id)
        if not post:
            logger.error(f"Post not found: {post_id}")
            return None
        
        # Check if recommendations already exist
        if not force_regenerate:
            existing = self.repository.get_recommendations_for_post(post.id)
            if existing:
                logger.info(f"Using existing recommendations for post {post_id}")
                return {
                    'post_id': post_id,
                    'recommendations': existing
                }
        
        # Analyze caption
        caption_analysis = self.analyzer.analyze_caption(
            caption=post.caption or "",
            likes=post.likes_count,
            comments=post.comments_count,
            engagement_rate=post.engagement_rate
        )
        
        if caption_analysis:
            # Save caption recommendation
            rec_data = {
                'post_id': post.id,
                'recommendation_type': 'caption',
                'original_text': post.caption,
                'analysis': caption_analysis['analysis'],
                'score': caption_analysis['score'],
                'suggestions': []
            }
            caption_rec = self.repository.create_recommendation(rec_data)
        
        # Analyze hashtags if present
        hashtag_rec = None
        if post.hashtags:
            hashtag_analysis = self.analyzer.analyze_hashtags(
                hashtags=post.hashtags,
                topic="Instagram"
            )
            
            if hashtag_analysis:
                rec_data = {
                    'post_id': post.id,
                    'recommendation_type': 'hashtags',
                    'original_text': " ".join(post.hashtags),
                    'improved_text': " ".join(hashtag_analysis.get('recommended_hashtags', [])),
                    'analysis': hashtag_analysis['analysis'],
                    'score': hashtag_analysis['score'],
                    'suggestions': hashtag_analysis.get('recommended_hashtags', [])
                }
                hashtag_rec = self.repository.create_recommendation(rec_data)
        
        logger.info(f"Recommendations generated for post {post_id}")
        
        return {
            'post_id': post_id,
            'caption_analysis': caption_analysis,
            'hashtag_analysis': hashtag_rec
        }
    
    def generate_batch_recommendations(
        self,
        days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Generate recommendations for recent posts.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Batch recommendations dictionary
        """
        logger.info(f"Generating batch recommendations for last {days} days")
        
        # Get recent posts
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        posts = self.repository.get_posts_by_date_range(start_date, end_date)
        
        if not posts:
            logger.warning("No posts found for batch analysis")
            return None
        
        # Calculate average engagement
        avg_engagement = sum(p.engagement_rate for p in posts) / len(posts)
        
        # Convert posts to dictionaries for analysis
        posts_data = [
            {
                'caption': p.caption,
                'likes_count': p.likes_count,
                'comments_count': p.comments_count,
                'engagement_rate': p.engagement_rate
            }
            for p in posts
        ]
        
        # Generate batch analysis
        batch_analysis = self.analyzer.analyze_batch(
            posts=posts_data,
            avg_engagement=avg_engagement
        )
        
        if batch_analysis:
            # Save as general recommendation
            rec_data = {
                'recommendation_type': 'general',
                'analysis': batch_analysis['analysis'],
                'score': batch_analysis['score'],
                'suggestions': [f"Analyzed {len(posts)} posts"]
            }
            self.repository.create_recommendation(rec_data)
            
            logger.info(f"Batch recommendations generated for {len(posts)} posts")
            
        return batch_analysis
    
    def generate_general_recommendations(
        self,
        period_days: int = 30
    ) -> Optional[str]:
        """
        Generate general account recommendations.
        
        Args:
            period_days: Period in days to analyze
            
        Returns:
            Recommendations text
        """
        logger.info(f"Generating general recommendations for {period_days} days")
        
        from datetime import timedelta
        from config.settings import settings
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Get statistics
        daily_stats = self.repository.get_daily_stats_range(start_date, end_date)
        
        if not daily_stats:
            logger.warning("No daily stats found for general recommendations")
            return None
        
        # Calculate aggregates
        total_posts = sum(s.posts_count for s in daily_stats)
        total_stories = sum(s.stories_count for s in daily_stats)
        total_reels = sum(s.reels_count for s in daily_stats)
        
        avg_engagement = 0.0
        if daily_stats:
            avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
        
        # Get follower change
        followers_change = 0
        if len(daily_stats) >= 2:
            followers_change = daily_stats[-1].followers_count - daily_stats[0].followers_count
        
        stats = {
            'posts_count': total_posts,
            'stories_count': total_stories,
            'reels_count': total_reels,
            'avg_engagement': round(avg_engagement, 2),
            'followers_change': followers_change
        }
        
        # Get targets
        targets = settings.load_targets().get('targets', {})
        
        # Generate recommendations
        recommendations = self.analyzer.generate_general_recommendations(
            stats=stats,
            targets=targets
        )
        
        if recommendations:
            # Save as general recommendation
            rec_data = {
                'recommendation_type': 'general',
                'analysis': recommendations,
                'score': 0.0,
                'suggestions': [f"Period: {period_days} days"]
            }
            self.repository.create_recommendation(rec_data)
            
            logger.info("General recommendations generated")
        
        return recommendations
    
    def get_latest_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get latest recommendations.
        
        Args:
            limit: Number of recommendations to retrieve
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = self.repository.get_recent_recommendations(limit=limit)
        
        return [
            {
                'id': rec.id,
                'type': rec.recommendation_type,
                'score': rec.score,
                'analysis': rec.analysis,
                'original_text': rec.original_text,
                'improved_text': rec.improved_text,
                'created_at': rec.created_at
            }
            for rec in recommendations
        ]
    
    def close(self):
        """Close repository connection."""
        self.repository.close()
