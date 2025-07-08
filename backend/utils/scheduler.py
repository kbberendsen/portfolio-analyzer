from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.portfolio import calc_portfolio
from backend.services.db_supabase_sync import db_supabase_sync
from backend.utils.refresh_status import get_db_sync_status
from backend.utils.logger import scheduler_logger

scheduler = BackgroundScheduler()

def scheduled_portfolio_job():
    scheduler_logger.info("Running scheduled portfolio calculation...")
    try:
        calc_portfolio()
        scheduler_logger.info("Portfolio calculation completed successfully.")
    except Exception as e:
        scheduler_logger.exception(f"Portfolio calculation failed: {e}")

def scheduled_db_sync_job():
    if get_db_sync_status() == "running":
        scheduler_logger.info("Scheduled DB sync skipped: sync already running.")
        return

    scheduler_logger.info("Running scheduled DB sync...")
    try:
        db_supabase_sync()
        scheduler_logger.info("DB sync completed successfully.")
    except Exception as e:
        scheduler_logger.exception(f"DB sync failed: {e}")

def start_scheduled_tasks():
    scheduler.add_job(scheduled_db_sync_job, trigger='cron', hour=3, minute=0, id='daily_db_sync')
    scheduler.add_job(scheduled_portfolio_job, trigger='interval', hours=1, id='portfolio_every_1h')
    scheduler_logger.info("Scheduler started with 2 jobs (daily db sync and hourly portfolio calc).")
    scheduler.start()
