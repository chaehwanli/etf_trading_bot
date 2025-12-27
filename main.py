import sys
import pandas as pd
from datetime import datetime, timedelta
from etf_bot.backtester import Backtester
from etf_bot.strategy import Strategy

def run_backtest_scenario(scenario_name, rsi_long, rsi_short, entry_time="09:00", sl_pct=0.03):
    print(f"\n========================================")
    print(f"Running Scenario: {scenario_name}")
    print(f"Params: RSI {rsi_long}/{rsi_short}, Time {entry_time}, SL {sl_pct}")
    print(f"========================================")
    
    # Date Range: Last 30 days to ensure 5m data availability
    # Current "simulated" date is 2025-12-27. 
    # Let's try 2025-11-25 to 2025-12-25.
    
    start_date = "2025-11-25"
    end_date = "2025-12-25"
    
    strategy = Strategy(rsi_long_threshold=rsi_long, rsi_short_threshold=rsi_short)
    
    backtester = Backtester(
        start_date=start_date,
        end_date=end_date,
        strategy=strategy,
        time_entry=entry_time,
        stop_loss_pct=sl_pct,
        max_hold_days=3,
        cooldown_days=0
    )
    
    backtester.run()
    results = backtester.get_summary()
    return results

def main():
    scenarios = [
        {"name": "Base Case", "rsi_long": 70, "rsi_short": 30, "entry_time": "09:00", "sl_pct": 0.03},
        {"name": "Aggressive RSI", "rsi_long": 60, "rsi_short": 40, "entry_time": "09:00", "sl_pct": 0.03},
        {"name": "Tight SL", "rsi_long": 70, "rsi_short": 30, "entry_time": "09:00", "sl_pct": 0.01},
        # {"name": "Pre-Market (08:40)", "rsi_long": 70, "rsi_short": 30, "entry_time": "08:40", "sl_pct": 0.03} # Data might be an issue
    ]
    
    all_results = []
    
    for sc in scenarios:
        res = run_backtest_scenario(sc["name"], sc["rsi_long"], sc["rsi_short"], sc["entry_time"], sc["sl_pct"])
        if isinstance(res, dict):
            res['Scenario'] = sc["name"]
            all_results.append(res)
        else:
            print(f"Skipping {sc['name']}: {res}")
        
    print("\n\n################ RESULT SUMMARY ################")
    df_res = pd.DataFrame(all_results)
    if not df_res.empty:
        # Reorder columns
        cols = ['Scenario'] + [c for c in df_res.columns if c != 'Scenario']
        print(df_res[cols].to_string(index=False))
    else:
        print("No results generated.")

if __name__ == "__main__":
    main()
