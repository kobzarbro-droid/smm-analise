"""Telegram bot for SMM analytics notifications and reports."""
import asyncio
from typing import Optional
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from src.telegram.reports import DailyReport, WeeklyReport, MonthlyReport
from src.telegram.formatters import MessageFormatter
from src.database.repository import Repository
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot for sending reports and notifications."""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram bot.
        
        Args:
            token: Telegram bot token (defaults to settings)
            chat_id: Target chat ID (defaults to settings)
        """
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.formatter = MessageFormatter()
        self.repository = Repository()
        
        logger.info("TelegramBot initialized")
    
    async def initialize(self):
        """Initialize the bot application."""
        if self.application is None:
            self.application = Application.builder().token(self.token).build()
            self.bot = self.application.bot
            
            # Register command handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("daily", self.cmd_daily_report))
            self.application.add_handler(CommandHandler("weekly", self.cmd_weekly_report))
            self.application.add_handler(CommandHandler("monthly", self.cmd_monthly_report))
            self.application.add_handler(CommandHandler("stats", self.cmd_stats))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            
            # Initialize application
            await self.application.initialize()
            logger.info("Bot application initialized")
    
    async def shutdown(self):
        """Shutdown the bot application."""
        if self.application:
            await self.application.shutdown()
            logger.info("Bot application shutdown")
        
        if self.repository:
            self.repository.close()
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = ParseMode.HTML,
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Send a message to Telegram chat.
        
        Args:
            text: Message text
            chat_id: Target chat ID (defaults to self.chat_id)
            parse_mode: Parse mode for message formatting
            disable_web_page_preview: Disable link previews
            
        Returns:
            True if message sent successfully
        """
        if not self.bot:
            await self.initialize()
        
        target_chat_id = chat_id or self.chat_id
        
        try:
            # Split long messages (Telegram limit is 4096 characters)
            max_length = 4000
            if len(text) <= max_length:
                await self.bot.send_message(
                    chat_id=target_chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview
                )
            else:
                # Split into chunks
                chunks = []
                current_chunk = ""
                
                for line in text.split('\n'):
                    if len(current_chunk) + len(line) + 1 <= max_length:
                        current_chunk += line + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = line + '\n'
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Send chunks
                for i, chunk in enumerate(chunks):
                    await self.bot.send_message(
                        chat_id=target_chat_id,
                        text=chunk,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview
                    )
                    
                    # Small delay between chunks to avoid rate limiting
                    if i < len(chunks) - 1:
                        await asyncio.sleep(0.5)
            
            logger.info(f"Message sent to chat {target_chat_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def send_daily_report(self, date: Optional[datetime] = None) -> bool:
        """
        Send daily report.
        
        Args:
            date: Date for report (defaults to today)
            
        Returns:
            True if report sent successfully
        """
        try:
            daily_report = DailyReport(self.repository)
            report_text = await daily_report.generate(date)
            return await self.send_message(report_text)
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            error_msg = self.formatter.format_alert(
                f"Помилка генерації щоденного звіту: {str(e)}",
                level='error'
            )
            await self.send_message(error_msg)
            return False
    
    async def send_weekly_report(self, end_date: Optional[datetime] = None) -> bool:
        """
        Send weekly report.
        
        Args:
            end_date: End date of week (defaults to today)
            
        Returns:
            True if report sent successfully
        """
        try:
            weekly_report = WeeklyReport(self.repository)
            report_text = await weekly_report.generate(end_date)
            return await self.send_message(report_text)
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
            error_msg = self.formatter.format_alert(
                f"Помилка генерації тижневого звіту: {str(e)}",
                level='error'
            )
            await self.send_message(error_msg)
            return False
    
    async def send_monthly_report(self, month: Optional[datetime] = None) -> bool:
        """
        Send monthly report.
        
        Args:
            month: Month for report (defaults to current month)
            
        Returns:
            True if report sent successfully
        """
        try:
            monthly_report = MonthlyReport(self.repository)
            report_text = await monthly_report.generate(month)
            return await self.send_message(report_text)
        except Exception as e:
            logger.error(f"Error sending monthly report: {e}")
            error_msg = self.formatter.format_alert(
                f"Помилка генерації місячного звіту: {str(e)}",
                level='error'
            )
            await self.send_message(error_msg)
            return False
    
    async def send_notification(
        self,
        title: str,
        message: str,
        level: str = 'info'
    ) -> bool:
        """
        Send a notification message.
        
        Args:
            title: Notification title
            message: Notification message
            level: Alert level ('info', 'warning', 'error')
            
        Returns:
            True if notification sent successfully
        """
        emoji_map = {
            'info': 'ℹ️',
            'warning': self.formatter.EMOJI['warning'],
            'error': self.formatter.EMOJI['cross'],
            'success': self.formatter.EMOJI['checkmark']
        }
        
        emoji = emoji_map.get(level, 'ℹ️')
        
        notification_text = (
            f"{emoji} <b>{title}</b>\n\n"
            f"{message}"
        )
        
        return await self.send_message(notification_text)
    
    async def send_alert(self, alert_message: str, level: str = 'warning') -> bool:
        """
        Send an alert message.
        
        Args:
            alert_message: Alert message text
            level: Alert level
            
        Returns:
            True if alert sent successfully
        """
        alert_text = self.formatter.format_alert(alert_message, level)
        return await self.send_message(alert_text)
    
    # Command handlers
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_text = (
            f"{self.formatter.EMOJI['rocket']} <b>Вітаємо в SMM Analytics Bot!</b>\n\n"
            f"Я допоможу вам відстежувати ефективність вашого Instagram акаунту.\n\n"
            f"Доступні команди:\n"
            f"/daily - Щоденний звіт\n"
            f"/weekly - Тижневий звіт\n"
            f"/monthly - Місячний звіт\n"
            f"/stats - Швидка статистика\n"
            f"/status - Статус системи\n"
            f"/help - Допомога\n\n"
            f"{self.formatter.EMOJI['star']} Автоматичні звіти надходитимуть щодня о {settings.DAILY_REPORT_TIME}"
        )
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            f"{self.formatter.EMOJI['book']} <b>Довідка по командам:</b>\n\n"
            f"<b>/daily</b> - Отримати звіт за сьогоднішній день\n"
            f"Показує опубліковані пости, сторіс, статистику залученості та рекомендації AI.\n\n"
            f"<b>/weekly</b> - Отримати звіт за тиждень\n"
            f"Включає виконання цілей, топ-3 пости та порівняння з минулим тижнем.\n\n"
            f"<b>/monthly</b> - Отримати звіт за місяць\n"
            f"Повна статистика, ріст підписників, тренди та рекомендації.\n\n"
            f"<b>/stats</b> - Швидка статистика\n"
            f"Показує ключові метрики за останні 7 днів.\n\n"
            f"<b>/status</b> - Статус системи\n"
            f"Перевірити роботу всіх компонентів системи.\n\n"
            f"{self.formatter.EMOJI['bulb']} <b>Автоматичні звіти:</b>\n"
            f"• Щоденні звіти: {settings.DAILY_REPORT_TIME}\n"
            f"• Тижневі звіти: щопонеділка о {settings.WEEKLY_REPORT_TIME}\n"
            f"• Місячні звіти: 1-го числа о {settings.MONTHLY_REPORT_TIME}"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML
        )
    
    async def cmd_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command."""
        await update.message.reply_text(
            f"{self.formatter.EMOJI['clock']} Генерую щоденний звіт..."
        )
        
        await self.send_daily_report()
    
    async def cmd_weekly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weekly command."""
        await update.message.reply_text(
            f"{self.formatter.EMOJI['clock']} Генерую тижневий звіт..."
        )
        
        await self.send_weekly_report()
    
    async def cmd_monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monthly command."""
        await update.message.reply_text(
            f"{self.formatter.EMOJI['clock']} Генерую місячний звіт..."
        )
        
        await self.send_monthly_report()
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - quick statistics."""
        try:
            from datetime import timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Get quick stats
            posts = self.repository.get_posts_by_date_range(start_date, end_date)
            daily_stats = self.repository.get_daily_stats_range(start_date, end_date)
            
            if not daily_stats:
                await update.message.reply_text(
                    f"{self.formatter.EMOJI['warning']} Недостатньо даних для статистики"
                )
                return
            
            total_posts = len(posts)
            total_stories = sum(s.stories_count for s in daily_stats)
            total_likes = sum(s.total_likes for s in daily_stats)
            total_comments = sum(s.total_comments for s in daily_stats)
            avg_engagement = sum(s.avg_engagement_rate for s in daily_stats) / len(daily_stats)
            
            stats_text = (
                f"{self.formatter.format_header('Швидка статистика', self.formatter.EMOJI['chart'])}\n\n"
                f"{self.formatter.EMOJI['calendar']} <b>Останні 7 днів</b>\n\n"
                f"{self.formatter.EMOJI['camera']} Пости: <b>{total_posts}</b>\n"
                f"{self.formatter.EMOJI['video']} Сторіс: <b>{total_stories}</b>\n"
                f"{self.formatter.EMOJI['heart']} Лайки: <b>{self.formatter.format_number(total_likes)}</b>\n"
                f"{self.formatter.EMOJI['comment']} Коментарі: <b>{self.formatter.format_number(total_comments)}</b>\n"
                f"{self.formatter.EMOJI['chart']} Залученість: <b>{self.formatter.format_percentage(avg_engagement)}</b>\n\n"
            )
            
            # Best post
            if posts:
                best_post = max(posts, key=lambda p: p.engagement_rate)
                stats_text += (
                    f"{self.formatter.format_section('Найкращий пост', self.formatter.EMOJI['trophy'])}\n"
                    f"{self.formatter.format_post_summary(best_post)}"
                )
            
            await update.message.reply_text(
                stats_text,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error generating stats: {e}")
            await update.message.reply_text(
                f"{self.formatter.EMOJI['cross']} Помилка отримання статистики"
            )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - system status."""
        try:
            # Check database
            db_status = "✅" if self.repository else "❌"
            
            # Check recent data
            recent_posts = self.repository.get_recent_posts(limit=1)
            last_update = recent_posts[0].updated_at if recent_posts else None
            
            if last_update:
                hours_ago = (datetime.utcnow() - last_update).total_seconds() / 3600
                data_status = "✅" if hours_ago < 24 else "⚠️"
                last_update_text = f"{hours_ago:.1f} годин тому"
            else:
                data_status = "❌"
                last_update_text = "Немає даних"
            
            status_text = (
                f"{self.formatter.format_header('Статус системи', '🔧')}\n\n"
                f"{db_status} <b>База даних:</b> {'Підключено' if db_status == '✅' else 'Помилка'}\n"
                f"{data_status} <b>Останнє оновлення:</b> {last_update_text}\n"
                f"✅ <b>Telegram бот:</b> Працює\n"
                f"✅ <b>Версія:</b> 1.0.0\n\n"
                f"{self.formatter.EMOJI['calendar']} <b>Налаштування:</b>\n"
                f"• Часовий пояс: {settings.TIMEZONE}\n"
                f"• Щоденний звіт: {settings.DAILY_REPORT_TIME}\n"
                f"• Збір даних: кожні {settings.DATA_COLLECTION_INTERVAL // 60} хв"
            )
            
            await update.message.reply_text(
                status_text,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            await update.message.reply_text(
                f"{self.formatter.EMOJI['cross']} Помилка перевірки статусу"
            )
    
    async def start_polling(self):
        """Start the bot in polling mode."""
        if not self.application:
            await self.initialize()
        
        logger.info("Starting bot polling...")
        
        try:
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES
            )
            logger.info("Bot is running in polling mode")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
        finally:
            if self.application.updater.running:
                await self.application.updater.stop()
            await self.application.stop()
            await self.shutdown()
    
    def run_polling(self):
        """Run the bot in polling mode (blocking)."""
        asyncio.run(self.start_polling())


