# backend/seed_data.py
from app.ingestion.fetchers import YahooFetcher
from app.db.models import upsert_ohlcv
from datetime import datetime, timedelta

def run():
    fetcher = YahooFetcher()
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d') # 5 Years ago
    
    print(f"Fetching AAPL data from {start} to {end}...")
    df = fetcher.get_daily("AAPL", start, end)
    
    print(f"Got {len(df)} daily bars. Injecting into TimescaleDB...")
    upsert_ohlcv(df, "AAPL", "1D", "yahoo")
    
    print("Data successfully saved to the hypertable!")

if __name__ == "__main__":
    run()