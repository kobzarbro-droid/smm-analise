# Analytics Module

This module provides comprehensive analytics for Instagram SMM monitoring, including performance metrics, competitor analysis, and hashtag insights.

## Features

### 1. Performance Analytics (`performance.py`)
- **Engagement Trends**: Track engagement rate, likes, and comments over time
- **Best Posting Times**: Identify optimal times and days for posting
- **Content Type Performance**: Analyze which content types (photo, video, carousel) perform best
- **Top Posts**: Find your best performing content
- **Comprehensive Insights**: Get actionable recommendations

### 2. Competitor Analysis (`competitors.py`)
- **Competitor Comparison**: Compare your metrics with competitors
- **Gap Analysis**: Identify areas for improvement
- **Benchmarking**: See how you rank against competitors
- **Strategy Analysis**: Analyze individual competitor strategies
- **Market Overview**: Get aggregate statistics across all competitors

### 3. Hashtag Analytics (`hashtags.py`)
- **Effectiveness Analysis**: Measure which hashtags drive engagement
- **Trending Hashtags**: Track trending hashtags
- **Smart Recommendations**: Get hashtag recommendations based on performance
- **Combination Analysis**: Find which hashtag combinations work best
- **Usage Patterns**: Understand optimal hashtag usage strategies

## Installation

The analytics modules are already integrated with the SMM monitoring system. No additional installation required.

## Usage

### Basic Usage

```python
from src.analytics import PerformanceAnalyzer, CompetitorAnalyzer, HashtagAnalyzer

# Initialize analyzers
performance = PerformanceAnalyzer()
competitors = CompetitorAnalyzer()
hashtags = HashtagAnalyzer()

# Analyze engagement trends
trends = performance.analyze_engagement_trends(days=30)
if trends['status'] == 'success':
    print(f"Average engagement: {trends['summary']['avg_engagement_rate']}%")
    print(f"Trend: {trends['trend']['direction']}")

# Compare with competitors
comparison = competitors.compare_with_competitors(days=30)
if comparison['status'] == 'success':
    print(f"Your engagement: {comparison['own_metrics']['avg_engagement_rate']}%")
    print(f"Competitor avg: {comparison['competitor_averages']['avg_engagement_rate']}%")

# Get hashtag recommendations
recommendations = hashtags.recommend_hashtags(count=10)
if recommendations['status'] == 'success':
    for rec in recommendations['recommendations']:
        print(f"#{rec['tag']}: {rec['reason']}")

# Always close connections when done
performance.close()
competitors.close()
hashtags.close()
```

### Advanced Usage

```python
# Get comprehensive performance insights
insights = performance.get_performance_insights(days=30)
for insight in insights['insights']:
    print(f"[{insight['type']}] {insight['title']}: {insight['message']}")

# Find competitive gaps
gaps = competitors.find_competitor_gaps()
if gaps.get('opportunities'):
    for opp in gaps['opportunities']:
        print(f"Opportunity: {opp['recommendation']}")

# Analyze hashtag combinations
combinations = hashtags.analyze_hashtag_combinations(days=30)
for combo in combinations['top_combinations'][:5]:
    print(f"{combo['display']}: {combo['avg_engagement_rate']}%")
```

## API Reference

### PerformanceAnalyzer

#### `analyze_engagement_trends(days=30, end_date=None)`
Analyze engagement trends over time.

**Parameters:**
- `days` (int): Number of days to analyze
- `end_date` (datetime): End date for analysis (defaults to today)

**Returns:**
- Dictionary with timeline data, summary statistics, and trend information

#### `find_best_posting_times(days=90, end_date=None)`
Find optimal posting times based on historical performance.

**Returns:**
- Dictionary with best hours and days for posting

#### `analyze_content_type_performance(days=30, end_date=None)`
Analyze performance by content type (photo, video, carousel).

**Returns:**
- Dictionary with performance data for each content type

#### `get_top_performing_posts(limit=10, days=30, end_date=None, metric='engagement_rate')`
Get top performing posts.

