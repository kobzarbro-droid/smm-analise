# Analytics Integration Guide

This guide shows how to integrate the analytics modules into the existing Instagram SMM monitoring system.

## Quick Integration Examples

### 1. Integration with Telegram Bot Reports

```python
# In src/telegram/reports.py

from src.analytics import PerformanceAnalyzer, CompetitorAnalyzer, HashtagAnalyzer

def generate_analytics_report(days=7):
    """Generate analytics report for Telegram."""
    
    # Initialize analyzers
    perf = PerformanceAnalyzer()
    comp = CompetitorAnalyzer()
    hashtags = HashtagAnalyzer()
    
    try:
        report = "📊 *Аналітичний звіт*\n\n"
        
        # Performance section
        trends = perf.analyze_engagement_trends(days=days)
        if trends['status'] == 'success':
            summary = trends['summary']
            report += f"📈 *Показники залученості ({days} днів)*\n"
            report += f"• Постів: {summary['total_posts']}\n"
            report += f"• Середня залученість: {summary['avg_engagement_rate']}%\n"
            report += f"• Тренд: {trends['trend']['direction']}\n\n"
        
        # Best posting times
        timing = perf.find_best_posting_times(days=days*3)
        if timing['status'] == 'success' and timing['best_hours']:
            report += "⏰ *Кращий час для публікацій*\n"
            for hour_data in timing['best_hours'][:3]:
                report += f"• {hour_data['hour']:02d}:00 - {hour_data['avg_engagement_rate']}%\n"
            report += "\n"
        
        # Competitor comparison
        comparison = comp.compare_with_competitors(days=days)
        if comparison['status'] == 'success':
            report += "🏆 *Порівняння з конкурентами*\n"
            own = comparison['own_metrics']
            comp_avg = comparison['competitor_averages']
            report += f"• Ваша залученість: {own['avg_engagement_rate']}%\n"
            report += f"• Середня у конкурентів: {comp_avg['avg_engagement_rate']}%\n\n"
        
        # Hashtag recommendations
        hashtag_recs = hashtags.recommend_hashtags(count=5)
        if hashtag_recs['status'] == 'success':
            report += "#️⃣ *Рекомендовані хештеги*\n"
            for rec in hashtag_recs['recommendations']:
                report += f"• #{rec['tag']}\n"
        
        return report
        
    finally:
        perf.close()
        comp.close()
        hashtags.close()
```

### 2. Integration with Dashboard

```python
# In src/dashboard/routes.py (or app.py)

from flask import Flask, jsonify
from src.analytics import PerformanceAnalyzer, CompetitorAnalyzer, HashtagAnalyzer

app = Flask(__name__)

@app.route('/api/analytics/performance')
def get_performance_analytics():
    """Get performance analytics for dashboard."""
    days = request.args.get('days', 30, type=int)
    
    analyzer = PerformanceAnalyzer()
    try:
        insights = analyzer.get_performance_insights(days=days)
        return jsonify(insights)
    finally:
        analyzer.close()

@app.route('/api/analytics/competitors')
def get_competitor_analytics():
    """Get competitor comparison data."""
    analyzer = CompetitorAnalyzer()
    try:
        comparison = analyzer.compare_with_competitors(days=30)
        benchmark = analyzer.benchmark_performance()
        
        return jsonify({
            'comparison': comparison,
            'benchmark': benchmark
        })
    finally:
        analyzer.close()

@app.route('/api/analytics/hashtags')
def get_hashtag_analytics():
    """Get hashtag recommendations and analysis."""
    analyzer = HashtagAnalyzer()
    try:
        effectiveness = analyzer.analyze_hashtag_effectiveness(days=30)
        recommendations = analyzer.recommend_hashtags(count=15)
        patterns = analyzer.get_hashtag_usage_patterns(days=90)
        
        return jsonify({
            'effectiveness': effectiveness,
            'recommendations': recommendations,
            'patterns': patterns
        })
    finally:
        analyzer.close()

@app.route('/api/analytics/insights')
def get_comprehensive_insights():
    """Get comprehensive insights combining all analytics."""
    perf = PerformanceAnalyzer()
    comp = CompetitorAnalyzer()
    hashtags = HashtagAnalyzer()
    
    try:
        return jsonify({
            'performance': perf.get_performance_insights(days=30),
            'competitors': comp.compare_with_competitors(days=30),
            'gaps': comp.find_competitor_gaps(),
            'hashtags': hashtags.analyze_hashtag_effectiveness(days=30),
            'recommendations': hashtags.recommend_hashtags(count=10)
        })
    finally:
        perf.close()
        comp.close()
        hashtags.close()
```

