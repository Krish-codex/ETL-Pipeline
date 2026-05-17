"""
Scheduler — Automatic Pipeline Execution
==========================================
Runs the ETL pipeline at a scheduled interval (e.g., every 30 minutes).

Usage:
    python scheduler.py

This keeps the weather data fresh by automatically re-running
the pipeline on a schedule. In production, you'd use something
like cron (Linux) or Task Scheduler (Windows), but this Python-based
scheduler is great for development and demos.

Press Ctrl+C to stop the scheduler.
"""

import time
from datetime import datetime

import schedule

from scripts.logger_setup import get_logger

logger = get_logger("scheduler")

# How often to run the pipeline (in minutes)
INTERVAL_MINUTES = 30


def run_scheduled_pipeline():
    """Wrapper that runs the full pipeline and logs the result."""
    logger.info(f"⏰ Scheduled run triggered at {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Import here to avoid circular imports
        from main import run_full_pipeline

        success = run_full_pipeline()
        if success:
            logger.info("✅ Scheduled run completed successfully")
        else:
            logger.warning("⚠️ Scheduled run completed with errors")

    except Exception as e:
        logger.error(f"❌ Scheduled run failed: {e}")


def main():
    """Sets up and starts the scheduler."""
    print(f"\n{'═' * 50}")
    print(f"  🕐 ETL Pipeline Scheduler")
    print(f"  Running every {INTERVAL_MINUTES} minutes")
    print(f"  Press Ctrl+C to stop")
    print(f"{'═' * 50}\n")

    # Schedule the pipeline to run at the defined interval
    schedule.every(INTERVAL_MINUTES).minutes.do(run_scheduled_pipeline)

    # Also run immediately on start
    logger.info("Running pipeline immediately on scheduler start...")
    run_scheduled_pipeline()

    # Keep the scheduler alive
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Scheduler stopped by user")
        print("\nScheduler stopped. Goodbye!")
