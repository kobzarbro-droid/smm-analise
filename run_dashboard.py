"""Web dashboard launcher."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.dashboard.app import create_app
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger('dashboard')


def main():
    """Launch Flask dashboard."""
    logger.info("="*60)
    logger.info("Instagram SMM Analytics - Web Dashboard")
    logger.info("="*60)
    
    # Validate configuration
    errors = settings.validate()
    if errors:
        logger.warning("Some configuration values are missing:")
        for error in errors:
            logger.warning(f"  ⚠ {error}")
        logger.warning("Dashboard will start but some features may not work")
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Create Flask app
    app = create_app()
    
    # Run the app
    host = settings.DASHBOARD_HOST
    port = settings.DASHBOARD_PORT
    debug = settings.DEBUG
    
    logger.info(f"\n🚀 Dashboard starting on http://{host}:{port}")
    logger.info("="*60 + "\n")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("\nDashboard stopped by user")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
