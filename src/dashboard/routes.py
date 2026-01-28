"""Dashboard routes."""
from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime, timedelta
from typing import Dict, Any, List
import io
import csv
from src.database.repository import Repository
from src.utils.logger import get_logger

bp = Blueprint('main', __name__)
logger = get_logger(__name__)


def get_date_range(period: str = '7d'):
    """Get date range based on period."""
    end_date = datetime.now()
    
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=7)
    
    return start_date, end_date


def format_number(num):
    """Format large numbers for display."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


@bp.route('/')
def index():
    """Homepage with key metrics dashboard."""
    try:
        repo = Repository()
        start_date, end_date = get_date_range('30d')
        
        # Get recent stats
        stats = repo.get_daily_stats_range(start_date, end_date)
        recent_posts = repo.get_recent_posts(limit=6)
        top_posts = repo.get_top_posts(limit=3, start_date=start_date, end_date=end_date)
        engagement_stats = repo.get_engagement_stats(start_date, end_date)
        recent_recommendations = repo.get_recent_recommendations(limit=5)
        
        # Calculate key metrics
        current_followers = stats[-1].followers_count if stats else 0
        prev_followers = stats[0].followers_count if stats else 0
        follower_growth = current_followers - prev_followers
        follower_growth_pct = (follower_growth / prev_followers * 100) if prev_followers > 0 else 0
        
        avg_reach = sum(s.reach for s in stats) / len(stats) if stats else 0
        avg_impressions = sum(s.impressions for s in stats) / len(stats) if stats else 0
        
        metrics = {
            'followers': {
                'value': format_number(current_followers),
                'change': follower_growth,
                'change_pct': round(follower_growth_pct, 1)
            },
            'engagement': {
                'value': f"{engagement_stats['avg_engagement']:.1f}%",
                'total_likes': engagement_stats['total_likes'],
                'total_comments': engagement_stats['total_comments']
            },
            'reach': {
                'value': format_number(int(avg_reach)),
                'total': sum(s.reach for s in stats)
            },
            'posts': {
                'value': engagement_stats['total_posts'],
                'period': '30 днів'
            }
        }
        
        repo.close()
        
        return render_template(
            'index.html',
            metrics=metrics,
            recent_posts=recent_posts,
            top_posts=top_posts,
            recommendations=recent_recommendations
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', error=str(e)), 500


@bp.route('/posts')
def posts():
    """Posts list with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        period = request.args.get('period', '30d')
        
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        all_posts = repo.get_posts_by_date_range(start_date, end_date)
        total = len(all_posts)
        
        # Simple pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        posts_list = all_posts[start_idx:end_idx]
        
        has_prev = page > 1
        has_next = end_idx < total
        
        repo.close()
        
        return render_template(
            'posts.html',
            posts=posts_list,
            page=page,
            has_prev=has_prev,
            has_next=has_next,
            total=total,
            period=period
        )
    except Exception as e:
        logger.error(f"Error loading posts: {e}")
        return render_template('posts.html', error=str(e)), 500


@bp.route('/analytics')
def analytics():
    """Analytics page with charts."""
    period = request.args.get('period', '30d')
    return render_template('analytics.html', period=period)


@bp.route('/competitors')
def competitors():
    """Competitor comparison page."""
    try:
        repo = Repository()
        competitors_list = repo.get_all_competitors()
        repo.close()
        
        return render_template('competitors.html', competitors=competitors_list)
    except Exception as e:
        logger.error(f"Error loading competitors: {e}")
        return render_template('competitors.html', error=str(e)), 500


@bp.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html')


@bp.route('/reports')
def reports():
    """Reports page."""
    return render_template('reports.html')


# API Endpoints
@bp.route('/api/metrics')
def api_metrics():
    """Get key metrics data."""
    try:
        period = request.args.get('period', '7d')
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        stats = repo.get_daily_stats_range(start_date, end_date)
        
        data = {
            'dates': [s.date.strftime('%Y-%m-%d') for s in stats],
            'followers': [s.followers_count for s in stats],
            'reach': [s.reach for s in stats],
            'impressions': [s.impressions for s in stats],
            'engagement': [s.engagement_rate for s in stats]
        }
        
        repo.close()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API metrics error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/engagement')
def api_engagement():
    """Get engagement data."""
    try:
        period = request.args.get('period', '30d')
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        posts = repo.get_posts_by_date_range(start_date, end_date)
        
        # Group by date
        engagement_by_date = {}
        for post in posts:
            date_key = post.posted_at.strftime('%Y-%m-%d')
            if date_key not in engagement_by_date:
                engagement_by_date[date_key] = {
                    'likes': 0,
                    'comments': 0,
                    'engagement_rate': []
                }
            engagement_by_date[date_key]['likes'] += post.likes_count
            engagement_by_date[date_key]['comments'] += post.comments_count
            engagement_by_date[date_key]['engagement_rate'].append(post.engagement_rate)
        
        data = {
            'dates': sorted(engagement_by_date.keys()),
            'likes': [engagement_by_date[d]['likes'] for d in sorted(engagement_by_date.keys())],
            'comments': [engagement_by_date[d]['comments'] for d in sorted(engagement_by_date.keys())],
            'engagement_rates': [
                sum(engagement_by_date[d]['engagement_rate']) / len(engagement_by_date[d]['engagement_rate'])
                if engagement_by_date[d]['engagement_rate'] else 0
                for d in sorted(engagement_by_date.keys())
            ]
        }
        
        repo.close()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API engagement error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/top-posts')