# Standalone functions for scheduled tasks
async def send_scheduled_daily_report(
    token: Optional[str] = None,
    chat_id: Optional[str] = None
):
    """
    Send daily report (for scheduled tasks).
    
    Args:
        token: Bot token
        chat_id: Target chat ID
    """
    bot = TelegramBot(token, chat_id)
    try:
        await bot.initialize()
        await bot.send_daily_report()
    finally:
        await bot.shutdown()


async def send_scheduled_weekly_report(
    token: Optional[str] = None,
    chat_id: Optional[str] = None
):
    """
    Send weekly report (for scheduled tasks).
    
    Args:
        token: Bot token
        chat_id: Target chat ID
    """
    bot = TelegramBot(token, chat_id)
    try:
        await bot.initialize()
        await bot.send_weekly_report()
    finally:
        await bot.shutdown()


async def send_scheduled_monthly_report(
    token: Optional[str] = None,
    chat_id: Optional[str] = None
):
    """
    Send monthly report (for scheduled tasks).
    
    Args:
        token: Bot token
        chat_id: Target chat ID
    """
    bot = TelegramBot(token, chat_id)
    try:
        await bot.initialize()
        await bot.send_monthly_report()
    finally:
        await bot.shutdown()


# Entry point for testing
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run_polling()
