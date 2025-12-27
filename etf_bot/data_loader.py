import yfinance as yf
import pandas as pd
import os

class DataLoader:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    def fetch_data(self, ticker: str, interval: str = "1d") -> pd.DataFrame:
        """
        Fetch data from yfinance.
        """
        print(f"Fetching {ticker} ({interval}) from {self.start_date} to {self.end_date}...")
        try:
            df = yf.download(ticker, start=self.start_date, end=self.end_date, interval=interval, progress=False)
            if df.empty:
                print(f"Warning: No data found for {ticker} with interval {interval}")
                return df
            
            # yfinance often works better with auto_adjust=True or actions=True depending on version, 
            # but standard download returns OHLC.
            # Handle MultiIndex columns if present (common in recent yfinance)
            if isinstance(df.columns, pd.MultiIndex):
                # If ticker is the second level, drop it
                if ticker in df.columns.get_level_values(1):
                    df = df.xs(ticker, axis=1, level=1)
                
            # If still multi-index, try to just keep the first level if it matches OHLCV
            if isinstance(df.columns, pd.MultiIndex):
                 df.columns = df.columns.get_level_values(0)

            df.columns = [c.lower() for c in df.columns]
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def get_spy_data(self) -> pd.DataFrame:
        # SPY for indicators needs to be Daily usually, but user said "SPY 종가 기준".
        # Usually indicators are on daily.
        return self.fetch_data("SPY", "1d")

    def get_etf_data(self, ticker: str) -> pd.DataFrame:
        # ETF data needs to be Minute ("분봉") for precise entry/exit at specific times like 09:00, 10:00 etc.
        # Note: yfinance limits 1m data to 7 days, 2m/5m/15m/30m/60m to 60 days.
        # We will try to fetch 1h (60m) or 5m depending on need?
        # User asked for minute data. Let's try "1h" for a wider backtest range by default, 
        # or "5m" if they want strict intraday testing (limited history).
        # Given "Backtest", usually implies a longer period. 
        # However, 08:40, 09:30 implies sub-hourly granularity.
        # We will default to '5m' for now, but be aware of the 60-day limit.
        return self.fetch_data(ticker, "5m")
