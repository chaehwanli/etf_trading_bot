import pandas as pd
import numpy as np
from datetime import timedelta, time
from ..strategies.strategy import Strategy, SignalType
from ..data.loader import DataLoader
from ..utils.indicators import Indicators

class Backtester:
    def __init__(self, config: dict, strategy: Strategy):
        self.config = config
        self.strategy = strategy
        
        # Config Parsing
        trading_cfg = config.get("trading", {})
        data_cfg = config.get("data", {})
        tickers_cfg = config.get("tickers", {})
        
        self.start_date = data_cfg.get("start_date")
        self.end_date = data_cfg.get("end_date")
        self.cache_dir = data_cfg.get("cache_dir", "data")
        
        entry_time_str = trading_cfg.get("entry_time", "09:00")
        self.entry_time = pd.Timestamp(entry_time_str).time()
        self.entry_time_str = entry_time_str
        
        # Tickers
        self.ticker_leverage = tickers_cfg.get("leverage")
        self.ticker_inverse = tickers_cfg.get("inverse")
        self.ticker_spy = tickers_cfg.get("spy")
        
        # Trading Params per ETF
        self.lev_params = trading_cfg.get("leverage", {})
        self.inv_params = trading_cfg.get("inverse", {})
        
        self.loader = DataLoader(self.start_date, self.end_date, self.cache_dir)
        self.trade_log = []
        
    def get_params(self, ticker):
        if ticker == self.ticker_leverage:
            return self.lev_params
        return self.inv_params

    def run(self):
        # 1. Load Data
        print("Loading data...")
        df_spy = self.loader.fetch_data(self.ticker_spy, "1d")
        df_lev = self.loader.fetch_data(self.ticker_leverage, "5m")
        df_inv = self.loader.fetch_data(self.ticker_inverse, "5m")
        
        if df_spy.empty or df_lev.empty or df_inv.empty:
            print("Insufficient data.")
            return

        # 2. Prepare Indicators for SPY
        df_spy['rsi'] = Indicators.calculate_rsi(df_spy['close'])
        macd, sig, _ = Indicators.calculate_macd(df_spy['close'])
        df_spy['macd'] = macd
        df_spy['macd_signal'] = sig
        
        # Date Adjustment: SPY D-1 Close -> KRX D Open
        spy_decision_dates = df_spy.index.to_series().apply(lambda x: (x + timedelta(days=1)).date())
        df_spy.index = spy_decision_dates
        
        # 3. Simulate
        lev_dates = df_lev.index.normalize().unique()
        inv_dates = df_inv.index.normalize().unique()
        all_dates = sorted(list(set(lev_dates).union(inv_dates)))
        print(f"Total days: {len(all_dates)}")
        
        position = None 
        cooldown_until = None
        
        history = []
        
        for current_dt_ts in all_dates:
            current_date_obj = current_dt_ts.date()
            
            # Check cooldown
            if cooldown_until and current_dt_ts < cooldown_until:
                continue
                
            # --- Intraday Logic ---
            # Extract intraday data
            day_data_lev = df_lev[df_lev.index.normalize() == current_dt_ts]
            day_data_inv = df_inv[df_inv.index.normalize() == current_dt_ts]
            
            if day_data_lev.empty or day_data_inv.empty:
                continue

            # Calculate Entry Time (UTC)
            dt_naive = pd.Timestamp.combine(current_date_obj, self.entry_time)
            try:
                entry_dt_kst = dt_naive.tz_localize("Asia/Seoul")
                entry_dt = entry_dt_kst.tz_convert("UTC")
            except Exception as e:
                # If already tz-aware or error, assume UTC match for safety or just use input
                entry_dt = dt_naive

            # 1. Entry Logic
            if position is None:
                if current_date_obj in df_spy.index:
                    spy_row = df_spy.loc[current_date_obj]
                    signal = self.strategy.decide_direction(spy_row['rsi'], spy_row['macd'], spy_row['macd_signal'])
                    
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
                        future_bars = target_df[target_df.index >= entry_dt]
                        if not future_bars.empty:
                            entry_bar = future_bars.iloc[0]
                            entry_price = entry_bar['open']
                            
                            position = {
                                'type': pos_type,
                                'ticker': target_ticker,
                                'entry_price': entry_price,
                                'entry_time': entry_bar.name,
                            }
                            history.append({
                                'action': 'ENTRY',
                                'date': entry_bar.name,
                                'ticker': target_ticker,
                                'price': entry_price,
                                'signal': signal.value
                            })

            # 2. Monitoring
            if position:
                current_ticker = position['ticker']
                params = self.get_params(current_ticker)
                
                sl_pct = params.get('stop_loss_pct', 0.03)
                max_hold_days = params.get('max_hold_days', 5)
                cooldown_days = params.get('cooldown_days', 0)
                
                current_df = day_data_lev if current_ticker == self.ticker_leverage else day_data_inv
                monitoring_bars = current_df[current_df.index > position['entry_time']]
                
                for timestamp, row in monitoring_bars.iterrows():
                    current_price = row['close']
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                    
                    # Stop Loss
                    if pnl_pct <= -sl_pct:
                        history.append({
                            'action': 'EXIT_SL',
                            'date': timestamp,
                            'ticker': current_ticker,
                            'price': current_price,
                            'pnl': pnl_pct
                        })
                        position = None
                        cooldown_until = current_dt_ts + timedelta(days=cooldown_days)
                        break
                    
                    # Time Exit
                    time_held = timestamp - position['entry_time']
                    if time_held.days >= max_hold_days:
                        history.append({
                            'action': 'EXIT_TIME',
                            'date': timestamp,
                            'ticker': current_ticker,
                            'price': current_price,
                            'pnl': pnl_pct
                        })
                        position = None
                        break

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
        return {
            "Total Trades": total_trades,
            "Win Rate": f"{win_rate:.2%}",
            "Avg PnL": f"{avg_pnl:.2%}",
            "Cumulative Return": f"{cum_pnl:.2%}"
        }
