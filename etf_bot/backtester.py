import pandas as pd
import numpy as np
from datetime import timedelta, time
from .strategy import Strategy, SignalType
from .data_loader import DataLoader
from .indicators import Indicators

class Backtester:
    def __init__(self, 
                 start_date: str, 
                 end_date: str, 
                 strategy: Strategy,
                 time_entry: str = "09:00", # "HH:MM"
                 stop_loss_pct: float = 0.03,
                 max_hold_days: int = 5,
                 cooldown_days: int = 0):
        self.start_date = start_date
        self.end_date = end_date
        self.strategy = strategy
        self.entry_time = pd.Timestamp(time_entry).time()
        self.stop_loss_pct = stop_loss_pct
        self.max_hold_days = max_hold_days
        self.cooldown_days = cooldown_days
        
        self.loader = DataLoader(start_date, end_date)
        self.trade_log = []
        self.balance_curve = []
        
        # Tickers
        self.ticker_leverage = "122630.KS"
        self.ticker_inverse = "252670.KS"
        self.ticker_spy = "SPY"

    def run(self):
        # 1. Load Data
        print("Loading data...")
        df_spy = self.loader.get_spy_data()
        df_lev = self.loader.get_etf_data(self.ticker_leverage)
        df_inv = self.loader.get_etf_data(self.ticker_inverse)
        
        if df_spy.empty or df_lev.empty or df_inv.empty:
            print("Insufficient data to proceed.")
            return

        # 2. Prepare Indicators for SPY
        df_spy['rsi'] = Indicators.calculate_rsi(df_spy['close'])
        macd, sig, _ = Indicators.calculate_macd(df_spy['close'])
        df_spy['macd'] = macd
        df_spy['macd_signal'] = sig
        
        # Date Adjustment:
        # SPY valid at Date D (Close) is used for Trading Date D+1.
        # We process SPY index to be the "Trading Decision Date" (Signal Date + 1 Day).
        # We align by naive date (YYYY-MM-DD) to avoid TZ confusion.
        
        # Convert index to naive date + 1 day
        spy_decision_dates = df_spy.index.to_series().apply(lambda x: (x + timedelta(days=1)).date())
        df_spy.index = spy_decision_dates
        
        # 3. Simulate
        lev_dates = df_lev.index.normalize().unique()
        inv_dates = df_inv.index.normalize().unique()
        all_dates = sorted(list(set(lev_dates).union(inv_dates)))
        
        position = None 
        cooldown_until = None
        
        history = []
        
        print("Starting simulation loop...")
        for current_dt_ts in all_dates:
            current_date_obj = current_dt_ts.date()
            
            # Check cooldown
            if cooldown_until and current_dt_ts < cooldown_until:
                continue

                
            # If we have a position, check exit conditions (Hold limit)
            # Checking SL is intra-day.
            
            # --- Intraday Logic ---
            # Extract intraday data for this date
            day_data_lev = df_lev[df_lev.index.normalize() == current_dt_ts]
            day_data_inv = df_inv[df_inv.index.normalize() == current_dt_ts]
            
            if day_data_lev.empty or day_data_inv.empty:
                continue

            # 1. Entry Logic (at entry_time)
            # Find closest bar to entry_time
            # entry_time e.g. 09:00.
            
            # Calculate entry_dt correctly handling Timezones
            # Combine Date + Time -> Localize KST -> Convert UTC
            dt_naive = pd.Timestamp.combine(current_date_obj, self.entry_time)
            
            # Note: current_date_obj is naive date.
            try:
                entry_dt_kst = dt_naive.tz_localize("Asia/Seoul")
                entry_dt = entry_dt_kst.tz_convert("UTC")
            except Exception as e:
                # If dt_naive is somehow already localized?
                print(f"TZ Error: {e}")
                entry_dt = dt_naive

            # If not in position, check for signal
            if position is None:
                if current_date_obj in df_spy.index:
                    spy_row = df_spy.loc[current_date_obj]
                    # Debug print (limit to first few or verbose)
                    # print(f"Date {current_date_obj}: RSI {spy_row['rsi']:.2f}, MACD {spy_row['macd']:.2f}/{spy_row['macd_signal']:.2f}")
                    signal = self.strategy.decide_direction(spy_row['rsi'], spy_row['macd'], spy_row['macd_signal'])
                    if signal != SignalType.NEUTRAL:
                        pass
                        # print(f"Signal {signal} on {current_date_obj}")
                    
                    target_ticker = None
                    target_df = None
                    
                    if signal == SignalType.BUY_LEVERAGE:
                        target_ticker = self.ticker_leverage
                        target_df = day_data_lev
                        pos_type = 'LEV'
                    elif signal == SignalType.BUY_INVERSE:
                        target_ticker = self.ticker_inverse
                        target_df = day_data_inv
                        pos_type = 'INV'
                    
                    if target_ticker:
                        # Market Entry at entry_time
                        # Find bar at or after entry_time
                        future_bars = target_df[target_df.index >= entry_dt]
                        
                        if not future_bars.empty:
                            entry_bar = future_bars.iloc[0]
                            entry_price = entry_bar['open'] # Assume Open of that minute bar ~ Market Price
                            # Or Close if we want to be conservative about "slippage" or "confirmation".
                            # Prompt: "시장가 주문 ... 슬리피지 반영". 
                            # Let's use Open of the bar, maybe add minimal slippage if needed.
                            # For simplicity: Use Open.
                            
                            position = {
                                'type': pos_type,
                                'ticker': target_ticker,
                                'entry_price': entry_price,
                                'entry_time': entry_bar.name,
                                'highest_pnl': 0
                            }
                            # Log Entry
                            history.append({
                                'action': 'ENTRY',
                                'date': entry_bar.name,
                                'ticker': target_ticker,
                                'price': entry_price,
                                'notes': f"Signal: {signal.value}"
                            })

            # 2. Monitoring Position (SL / Time Exit)
            if position:
                current_ticker = position['ticker']
                current_df = day_data_lev if current_ticker == self.ticker_leverage else day_data_inv
                
                # Filter for bars AFTER entry
                monitoring_bars = current_df[current_df.index > position['entry_time']]
                
                for timestamp, row in monitoring_bars.iterrows():
                    current_price = row['close']
                    # Calculate PnL
                    # Long only logic for ETFs (we buy Inverse ETF, we don't short sell)
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                    
                    # Check Stop Loss
                    if pnl_pct <= -self.stop_loss_pct:
                        # Trigger SL
                        history.append({
                            'action': 'EXIT_SL',
                            'date': timestamp,
                            'ticker': current_ticker,
                            'price': current_price,
                            'pnl': pnl_pct
                        })
                        position = None
                        # Set Cooldown
                        cooldown_until = current_dt_ts + timedelta(days=self.cooldown_days)
                        break
                    
                    # Check Max Hold Time (if defined by days, checked at day start? Or continuous?)
                    # Prompt: "최대 보유 일수".
                    # If current_date - entry_date >= max_hold_days?
                    # Let's check:
                    time_held = timestamp - position['entry_time']
                    if time_held.days >= self.max_hold_days:
                         # Trigger Time Exit
                        history.append({
                            'action': 'EXIT_TIME',
                            'date': timestamp,
                            'ticker': current_ticker,
                            'price': current_price,
                            'pnl': pnl_pct
                        })
                        position = None
                        break
                
                # End of Day Check? Nothing specific, carry over position.

        self.trade_log = pd.DataFrame(history)
        return self.trade_log

    def get_summary(self):
        if self.trade_log.empty:
            return "No trades executed."
        
        exits = self.trade_log[self.trade_log['action'].str.contains('EXIT')]
        if exits.empty:
            return "Trades opened but none closed."
            
        total_trades = len(exits)
        wins = len(exits[exits['pnl'] > 0])
        win_rate = wins / total_trades if total_trades > 0 else 0
        avg_pnl = exits['pnl'].mean()
        cum_pnl = (1 + exits['pnl']).prod() - 1
        
        # MDD calculation (Needs full equity curve ideally, simplified here on closed trades)
        cum_returns = (1 + exits['pnl']).cumprod()
        peak = cum_returns.cummax()
        drawdown = (cum_returns - peak) / peak
        mdd = drawdown.min()

        return {
            "Total Trades": total_trades,
            "Win Rate": f"{win_rate:.2%}",
            "Avg PnL": f"{avg_pnl:.2%}",
            "Cumulative Return": f"{cum_pnl:.2%}",
            "MDD": f"{mdd:.2%}"
        }
