import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from backend.db.base import Base 
from backend.models.portfolio_daily import PortfolioPerformanceDailyTable
from backend.models.stock_prices import StockPricesTable
from backend.utils.logger import app_logger
import time

POSTGRES_USER = os.getenv("POSTGRES_USER", "portfolio_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "default_pass1234!")
POSTGRES_DB = os.getenv("POSTGRES_DB", "portfolio_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(POSTGRES_URL)

def wait_for_db():
    """
    At startup, wait for the database to be ready before proceeding.
    This function is called from the main application's startup event.
    """
    MAX_RETRIES = 15
    RETRY_DELAY = 5  # seconds

    for i in range(MAX_RETRIES):
        try:
            app_logger.info(f"[DB] Attempting to connect to the database (attempt {i+1}/{MAX_RETRIES})...")
            connection = engine.connect()
            connection.close()
            app_logger.info("[DB] Database connection successful.")
            return
        except OperationalError:
            app_logger.warning(f"[DB] Database connection failed. Retrying in {RETRY_DELAY} seconds...")
            if i + 1 == MAX_RETRIES:
                app_logger.error("[DB] Could not connect to the database after multiple retries. Application will not start.")
                raise
            time.sleep(RETRY_DELAY)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to use in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    app_logger.info("[DB] Ensuring all tables exist in the database...")
    Base.metadata.create_all(bind=engine)
    app_logger.info("[DB] Table check complete.")

def delete_all_data():
    db = SessionLocal()
    try:
        # Ensure tables exist, create if missing
        Base.metadata.create_all(bind=engine)

        # Clear rows from tables
        db.query(PortfolioPerformanceDailyTable).delete()
        db.query(StockPricesTable).delete()

        db.commit()
        app_logger.info("[DB] All data deleted from tables.")
    except OperationalError as e:
        db.rollback()
        raise RuntimeError(f"Database operation failed: {e}")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

from sqlalchemy.exc import OperationalError

def check_postgres_connection():
    try:
        app_logger.info("[DB CHECK] Attempting to connect to Postgres...")
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        app_logger.info("[DB CHECK] Successfully connected to Postgres.")
        return True
    except OperationalError as e:
        app_logger.error(f"[DB CHECK] PostgreSQL connection failed: {e}")
        return False
    except Exception as e:
        app_logger.error(f"[DB CHECK] Unexpected error during DB connection check: {e}")
        return False

def load_portfolio_performance_from_db():
    db = SessionLocal()
    try:
        rows = db.query(PortfolioPerformanceDailyTable).all()

        # Extract dicts, excluding _sa_instance_state
        data = [
            {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
            for r in rows
        ]

        if not data:
            # Get column names from the SQLAlchemy model
            columns = [c.name for c in PortfolioPerformanceDailyTable.__table__.columns]
            # Return empty DataFrame with these columns
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(data)

    finally:
        db.close()

def load_stock_prices_from_db():
    db = SessionLocal()
    try:
        rows = db.query(StockPricesTable).all()

        # Extract dicts, excluding _sa_instance_state
        data = [
            {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
            for r in rows
        ]

        if not data:
            # Get column names from the SQLAlchemy model
            columns = [c.name for c in StockPricesTable.__table__.columns]
            # Return empty DataFrame with these columns
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(data)

    finally:
        db.close()
        
def save_portfolio_performance_to_db(df):
    db = SessionLocal()
    try:
        records = df.to_dict(orient="records")
        table = PortfolioPerformanceDailyTable.__table__

        stmt = insert(table).values(records)
        update_cols = {c.name: c for c in stmt.excluded if c.name not in ['ticker', 'end_date']}
        # Assumes 'ticker' and 'end_date' are PK, exclude them from update

        stmt = stmt.on_conflict_do_update(
            index_elements=['ticker', 'end_date'],
            set_=update_cols
        )

        db.execute(stmt)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def save_stock_prices_to_db(df):
    db = SessionLocal()
    try:
        records = df.to_dict(orient="records")
        table = StockPricesTable.__table__

        stmt = insert(table).values(records)
        update_cols = {c.name: c for c in stmt.excluded if c.name not in ['ticker', 'date']}
        # 'ticker' and 'date' as PK, exclude from update

        stmt = stmt.on_conflict_do_update(
            index_elements=['ticker', 'date'],
            set_=update_cols
        )

        db.execute(stmt)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()