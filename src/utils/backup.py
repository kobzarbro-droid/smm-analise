"""Database backup utilities."""
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """Manager for database backups."""
    
    def __init__(self):
        """Initialize backup manager."""
        self.backup_dir = settings.BACKUPS_DIR
        self.retention_days = settings.BACKUP_RETENTION_DAYS
        settings.ensure_directories()
    
    def create_backup(self, db_path: Optional[Path] = None) -> Optional[Path]:
        """
        Create a backup of the database.
        
        Args:
            db_path: Path to database file (optional)
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            # Get database path
            if db_path is None:
                db_url = settings.DATABASE_URL
                if db_url.startswith('sqlite:///'):
                    db_path = Path(db_url.replace('sqlite:///', ''))
                else:
                    logger.error("Only SQLite databases are supported for backup")
                    return None
            
            if not db_path.exists():
                logger.error(f"Database file not found: {db_path}")
                return None
            
            # Create backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"smm_analise_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Create backup using SQLite backup API for consistency
            source_conn = sqlite3.connect(str(db_path))
            backup_conn = sqlite3.connect(str(backup_path))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            logger.info(f"Backup created successfully: {backup_path}")
            
            # Clean old backups
            self.cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            return None
    
    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period.
        
        Returns:
            Number of backups removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            for backup_file in self.backup_dir.glob('smm_analise_backup_*.db'):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file.name}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backup(s)")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}", exc_info=True)
            return 0
    
    def restore_backup(self, backup_path: Path, db_path: Optional[Path] = None) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            db_path: Path to restore to (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Get database path
            if db_path is None:
                db_url = settings.DATABASE_URL
                if db_url.startswith('sqlite:///'):
                    db_path = Path(db_url.replace('sqlite:///', ''))
                else:
                    logger.error("Only SQLite databases are supported")
                    return False
            
            # Create backup of current database before restoring
            if db_path.exists():
                current_backup = db_path.parent / f"{db_path.stem}_before_restore_{datetime.now():%Y%m%d_%H%M%S}.db"
                shutil.copy2(db_path, current_backup)
                logger.info(f"Created safety backup: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}", exc_info=True)
            return False
    
    def list_backups(self) -> list:
        """
        List all available backups.
        
        Returns:
            List of backup file paths sorted by date (newest first)
        """
        backups = list(self.backup_dir.glob('smm_analise_backup_*.db'))
        return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