def api_top_posts():
    """Get top performing posts."""
    try:
        period = request.args.get('period', '30d')
        limit = request.args.get('limit', 10, type=int)
        
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        top_posts = repo.get_top_posts(limit=limit, start_date=start_date, end_date=end_date)
        
        data = [{
            'post_id': post.post_id,
            'caption': post.caption[:100] if post.caption else '',
            'engagement_rate': post.engagement_rate,
            'likes': post.likes_count,
            'comments': post.comments_count,
            'posted_at': post.posted_at.strftime('%Y-%m-%d %H:%M'),
            'thumbnail': post.thumbnail_url
        } for post in top_posts]
        
        repo.close()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API top posts error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/competitors-comparison')
def api_competitors_comparison():
    """Get competitors comparison data."""
    try:
        repo = Repository()
        competitors = repo.get_all_competitors()
        
        data = {
            'usernames': [c.username for c in competitors],
            'followers': [c.followers_count for c in competitors],
            'engagement_rates': [c.avg_engagement_rate for c in competitors],
            'posts_per_week': [c.posts_per_week for c in competitors]
        }
        
        repo.close()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API competitors error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/hashtags')
def api_hashtags():
    """Get top hashtags."""
    try:
        limit = request.args.get('limit', 20, type=int)
        repo = Repository()
        
        hashtags = repo.get_top_hashtags(limit=limit)
        trending = repo.get_trending_hashtags(limit=10)
        
        data = {
            'top_hashtags': [{
                'tag': f"#{h.tag}",
                'usage_count': h.usage_count,
                'avg_engagement': h.avg_engagement_rate
            } for h in hashtags],
            'trending': [{
                'tag': f"#{h.tag}",
                'trend_score': h.trend_score
            } for h in trending]
        }
        
        repo.close()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API hashtags error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/export/posts')
def export_posts():
    """Export posts data to CSV."""
    try:
        period = request.args.get('period', '30d')
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        posts = repo.get_posts_by_date_range(start_date, end_date)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'ID', 'Дата', 'Тип', 'Опис', 'Лайки', 'Коментарі',
            'Збереження', 'Охоплення', 'Покази', 'Engagement Rate'
        ])
        
        for post in posts:
            writer.writerow([
                post.post_id,
                post.posted_at.strftime('%Y-%m-%d %H:%M'),
                post.media_type,
                post.caption[:100] if post.caption else '',
                post.likes_count,
                post.comments_count,
                post.saves_count,
                post.reach,
                post.impressions,
                f"{post.engagement_rate:.2f}%"
            ])
        
        output.seek(0)
        repo.close()
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'posts_{period}.csv'
        )
    except Exception as e:
        logger.error(f"Export posts error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/export/stats')
def export_stats():
    """Export daily stats to CSV."""
    try:
        period = request.args.get('period', '30d')
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        stats = repo.get_daily_stats_range(start_date, end_date)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Дата', 'Підписники', 'Охоплення', 'Покази',
            'Візити профілю', 'Engagement Rate'
        ])
        
        for stat in stats:
            writer.writerow([
                stat.date.strftime('%Y-%m-%d'),
                stat.followers_count,
                stat.reach,
                stat.impressions,
                stat.profile_visits,
                f"{stat.engagement_rate:.2f}%"
            ])
        
        output.seek(0)
        repo.close()
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'stats_{period}.csv'
        )
    except Exception as e:
        logger.error(f"Export stats error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate analytics report."""
    try:
        data = request.get_json()
        period = data.get('period', '30d')
        
        repo = Repository()
        start_date, end_date = get_date_range(period)
        
        # Collect report data
        stats = repo.get_daily_stats_range(start_date, end_date)
        posts = repo.get_posts_by_date_range(start_date, end_date)
        top_posts = repo.get_top_posts(limit=5, start_date=start_date, end_date=end_date)
        engagement_stats = repo.get_engagement_stats(start_date, end_date)
        
        report = {
            'period': period,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'summary': {
                'total_posts': len(posts),
                'avg_engagement': engagement_stats['avg_engagement'],
                'total_likes': engagement_stats['total_likes'],
                'total_comments': engagement_stats['total_comments'],
                'follower_growth': stats[-1].followers_count - stats[0].followers_count if stats else 0
            },
            'top_posts': [{
                'post_id': p.post_id,
                'engagement_rate': p.engagement_rate,
                'likes': p.likes_count,
                'comments': p.comments_count
            } for p in top_posts]
        }
        
        repo.close()
        return jsonify(report)
    except Exception as e:
        logger.error(f"Generate report error: {e}")
        return jsonify({'error': str(e)}), 500
