#!/usr/bin/env python3
"""
Example script demonstrating Telegram bot usage.

This script shows how to:
1. Initialize the bot
2. Send different types of reports
3. Send notifications and alerts
4. Use the formatter utilities

Note: Requires valid TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment or config/.env
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.telegram.bot import TelegramBot
from src.telegram.formatters import MessageFormatter
from src.telegram.reports import DailyReport, WeeklyReport, MonthlyReport


async def example_send_reports():
    """Example: Send all types of reports."""
    print("=== Example: Sending Reports ===\n")
    
    # Initialize bot
    bot = TelegramBot()
    
    try:
        # Initialize the bot application
        await bot.initialize()
        print("✓ Bot initialized\n")
        
        # Send daily report
        print("Sending daily report...")
        success = await bot.send_daily_report()
        print(f"{'✓' if success else '✗'} Daily report sent\n")
        
        # Wait a bit to avoid rate limiting
        await asyncio.sleep(1)
        
        # Send weekly report
        print("Sending weekly report...")
        success = await bot.send_weekly_report()
        print(f"{'✓' if success else '✗'} Weekly report sent\n")
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Send monthly report
        print("Sending monthly report...")
        success = await bot.send_monthly_report()
        print(f"{'✓' if success else '✗'} Monthly report sent\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await bot.shutdown()
        print("Bot shutdown complete")


async def example_send_notifications():
    """Example: Send various notifications."""
    print("=== Example: Sending Notifications ===\n")
    
    bot = TelegramBot()
    
    try:
        await bot.initialize()
        
        # Info notification
        print("Sending info notification...")
        await bot.send_notification(
            title="Система запущена",
            message="Моніторинг Instagram акаунту активний",
            level="info"
        )
        print("✓ Info notification sent\n")
        
        await asyncio.sleep(0.5)
        
        # Success notification
        print("Sending success notification...")
        await bot.send_notification(
            title="Ціль досягнута!",
            message="Сьогодні опубліковано 3 пости - місячна ціль виконана!",
            level="success"
        )
        print("✓ Success notification sent\n")
        
        await asyncio.sleep(0.5)
        
        # Warning alert
        print("Sending warning alert...")
        await bot.send_alert(
            "Залученість нижче цільової: 2.1% (ціль: 3.5%)",
            level="warning"
        )
        print("✓ Warning alert sent\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await bot.shutdown()


async def example_formatter_usage():
    """Example: Using MessageFormatter utilities."""
    print("=== Example: MessageFormatter Usage ===\n")
    
    formatter = MessageFormatter()
    
    # Progress bars
    print("Progress bars:")
    print(f"  20%: {formatter.progress_bar(2, 10)}")
    print(f"  50%: {formatter.progress_bar(5, 10)}")
    print(f"  80%: {formatter.progress_bar(8, 10)}")
    print(f" 100%: {formatter.progress_bar(10, 10)}")
    print()
    
    # Number formatting
    print("Number formatting:")
    print(f"  999 → {formatter.format_number(999)}")
    print(f"  1,234 → {formatter.format_number(1234)}")
    print(f"  12,345 → {formatter.format_number(12345)}")
    print(f"  1,234,567 → {formatter.format_number(1234567)}")
    print()
    
    # Dates
    print("Date formatting:")
    date = datetime(2024, 1, 15, 14, 30)
    print(f"  Short: {formatter.format_date(date, 'short')}")
    print(f"  Long: {formatter.format_date(date, 'long')}")
    print(f"  Time: {formatter.format_time(date)}")
    print()
    
    # Changes
    print("Change formatting:")
    print(f"  Growth: {formatter.format_change(150, 100)}")
    print(f"  Decline: {formatter.format_change(80, 100)}")
    print(f"  Stable: {formatter.format_change(100, 100)}")
    print()
    
    # Target progress
    print("Target progress:")
    progress = formatter.format_target_progress("Пости", 15, 20, "📷")
    print(progress.replace('\n', '\n  '))
    print()
    
    # Engagement stats
    print("Engagement statistics:")
    stats = formatter.format_engagement_stats(1234, 56, 78, 4.5)
    print(stats.replace('\n', '\n  '))
    print()
    
    # Recommendations
    print("Recommendations:")
    recs = formatter.format_recommendations([
        "Публікуйте більше Reels для збільшення охоплення",
        "Використовуйте актуальні хештеги",
        "Взаємодійте з коментарями швидше"
    ])
    print(recs.replace('\n', '\n  '))
    print()


async def example_generate_reports_text():
    """Example: Generate report texts without sending."""
    print("=== Example: Generating Report Texts ===\n")
    
    # Daily report
    print("Generating daily report text...")
    daily = DailyReport()
    daily_text = await daily.generate()
    print(f"Daily report length: {len(daily_text)} characters")
    print("Preview (first 300 chars):")
    print(daily_text[:300] + "...\n")
    daily.close()
    
    # Weekly report
    print("Generating weekly report text...")
    weekly = WeeklyReport()
    weekly_text = await weekly.generate()
    print(f"Weekly report length: {len(weekly_text)} characters")
    print("Preview (first 300 chars):")
    print(weekly_text[:300] + "...\n")
    weekly.close()
    
    # Monthly report
    print("Generating monthly report text...")
    monthly = MonthlyReport()
    monthly_text = await monthly.generate()
    print(f"Monthly report length: {len(monthly_text)} characters")
    print("Preview (first 300 chars):")
    print(monthly_text[:300] + "...\n")
    monthly.close()


async def main():
    """Run all examples."""
    print("╔════════════════════════════════════════╗")
    print("║  Telegram Bot Module Examples         ║")
    print("╚════════════════════════════════════════╝\n")
    
    # Choose which examples to run
    examples = [
        ("Formatter Usage", example_formatter_usage, False),  # Safe to run without bot
        ("Generate Reports Text", example_generate_reports_text, False),  # Safe
        ("Send Reports", example_send_reports, True),  # Requires bot token
        ("Send Notifications", example_send_notifications, True),  # Requires bot token
    ]
    
    for name, func, requires_bot in examples:
        try:
            if requires_bot:
                # Check if bot credentials are available
                from config.settings import settings
                if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
                    print(f"⊘ Skipping '{name}' - requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID\n")
                    continue
            
            await func()
            print("─" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"✗ Error in '{name}': {e}\n")
            continue
    
    print("All examples completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
