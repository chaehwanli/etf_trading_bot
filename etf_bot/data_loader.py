import yfinance as yf
import pandas as pd
import os
import shutil

class DataLoader:
    def __init__(self, start_date: str, end_date: str, cache_dir: str = "data"):
        self.start_date = start_date
        self.end_date = end_date
        self.cache_dir = cache_dir
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_data(self, ticker: str, interval: str = "1d", force_update: bool = False) -> pd.DataFrame:
        """
        Fetch data from cache or yfinance.
        """
        # File name safely
        safe_ticker = ticker.replace(".", "_")
        cache_file = os.path.join(self.cache_dir, f"{safe_ticker}_{interval}_{self.start_date}_{self.end_date}.csv")
        
        if not force_update and os.path.exists(cache_file):
            print(f"Loading {ticker} ({interval}) from cache...")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            # Ensure index is tz-aware if it was saved as such (CSV loses some metadata, but ISO helps)
            return df
            
        print(f"Fetching {ticker} ({interval}) from {self.start_date} to {self.end_date} (Force: {force_update})...")
        try:
            # Add small buffer to end date because yfinance end is exclusive?
            # Actually yfinance uses inclusive start, exclusive end.
            df = yf.download(ticker, start=self.start_date, end=self.end_date, interval=interval, progress=False)
            
            if df.empty:
                print(f"Warning: No data found for {ticker} with interval {interval}")
                return df
            
            # Cleaning Data
            if isinstance(df.columns, pd.MultiIndex):
                if ticker in df.columns.get_level_values(1):
                    df = df.xs(ticker, axis=1, level=1)
            
            if isinstance(df.columns, pd.MultiIndex):
                 df.columns = df.columns.get_level_values(0)

            df.columns = [c.lower() for c in df.columns]
            
            # Save to Cache
            df.to_csv(cache_file)
            print(f"Saved {ticker} to {cache_file}")
            
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def clean_cache(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
            print("Cache cleared.")
