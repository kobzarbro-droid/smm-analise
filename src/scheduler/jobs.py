"""Scheduler manager for running scheduled tasks."""
import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config.settings import settings
from src.scheduler import tasks
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerManager:
    """Manage scheduled tasks using APScheduler."""
    
    def __init__(self):
        """Initialize scheduler manager."""
        self.scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
        self.is_running = False
    
    def setup_jobs(self):
        """Setup all scheduled jobs."""
        logger.info("Setting up scheduled jobs...")
        
        # Data collection - every hour
        self.scheduler.add_job(
            tasks.collect_data_task,
            trigger=IntervalTrigger(seconds=settings.DATA_COLLECTION_INTERVAL),
            id='collect_data',
            name='Data Collection',
            replace_existing=True
        )
        logger.info(f"✓ Data collection: every {settings.DATA_COLLECTION_INTERVAL}s")
        
        # Daily report - at specified time (default 20:00)
        daily_time = settings.DAILY_REPORT_TIME.split(':')
        self.scheduler.add_job(
            tasks.send_daily_report_task,
            trigger=CronTrigger(
                hour=int(daily_time[0]),
                minute=int(daily_time[1]),
                timezone=settings.TIMEZONE
            ),
            id='daily_report',
            name='Daily Report',
            replace_existing=True
        )
        logger.info(f"✓ Daily report: {settings.DAILY_REPORT_TIME}")
        
        # Weekly report - Monday at specified time (default 09:00)
        weekly_time = settings.WEEKLY_REPORT_TIME.split(':')
        self.scheduler.add_job(
            tasks.send_weekly_report_task,
            trigger=CronTrigger(
                day_of_week=settings.WEEKLY_REPORT_DAY,
                hour=int(weekly_time[0]),
                minute=int(weekly_time[1]),
                timezone=settings.TIMEZONE
            ),
            id='weekly_report',
            name='Weekly Report',
            replace_existing=True
        )
        logger.info(f"✓ Weekly report: Monday {settings.WEEKLY_REPORT_TIME}")
        
        # Monthly report - 1st of month at specified time (default 09:00)
        monthly_time = settings.MONTHLY_REPORT_TIME.split(':')
        self.scheduler.add_job(
            tasks.send_monthly_report_task,
            trigger=CronTrigger(
                day=1,
                hour=int(monthly_time[0]),
                minute=int(monthly_time[1]),
                timezone=settings.TIMEZONE
            ),
            id='monthly_report',
            name='Monthly Report',
            replace_existing=True
        )
        logger.info(f"✓ Monthly report: 1st of month {settings.MONTHLY_REPORT_TIME}")
        
        # AI recommendations - daily at 22:00
        self.scheduler.add_job(
            tasks.generate_ai_recommendations_task,
            trigger=CronTrigger(hour=22, minute=0, timezone=settings.TIMEZONE),
            id='ai_recommendations',
            name='AI Recommendations',
            replace_existing=True
        )
        logger.info("✓ AI recommendations: daily at 22:00")
        
        # Competitor analysis - daily at 23:00
        self.scheduler.add_job(
            tasks.analyze_competitors_task,
            trigger=CronTrigger(hour=23, minute=0, timezone=settings.TIMEZONE),
            id='analyze_competitors',
            name='Competitor Analysis',
            replace_existing=True
        )
        logger.info("✓ Competitor analysis: daily at 23:00")
        
        # Check daily targets - at 19:00
        self.scheduler.add_job(
            tasks.check_daily_targets_task,
            trigger=CronTrigger(hour=19, minute=0, timezone=settings.TIMEZONE),
            id='check_targets',
            name='Check Daily Targets',
            replace_existing=True
        )
        logger.info("✓ Check targets: daily at 19:00")
        
        # Database backup - daily at 02:00
        if settings.BACKUP_ENABLED:
            self.scheduler.add_job(
                tasks.backup_database_task,
                trigger=CronTrigger(hour=2, minute=0, timezone=settings.TIMEZONE),
                id='backup_database',
                name='Database Backup',
                replace_existing=True
            )
            logger.info("✓ Database backup: daily at 02:00")
        
        logger.info("All scheduled jobs configured successfully")
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.setup_jobs()
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Scheduler started successfully")
            self.print_jobs()
        else:
            logger.warning("Scheduler is already running")
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler is not running")
    
    def print_jobs(self):
        """Print all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        if jobs:
            logger.info(f"\n{'='*60}")
            logger.info("SCHEDULED JOBS:")
            logger.info(f"{'='*60}")
            for job in jobs:
                logger.info(f"  • {job.name} (ID: {job.id})")
                logger.info(f"    Next run: {job.next_run_time}")
            logger.info(f"{'='*60}\n")
        else:
            logger.info("No jobs scheduled")
    
    async def run_task_manually(self, task_name: str) -> bool:
        """
        Run a specific task manually.
        
        Args:
            task_name: Name of the task to run
            
        Returns:
            True if task ran successfully, False otherwise
        """
        if task_name not in tasks.AVAILABLE_TASKS:
            logger.error(f"Unknown task: {task_name}")
            return False
        
        logger.info(f"Running task manually: {task_name}")
        try:
            task_func = tasks.AVAILABLE_TASKS[task_name]
            await task_func()
            logger.info(f"Task completed: {task_name}")
            return True
        except Exception as e:
            logger.error(f"Error running task {task_name}: {e}", exc_info=True)
            return False
    
    def pause_job(self, job_id: str):
        """Pause a specific job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
    
    def get_job_info(self, job_id: str) -> Optional[dict]:
        """Get information about a specific job."""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time,
                'trigger': str(job.trigger)
            }
        return None
    
    async def keep_running(self):
        """Keep the scheduler running indefinitely."""
        logger.info("Scheduler is now running. Press Ctrl+C to stop.")
        try:
            # Keep the event loop running
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()


async def main():
    """Main function to run scheduler."""
    manager = SchedulerManager()
    manager.start()
    await manager.keep_running()


if __name__ == '__main__':
    asyncio.run(main())
