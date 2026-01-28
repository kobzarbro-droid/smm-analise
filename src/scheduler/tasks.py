"""Individual scheduled tasks."""
from datetime import datetime, timedelta
from typing import Optional
from config.settings import settings
from src.instagram.client import InstagramClient
from src.instagram.collector import DataCollector
from src.ai.recommendations import RecommendationGenerator
from src.telegram.bot import TelegramBot
from src.telegram.reports import DailyReport, WeeklyReport, MonthlyReport
from src.analytics.competitors import CompetitorAnalyzer
from src.utils.backup import BackupManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def collect_data_task():
    """Task to collect Instagram data."""
    logger.info("Running data collection task...")
    
    try:
        client = InstagramClient()
        if not client.login():
            logger.error("Failed to login to Instagram")
            return
        
        collector = DataCollector(client)
        stats = collector.collect_all()
        
        logger.info(f"Data collection completed: {stats}")
        collector.close()
        
    except Exception as e:
        logger.error(f"Error in data collection task: {e}", exc_info=True)


async def send_daily_report_task():
    """Task to send daily report to Telegram."""
    logger.info("Generating and sending daily report...")
    
    try:
        report = DailyReport()
        message = report.generate()
        
        if message:
            bot = TelegramBot()
            await bot.send_daily_report()
            logger.info("Daily report sent successfully")
        else:
            logger.warning("Failed to generate daily report")
            
    except Exception as e:
        logger.error(f"Error sending daily report: {e}", exc_info=True)


async def send_weekly_report_task():
    """Task to send weekly report to Telegram."""
    logger.info("Generating and sending weekly report...")
    
    try:
        report = WeeklyReport()
        message = report.generate()
        
        if message:
            bot = TelegramBot()
            await bot.send_weekly_report()
            logger.info("Weekly report sent successfully")
        else:
            logger.warning("Failed to generate weekly report")
            
    except Exception as e:
        logger.error(f"Error sending weekly report: {e}", exc_info=True)


async def send_monthly_report_task():
    """Task to send monthly report to Telegram."""
    logger.info("Generating and sending monthly report...")
    
    try:
        report = MonthlyReport()
        message = report.generate()
        
        if message:
            bot = TelegramBot()
            await bot.send_monthly_report()
            logger.info("Monthly report sent successfully")
        else:
            logger.warning("Failed to generate monthly report")
            
    except Exception as e:
        logger.error(f"Error sending monthly report: {e}", exc_info=True)


async def generate_ai_recommendations_task():
    """Task to generate AI recommendations."""
    logger.info("Generating AI recommendations...")
    
    try:
        rec_gen = RecommendationGenerator()
        
        # Generate batch recommendations for last 7 days
        batch_recs = rec_gen.generate_batch_recommendations(days=7)
        
        # Generate general recommendations for last 30 days
        general_recs = rec_gen.generate_general_recommendations(period_days=30)
        
        logger.info("AI recommendations generated successfully")
        rec_gen.close()
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}", exc_info=True)


async def analyze_competitors_task():
    """Task to analyze competitor accounts."""
    logger.info("Analyzing competitors...")
    
    try:
        # Get competitor usernames from config
        competitors = settings.get_target('competitors', [])
        
        if not competitors:
            logger.info("No competitors configured")
            return
        
        client = InstagramClient()
        if not client.login():
            logger.error("Failed to login to Instagram")
            return
        
        collector = DataCollector(client)
        
        for username in competitors:
            try:
                logger.info(f"Analyzing competitor: @{username}")
                competitor_data = collector.collect_competitor_data(username)
                if competitor_data:
                    logger.info(f"Competitor data collected for @{username}")
            except Exception as e:
                logger.error(f"Error analyzing competitor {username}: {e}")
        
        collector.close()
        logger.info("Competitor analysis completed")
        
    except Exception as e:
        logger.error(f"Error in competitor analysis task: {e}", exc_info=True)


async def backup_database_task():
    """Task to backup database."""
    logger.info("Running database backup...")
    
    try:
        if not settings.BACKUP_ENABLED:
            logger.info("Backup is disabled in settings")
            return
        
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup()
        
        if backup_path:
            logger.info(f"Database backup created: {backup_path}")
        else:
            logger.error("Failed to create database backup")
            
    except Exception as e:
        logger.error(f"Error in backup task: {e}", exc_info=True)


async def check_daily_targets_task():
    """Task to check if daily targets are met and send alerts."""
    logger.info("Checking daily targets...")
    
    try:
        from src.database.repository import Repository
        
        repo = Repository()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_stat = repo.get_daily_stat(today)
        
        if not daily_stat:
            logger.info("No statistics available for today yet")
            return
        
        # Get targets
        targets = settings.load_targets().get('targets', {})
        stories_target = targets.get('stories_per_day', 3)
        min_engagement = targets.get('min_engagement_rate', 3.5)
        
        alerts = []
        
        # Check stories target
        if daily_stat.stories_count < stories_target:
            alerts.append(
                f"⚠️ Увага! Опубліковано {daily_stat.stories_count} stories з {stories_target} запланованих."
            )
        
        # Check engagement
        if daily_stat.avg_engagement_rate < min_engagement:
            alerts.append(
                f"⚠️ Engagement нижче норми: {daily_stat.avg_engagement_rate}% (мінімум {min_engagement}%)"
            )
        
        # Send alerts if any
        if alerts:
            bot = TelegramBot()
            alert_message = "🚨 <b>АЛЕРТИ</b>\n\n" + "\n".join(alerts)
            await bot.send_notification(alert_message)
            logger.info(f"Sent {len(alerts)} alert(s)")
        else:
            logger.info("All daily targets met, no alerts needed")
        
        repo.close()
        
    except Exception as e:
        logger.error(f"Error checking daily targets: {e}", exc_info=True)


# Dictionary of all available tasks
AVAILABLE_TASKS = {
    'collect_data': collect_data_task,
    'daily_report': send_daily_report_task,
    'weekly_report': send_weekly_report_task,
    'monthly_report': send_monthly_report_task,
    'ai_recommendations': generate_ai_recommendations_task,
    'analyze_competitors': analyze_competitors_task,
    'backup_database': backup_database_task,
    'check_targets': check_daily_targets_task,
}
