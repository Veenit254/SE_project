# backend/app/db/models.py
from sqlalchemy import create_engine, Column, String, Numeric, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from app.core.config import settings
import pandas as pd

# Connect to TimescaleDB
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@contextmanager
def db_session():
    """Provides a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

# The Position model your portfolio manager uses
class Position(Base):
    __tablename__ = "positions"
    id = Column(String, primary_key=True)
    symbol = Column(String)
    quantity = Column(Numeric)
    entry_price = Column(Numeric)
    entry_time = Column(DateTime)
    exit_price = Column(Numeric)
    exit_time = Column(DateTime)
    side = Column(String)
    status = Column(String)
    account_id = Column(String)

# The function your Celery worker uses to insert market data
def upsert_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str, source: str):
    df = df.copy()
    df['symbol'] = symbol
    df['timeframe'] = timeframe
    df['source'] = source
    
    # FIX: Move the 'time' index into a standard column so it doesn't get deleted
    if df.index.name == 'time':
        df.reset_index(inplace=True)
        
    df.to_sql('ohlcv', engine, if_exists='append', index=False)