### 3. Integration with AI Recommendations

```python
# In src/ai/recommendations.py

from src.analytics import PerformanceAnalyzer, HashtagAnalyzer

def generate_ai_recommendations():
    """Generate AI recommendations based on analytics."""
    
    perf = PerformanceAnalyzer()
    hashtags = HashtagAnalyzer()
    
    try:
        # Get performance data
        insights = perf.get_performance_insights(days=30)
        timing = perf.find_best_posting_times(days=90)
        content = perf.analyze_content_type_performance(days=30)
        
        # Get hashtag data
        hashtag_recs = hashtags.recommend_hashtags(count=20)
        patterns = hashtags.get_hashtag_usage_patterns(days=90)
        
        # Build context for AI
        context = f"""
        Performance Summary:
        - Average engagement: {insights['trends']['summary']['avg_engagement_rate']}%
        - Trend: {insights['trends']['trend']['direction']}
        
        Best Content Type: {content.get('best_performing_type', {}).get('type_name', 'N/A')}
        
        Best Posting Times: {', '.join([f"{h['hour']:02d}:00" for h in timing.get('best_hours', [])[:3]])}
        
        Recommended Hashtags: {', '.join([f"#{r['tag']}" for r in hashtag_recs.get('recommendations', [])[:10]])}
        """
        
        # Use AI analyzer with context
        # ... (existing AI code)
        
        return context
        
    finally:
        perf.close()
        hashtags.close()
```

### 4. Integration with Scheduler

```python
# In src/scheduler/tasks.py

from src.analytics import PerformanceAnalyzer, CompetitorAnalyzer, HashtagAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)

def scheduled_analytics_report():
    """Scheduled task to generate and send analytics reports."""
    logger.info("Running scheduled analytics report")
    
    perf = PerformanceAnalyzer()
    comp = CompetitorAnalyzer()
    hashtags = HashtagAnalyzer()
    
    try:
        # Generate comprehensive report
        report_data = {
            'performance': perf.get_performance_insights(days=7),
            'competitors': comp.compare_with_competitors(days=7),
            'hashtags': hashtags.analyze_hashtag_effectiveness(days=7)
        }
        
        # Send via Telegram
        from src.telegram.bot import send_analytics_report
        send_analytics_report(report_data)
        
        logger.info("Analytics report sent successfully")
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
    finally:
        perf.close()
        comp.close()
        hashtags.close()

def update_hashtag_trends():
    """Scheduled task to update hashtag trends."""
    logger.info("Updating hashtag trends")
    
    analyzer = HashtagAnalyzer()
    try:
        # This would update the database with current trends
        effectiveness = analyzer.analyze_hashtag_effectiveness(days=30)
        # Store results in database for quick access
        
        logger.info(f"Updated trends for {effectiveness.get('total_unique_hashtags', 0)} hashtags")
    finally:
        analyzer.close()
```

### 5. Standalone Usage for Manual Analysis

```python
# scripts/run_analytics.py

from datetime import datetime
from src.analytics import PerformanceAnalyzer, CompetitorAnalyzer, HashtagAnalyzer

def main():
    """Run comprehensive analytics analysis."""
    print(f"Running analytics for {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Performance analysis
    print("=" * 60)
    print("PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    perf = PerformanceAnalyzer()
    
    insights = perf.get_performance_insights(days=30)
    if insights['status'] == 'success':
        for insight in insights.get('insights', []):
            print(f"[{insight['type'].upper()}] {insight['title']}")
            print(f"  {insight['message']}\n")
    
    perf.close()
    
    # Competitor analysis
    print("=" * 60)
    print("COMPETITOR ANALYSIS")
    print("=" * 60)
    
    comp = CompetitorAnalyzer()
    
    gaps = comp.find_competitor_gaps()
    if gaps['status'] == 'success':
        print("Opportunities:")
        for opp in gaps.get('opportunities', []):
            print(f"  • {opp['recommendation']}")
        
        print("\nStrengths:")
        for strength in gaps.get('strengths', []):
            print(f"  • {strength['message']}")
    
    comp.close()
    
    # Hashtag analysis
    print("\n" + "=" * 60)
    print("HASHTAG ANALYSIS")
    print("=" * 60)
    
    hashtags = HashtagAnalyzer()
    
    recommendations = hashtags.recommend_hashtags(count=10)
    if recommendations['status'] == 'success':
        print("Top Recommended Hashtags:")
        for rec in recommendations['recommendations']:
            print(f"  #{rec['tag']} - Score: {rec['score']}")
            print(f"    Reason: {rec['reason']}")
    
    hashtags.close()

if __name__ == '__main__':
    main()
```

