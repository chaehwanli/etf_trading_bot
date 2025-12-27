import yaml
import sys
import os
from etf_bot.data.loader import DataLoader

def load_config():
    if not os.path.exists("config.yaml"):
        print("config.yaml not found.")
        sys.exit(1)
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    data_cfg = config.get("data", {})
    tickers = config.get("tickers", {})
    
    start_date = data_cfg.get("start_date")
    end_date = data_cfg.get("end_date")
    cache_dir = data_cfg.get("cache_dir", "data")
    spy_interval = data_cfg.get("spy_interval", "1d")
    leverage_interval = data_cfg.get("leverage_interval", "5m")
    inverse_interval = data_cfg.get("inverse_interval", "5m")
    
    loader = DataLoader(start_date, end_date, cache_dir)
    
    print("--- Starting Data Fetch ---")
    
    # SPY Daily
    loader.fetch_data(tickers['spy'], interval=spy_interval, force_update=True)
    
    # ETFs Minute (5m)
    loader.fetch_data(tickers['leverage'], interval=leverage_interval, force_update=True)
    loader.fetch_data(tickers['inverse'], interval=inverse_interval, force_update=True)
    
    print("--- Data Fetch Complete ---")

if __name__ == "__main__":
    main()
