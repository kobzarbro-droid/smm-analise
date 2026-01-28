"""Main entry point for SMM Analytics system."""
import asyncio
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from src.scheduler.jobs import SchedulerManager
from src.database.models import init_db
from src.utils.logger import get_logger

logger = get_logger('main')


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main application function."""
    logger.info("="*60)
    logger.info("Instagram SMM Analytics System")
    logger.info("="*60)
    
    # Validate configuration
    errors = settings.validate()
    if errors:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error(f"  ✗ {error}")
        logger.error("\nPlease check your config/.env file")
        sys.exit(1)
    
    logger.info("✓ Configuration validated")
    
    # Ensure directories exist
    settings.ensure_directories()
    logger.info("✓ Directories initialized")
    
    # Initialize database
    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    try:
        logger.info("\nStarting scheduler...")
        scheduler = SchedulerManager()
        scheduler.start()
        
        # Run initial data collection
        logger.info("\nRunning initial data collection...")
        await scheduler.run_task_manually('collect_data')
        
        # Keep running
        logger.info("\n" + "="*60)
        logger.info("System is running. Press Ctrl+C to stop.")
        logger.info("="*60 + "\n")
        
        await scheduler.keep_running()
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutting down gracefully...")
        if 'scheduler' in locals():
            scheduler.stop()
        logger.info("Goodbye! 👋")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
