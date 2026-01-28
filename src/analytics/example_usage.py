"""
Example usage of analytics modules.

This script demonstrates how to use the analytics modules to:
1. Analyze performance metrics
2. Compare with competitors
3. Analyze hashtag effectiveness
"""
from datetime import datetime, timedelta
from src.analytics import PerformanceAnalyzer, CompetitorAnalyzer, HashtagAnalyzer


def main():
    """Main function to demonstrate analytics usage."""
    
    print("=== Instagram SMM Analytics Demo ===\n")
    
    # Initialize analyzers
    performance = PerformanceAnalyzer()
    competitors = CompetitorAnalyzer()
    hashtags = HashtagAnalyzer()
    
    try:
        # 1. Performance Analysis
        print("1. Analyzing Performance Trends...")
        print("-" * 50)
        
        trends = performance.analyze_engagement_trends(days=30)
        if trends['status'] == 'success':
            summary = trends['summary']
            print(f"Total Posts: {summary['total_posts']}")
            print(f"Avg Engagement Rate: {summary['avg_engagement_rate']}%")
            print(f"Total Likes: {summary['total_likes']}")
            print(f"Total Comments: {summary['total_comments']}")
            print(f"Trend: {trends['trend']['direction']}")
        else:
            print(f"Status: {trends['status']}")
        
        print("\n2. Finding Best Posting Times...")
        print("-" * 50)
        
        timing = performance.find_best_posting_times(days=90)
        if timing['status'] == 'success':
            print("Best Hours:")
            for hour_data in timing['best_hours'][:3]:
                print(f"  - {hour_data['hour']:02d}:00 "
                      f"({hour_data['avg_engagement_rate']}% engagement)")
            
            print("\nBest Days:")
            for day_data in timing['best_days']:
                print(f"  - {day_data['day_name']} "
                      f"({day_data['avg_engagement_rate']}% engagement)")
        else:
            print(f"Status: {timing['status']}")
        
        print("\n3. Content Type Performance...")
        print("-" * 50)
        
        content = performance.analyze_content_type_performance(days=30)
        if content['status'] == 'success':
            for ctype in content['content_types']:
                print(f"{ctype['type_name']}: "
                      f"{ctype['avg_engagement_rate']}% engagement "
                      f"({ctype['count']} posts)")
        else:
            print(f"Status: {content['status']}")
        
        print("\n4. Top Performing Posts...")
        print("-" * 50)
        
        top_posts = performance.get_top_performing_posts(limit=5, days=30)
        if top_posts['status'] == 'success':
            for i, post in enumerate(top_posts['top_posts'], 1):
                print(f"{i}. {post['media_type']} - "
                      f"{post['engagement_rate']}% engagement")
                print(f"   Likes: {post['likes_count']}, "
                      f"Comments: {post['comments_count']}")
        else:
            print(f"Status: {top_posts['status']}")
        
        # 2. Competitor Analysis
        print("\n\n5. Competitor Comparison...")
        print("-" * 50)
        
        comparison = competitors.compare_with_competitors(days=30)
        if comparison['status'] == 'success':
            print("Your Metrics:")
            own = comparison['own_metrics']
            print(f"  - Engagement Rate: {own['avg_engagement_rate']}%")
            print(f"  - Avg Likes: {own['avg_likes']}")
            print(f"  - Avg Comments: {own['avg_comments']}")
            
            print("\nCompetitor Averages:")
            comp_avg = comparison['competitor_averages']
            print(f"  - Engagement Rate: {comp_avg['avg_engagement_rate']}%")
            print(f"  - Avg Likes: {comp_avg['avg_likes']}")
            print(f"  - Avg Comments: {comp_avg['avg_comments']}")
        else:
            print(f"Status: {comparison['status']}")
        
        print("\n6. Finding Gaps and Opportunities...")
        print("-" * 50)
        
        gaps = competitors.find_competitor_gaps()
        if gaps['status'] == 'success':
            if gaps.get('opportunities'):
                print("Opportunities for Improvement:")
                for opp in gaps['opportunities']:
                    print(f"  - {opp['metric']}: {opp['recommendation']}")
            
            if gaps.get('strengths'):
                print("\nYour Strengths:")
                for strength in gaps['strengths']:
                    print(f"  - {strength['message']}")
        else:
            print(f"Status: {gaps['status']}")
        
        print("\n7. Performance Benchmarking...")
        print("-" * 50)
        
        benchmark = competitors.benchmark_performance()
        if benchmark['status'] == 'success':
            rankings = benchmark['rankings']
            print(f"Performance Level: {benchmark['performance_level']}")
            print(f"Engagement Rank: {rankings['engagement']['rank']} "
                  f"of {rankings['engagement']['total']} "
                  f"({rankings['engagement']['percentile']}th percentile)")
        else:
            print(f"Status: {benchmark['status']}")
        
        # 3. Hashtag Analysis
        print("\n\n8. Hashtag Effectiveness...")
        print("-" * 50)
        
        hashtag_analysis = hashtags.analyze_hashtag_effectiveness(days=30)
        if hashtag_analysis['status'] == 'success':
            print(f"Total Unique Hashtags: {hashtag_analysis['total_unique_hashtags']}")
            
            high_performers = hashtag_analysis['high_performers']
            if high_performers:
                print("\nHigh Performing Hashtags:")
                for tag_data in high_performers[:5]:
                    print(f"  - #{tag_data['tag']}: "
                          f"{tag_data['avg_engagement_rate']}% engagement "
                          f"({tag_data['usage_count']} uses)")
        else:
            print(f"Status: {hashtag_analysis['status']}")
        
        print("\n9. Trending Hashtags...")
        print("-" * 50)
        
        trending = hashtags.get_trending_hashtags(limit=10)
        if trending['status'] == 'success' and trending['trending_hashtags']:
            for tag_data in trending['trending_hashtags'][:5]:
                print(f"  - #{tag_data['tag']}: "
                      f"{tag_data['avg_engagement_rate']}% engagement")
        else:
            print(f"Status: {trending['status']}")
        
        print("\n10. Hashtag Recommendations...")
        print("-" * 50)
        
        recommendations = hashtags.recommend_hashtags(count=10)
        if recommendations['status'] == 'success':
            print("Recommended Hashtags:")
            for rec in recommendations['recommendations'][:5]:
                print(f"  - #{rec['tag']}: Score {rec['score']} "
                      f"({rec['reason']})")
        else:
            print(f"Status: {recommendations['status']}")
        
        print("\n11. Hashtag Usage Patterns...")
        print("-" * 50)
        
        patterns = hashtags.get_hashtag_usage_patterns(days=90)
        if patterns['status'] == 'success':
            stats = patterns['statistics']
            print(f"Avg Hashtags per Post: {stats['avg_hashtags_per_post']}")
            print(f"Unique Hashtags Used: {stats['unique_hashtags']}")
            
            if patterns.get('optimal_count'):
                optimal = patterns['optimal_count']
                print(f"Optimal Count Range: {optimal['hashtag_count_range']} "
                      f"({optimal['avg_engagement_rate']}% engagement)")
        else:
            print(f"Status: {patterns['status']}")
        
        print("\n12. Getting Comprehensive Insights...")
        print("-" * 50)
        
        insights = performance.get_performance_insights(days=30)
        if insights['status'] == 'success' and insights.get('insights'):
            print("Key Insights:")
            for insight in insights['insights']:
                print(f"  [{insight['type'].upper()}] {insight['title']}")
                print(f"    {insight['message']}")
        else:
            print(f"Status: {insights['status']}")
        
    finally:
        # Close connections
        performance.close()
        competitors.close()
        hashtags.close()
    
    print("\n" + "=" * 50)
    print("Analytics demo completed!")


if __name__ == '__main__':
    main()
