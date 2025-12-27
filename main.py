import sys
import yaml
import os
import pandas as pd
from etf_bot.backtester import Backtester
from etf_bot.strategy import Strategy

def load_config():
    if not os.path.exists("config.yaml"):
        print("config.yaml not found.")
        sys.exit(1)
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    
    # We can still loop scenarios by overriding config in memory if we want,
    # or just run single config.
    # User asked to "configure via config", essentially enabling param settings.
    # Let's run a single backtest based on config.yaml values for simplicity of the request, 
    # OR we can keep scenarios but apply config defaults.
    # Let's run ONE main backtest based on 'config.yaml'.
    
    print("Running Backtest with Configuration:")
    print(yaml.dump(config.get("trading"), default_flow_style=False))
    
    # Strategy Params (Hardcoded or could be in config too... let's add them to config logic implicitly or explicitly)
    # The Prompt said: "RSI 및 MACD의 조합 조건은 파라미터화 가능하도록 설계 필요"
    # But detailed params weren't explicitly in the user's config request list.
    # Let's assume standard 70/30 for now or add to config if needed. 
    # I'll stick to 70/30 default for this run.
    
    strategy = Strategy(rsi_long_threshold=70, rsi_short_threshold=30)
    
    backtester = Backtester(config, strategy)
    backtester.run()
    
    results = backtester.get_summary()
    
    if isinstance(results, dict):
        print("\n=== Results ===")
        for k, v in results.items():
            print(f"{k}: {v}")
    else:
        print(results)

if __name__ == "__main__":
    main()