## Best Practices

### 1. Always Close Connections

```python
analyzer = PerformanceAnalyzer()
try:
    result = analyzer.analyze_engagement_trends(days=30)
    # Process result
finally:
    analyzer.close()  # Always close!
```

### 2. Handle Different Status Codes

```python
result = analyzer.analyze_engagement_trends(days=30)

if result['status'] == 'success':
    # Process successful result
    data = result['summary']
elif result['status'] == 'no_data':
    # Handle empty data case
    print("No data available for this period")
elif result['status'] == 'error':
    # Handle error
    logger.error(f"Analytics error: {result.get('message')}")
```

### 3. Use Context Managers (Future Enhancement)

```python
# Future enhancement - add context manager support
with PerformanceAnalyzer() as analyzer:
    result = analyzer.analyze_engagement_trends(days=30)
    # Automatically closes connection
```

### 4. Caching for Performance

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=10)
def get_cached_analytics(date_key, days):
    """Cache analytics results for performance."""
    analyzer = PerformanceAnalyzer()
    try:
        return analyzer.get_performance_insights(days=days)
    finally:
        analyzer.close()

# Usage
today = datetime.now().date().isoformat()
result = get_cached_analytics(today, 30)
```

### 5. Batch Processing

```python
def process_multiple_analyses(days_list):
    """Process multiple analyses efficiently."""
    analyzer = PerformanceAnalyzer()
    
    try:
        results = {}
        for days in days_list:
            results[days] = analyzer.analyze_engagement_trends(days=days)
        return results
    finally:
        analyzer.close()

# Usage
results = process_multiple_analyses([7, 14, 30, 90])
```

## Error Handling

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

def safe_analytics_call():
    """Safely call analytics with comprehensive error handling."""
    analyzer = PerformanceAnalyzer()
    
    try:
        result = analyzer.analyze_engagement_trends(days=30)
        
        if result['status'] == 'error':
            logger.error(f"Analytics error: {result.get('message')}")
            return None
        
        return result
        
    except Exception as e:
        logger.exception(f"Unexpected error in analytics: {e}")
        return None
    finally:
        try:
            analyzer.close()
        except Exception as e:
            logger.error(f"Error closing analyzer: {e}")
```

## Testing

```python
# tests/test_analytics.py

import pytest
from src.analytics import PerformanceAnalyzer

def test_performance_analyzer_initialization():
    """Test analyzer can be initialized."""
    analyzer = PerformanceAnalyzer()
    assert analyzer is not None
    analyzer.close()

def test_engagement_trends_with_no_data():
    """Test behavior with no data."""
    analyzer = PerformanceAnalyzer()
    try:
        result = analyzer.analyze_engagement_trends(days=30)
        assert 'status' in result
        assert result['status'] in ['success', 'no_data', 'error']
    finally:
        analyzer.close()

@pytest.fixture
def analyzer():
    """Fixture for performance analyzer."""
    analyzer = PerformanceAnalyzer()
    yield analyzer
    analyzer.close()

def test_all_methods_exist(analyzer):
    """Test all expected methods exist."""
    methods = [
        'analyze_engagement_trends',
        'find_best_posting_times',
        'analyze_content_type_performance',
        'get_top_performing_posts',
        'get_performance_insights'
    ]
    
    for method in methods:
        assert hasattr(analyzer, method)
        assert callable(getattr(analyzer, method))
```

## Performance Considerations

1. **Database Queries**: Analytics modules use the Repository pattern which queries the database. For large datasets, consider:
   - Indexing important columns (already done in models)
   - Limiting date ranges
   - Caching results

2. **Memory Usage**: When analyzing large time periods:
   - Process in batches
   - Use generators for large datasets
   - Clear variables when done

3. **API Rate Limits**: Not applicable to analytics (uses local database)

## Troubleshooting

### Common Issues

1. **"no_data" Status**
   - Ensure data collection is running
   - Check date ranges
   - Verify database has posts

2. **"no_competitors" Status**
   - Add competitors using the data collector
   - Check competitor data is recent

3. **Performance Issues**
   - Reduce time range (days parameter)
   - Add database indexes
   - Use caching

## Next Steps

1. Add analytics to dashboard visualization
2. Integrate with Telegram daily/weekly reports
3. Connect with AI recommendation system
4. Add scheduled analytics tasks
5. Create unit and integration tests
6. Add performance monitoring

## Support

For issues or questions about the analytics modules:
1. Check the README.md in src/analytics/
2. Review example_usage.py for working examples
3. Enable DEBUG logging for detailed information
4. Check logs in logs/ directory