**Parameters:**
- `limit` (int): Number of posts to return
- `metric` (str): Metric to sort by ('engagement_rate', 'likes_count', 'comments_count')

**Returns:**
- Dictionary with top posts data

#### `get_performance_insights(days=30, end_date=None)`
Generate comprehensive performance insights.

**Returns:**
- Dictionary with insights, trends, timing, and recommendations

### CompetitorAnalyzer

#### `compare_with_competitors(days=30, end_date=None)`
Compare your performance with competitors.

**Returns:**
- Dictionary with comparison data and gaps analysis

#### `find_competitor_gaps()`
Find performance gaps and opportunities.

**Returns:**
- Dictionary with opportunities and strengths

#### `benchmark_performance()`
Benchmark performance against competitors.

**Returns:**
- Dictionary with rankings and percentiles

#### `analyze_competitor_content_strategy(competitor_username)`
Analyze specific competitor's strategy.

**Parameters:**
- `competitor_username` (str): Competitor username

**Returns:**
- Dictionary with competitor strategy analysis

#### `get_all_competitors_overview()`
Get overview of all tracked competitors.

**Returns:**
- Dictionary with all competitors data

### HashtagAnalyzer

#### `analyze_hashtag_effectiveness(days=30, end_date=None, min_usage=2)`
Analyze hashtag effectiveness.

**Parameters:**
- `min_usage` (int): Minimum usage count to include hashtag

**Returns:**
- Dictionary with effectiveness scores and categories

#### `get_trending_hashtags(limit=20)`
Get trending hashtags.

**Returns:**
- Dictionary with trending hashtags list

#### `recommend_hashtags(context=None, count=10, exclude_tags=None)`
Get hashtag recommendations.

**Parameters:**
- `context` (str): Context for recommendations (optional)
- `count` (int): Number of recommendations
- `exclude_tags` (list): Tags to exclude

**Returns:**
- Dictionary with recommendations and usage tips

#### `analyze_hashtag_combinations(days=30, end_date=None, min_posts=3)`
Analyze hashtag combinations.

**Returns:**
- Dictionary with top performing combinations

#### `get_hashtag_usage_patterns(days=90, end_date=None)`
Analyze hashtag usage patterns.

**Returns:**
- Dictionary with usage statistics and optimal count

## Response Format

All methods return a dictionary with a `status` field:

- `'success'`: Operation completed successfully
- `'no_data'`: No data available for analysis
- `'no_competitors'`: No competitor data available
- `'error'`: An error occurred

Example response:

```python
{
    'status': 'success',
    'period': {
        'start': '2025-12-29',
        'end': '2026-01-28',
        'days': 30
    },
    'summary': {
        'total_posts': 45,
        'avg_engagement_rate': 5.2,
        'total_likes': 2340,
        'total_comments': 187
    },
    'trend': {
        'direction': 'зростання',
        'change_percent': 12.5
    }
}
```

## Integration with Dashboard and Reports

The analytics modules are designed to work seamlessly with:

- **Dashboard**: Display real-time analytics and visualizations
- **Telegram Reports**: Generate automated reports with insights
- **AI Recommendations**: Provide data for AI-powered suggestions

## Error Handling

All methods include comprehensive error handling:

```python
result = performance.analyze_engagement_trends(days=30)

if result['status'] == 'error':
    print(f"Error: {result['message']}")
elif result['status'] == 'no_data':
    print("No data available for analysis")
else:
    # Process successful result
    pass
```

## Logging

All analytics operations are logged using the application's logging system:

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
```

Logs include:
- Operation start/completion
- Data ranges analyzed
- Errors and warnings

## Examples

See `example_usage.py` for comprehensive examples of all analytics features.

## Contributing

When adding new analytics features:

1. Follow the existing pattern (Repository for data access)
2. Include comprehensive docstrings
3. Return structured data suitable for both dashboard and reports
4. Use proper error handling and logging
5. Add examples to `example_usage.py`

## License

Part of the Instagram SMM Monitoring System.
