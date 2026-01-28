"""AI analyzer using OpenAI GPT for content analysis."""
import openai
from typing import Dict, Any, List, Optional
from config.settings import settings
from src.ai import prompts
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AIAnalyzer:
    """AI-powered content analyzer using OpenAI GPT."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize AI analyzer.
        
        Args:
            api_key: OpenAI API key (optional, uses settings if not provided)
            model: Model to use (optional, uses settings if not provided)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def _call_gpt(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """
        Make a call to GPT API.
        
        Args:
            prompt: Prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text or None if failed
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ти експерт з Instagram маркетингу та SMM. Надаєш професійні поради українською мовою."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            return None
    
    def analyze_caption(
        self,
        caption: str,
        likes: int = 0,
        comments: int = 0,
        engagement_rate: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a post caption.
        
        Args:
            caption: Post caption text
            likes: Number of likes
            comments: Number of comments
            engagement_rate: Engagement rate percentage
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing caption with AI...")
        
        prompt = prompts.CAPTION_ANALYSIS_PROMPT.format(
            caption=caption,
            likes=likes,
            comments=comments,
            engagement_rate=engagement_rate
        )
        
        response = self._call_gpt(prompt, max_tokens=1500)
        
        if response:
            # Parse response to extract score and sections
            try:
                score = self._extract_score(response)
                return {
                    'analysis': response,
                    'score': score,
                    'original_caption': caption,
                    'metrics': {
                        'likes': likes,
                        'comments': comments,
                        'engagement_rate': engagement_rate
                    }
                }
            except Exception as e:
                logger.error(f"Error parsing AI response: {e}")
                return {
                    'analysis': response,
                    'score': 5.0,
                    'original_caption': caption
                }
        
        return None
    
    def analyze_hashtags(
        self,
        hashtags: List[str],
        topic: str = "загальна тематика"
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze hashtags effectiveness.
        
        Args:
            hashtags: List of hashtags
            topic: Content topic/niche
            
        Returns:
            Dictionary with hashtag analysis
        """
        logger.info("Analyzing hashtags with AI...")
        
        hashtags_str = " ".join(hashtags) if hashtags else "немає хештегів"
        
        prompt = prompts.HASHTAGS_ANALYSIS_PROMPT.format(
            hashtags=hashtags_str,
            topic=topic
        )
        
        response = self._call_gpt(prompt, max_tokens=1000)
        
        if response:
            score = self._extract_score(response)
            return {
                'analysis': response,
                'score': score,
                'original_hashtags': hashtags,
                'recommended_hashtags': self._extract_hashtags(response)
            }
        
        return None
    
    def analyze_batch(
        self,
        posts: List[Dict[str, Any]],
        avg_engagement: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze multiple posts together for strategic insights.
        
        Args:
            posts: List of post dictionaries
            avg_engagement: Average engagement rate
            
        Returns:
            Dictionary with batch analysis
        """
        logger.info(f"Analyzing batch of {len(posts)} posts with AI...")
        
        # Create posts summary
        posts_summary = []
        for i, post in enumerate(posts[:10], 1):  # Limit to 10 for token management
            caption_preview = post.get('caption', '')[:100]
            posts_summary.append(
                f"{i}. Лайки: {post.get('likes_count', 0)}, "
                f"Коментарі: {post.get('comments_count', 0)}, "
                f"ER: {post.get('engagement_rate', 0)}%\n"
                f"   Текст: {caption_preview}..."
            )
        
        prompt = prompts.BATCH_ANALYSIS_PROMPT.format(
            posts_summary="\n".join(posts_summary),
            avg_engagement=avg_engagement,
            posts_count=len(posts)
        )
        
        response = self._call_gpt(prompt, max_tokens=1500)
        
        if response:
            score = self._extract_score(response)
            return {
                'analysis': response,
                'score': score,
                'posts_analyzed': len(posts),
                'avg_engagement': avg_engagement
            }
        
        return None
    
    def improve_caption(
        self,
        original_caption: str,
        min_length: int = 50,
        style: str = "дружній та залучаючий"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate improved version of caption.
        
        Args:
            original_caption: Original caption text
            min_length: Minimum caption length
            style: Desired writing style
            
        Returns:
            Dictionary with improved caption
        """
        logger.info("Generating improved caption with AI...")
        
        prompt = prompts.CAPTION_IMPROVEMENT_PROMPT.format(
            original_caption=original_caption,
            min_length=min_length,
            style=style
        )
        
        response = self._call_gpt(prompt, max_tokens=1000)
        
        if response:
            improved = self._extract_improved_caption(response)
            return {
                'original': original_caption,
                'improved': improved or response,
                'full_response': response
            }
        
        return None
    
    def analyze_tone(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze tone and style of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with tone analysis
        """
        logger.info("Analyzing tone with AI...")
        
        prompt = prompts.TONE_ANALYSIS_PROMPT.format(text=text)
        response = self._call_gpt(prompt, max_tokens=800)
        
        if response:
            return {
                'text': text,
                'analysis': response
            }
        
        return None
    
    def generate_general_recommendations(
        self,
        stats: Dict[str, Any],
        targets: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate general recommendations based on statistics and targets.
        
        Args:
            stats: Dictionary with statistics
            targets: Dictionary with targets
            
        Returns:
            Recommendations text
        """
        logger.info("Generating general recommendations with AI...")
        
        prompt = prompts.GENERAL_RECOMMENDATIONS_PROMPT.format(
            posts_count=stats.get('posts_count', 0),
            stories_count=stats.get('stories_count', 0),
            reels_count=stats.get('reels_count', 0),
            avg_engagement=stats.get('avg_engagement', 0.0),
            followers_change=stats.get('followers_change', 0),
            target_posts=targets.get('posts_per_month', 20),
            target_stories=targets.get('stories_per_day', 3),
            target_reels=targets.get('reels_per_week', 2),
            target_engagement=targets.get('min_engagement_rate', 3.5)
        )
        
        response = self._call_gpt(prompt, max_tokens=1500)
        return response
    
    def _extract_score(self, text: str) -> float:
        """Extract numerical score from AI response."""
        try:
            # Look for patterns like "ОЦІНКА: 7" or "7/10"
            import re
            patterns = [
                r'ОЦІНКА[:\s]+(\d+)',
                r'(\d+)/10',
                r'оцінка[:\s]+(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    score = float(match.group(1))
                    return min(max(score, 0), 10)  # Clamp between 0-10
            
            return 5.0  # Default score
            
        except Exception:
            return 5.0
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from AI response."""
        try:
            import re
            # Find all words starting with #
            hashtags = re.findall(r'#\w+', text)
            return hashtags[:15]  # Limit to 15
        except Exception:
            return []
    
    def _extract_improved_caption(self, text: str) -> Optional[str]:
        """Extract improved caption from AI response."""
        try:
            # Look for section after "ПОКРАЩЕНИЙ ВАРІАНТ:"
            import re
            pattern = r'ПОКРАЩЕНИЙ ВАРІАНТ:(.+?)(?:\n\n|\d\.|$)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return None
        except Exception:
            return None
