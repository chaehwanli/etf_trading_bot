# ETF Backtest Trading Bot

This project is a Python-based backtesting bot for tracking and trading KRX ETFs (KODEX Leverage, KODEX 200 Futures Inverse 2X) based on SPY daily technical indicators (RSI, MACD).

## Features
- **Configurable**: Manage all parameters via `config.yaml`.
- **Data Caching**: Downloads and caches `yfinance` data to CSV for faster repeated testing.
- **Intraday Simulation**: Uses 5-minute data for accurate entry/exit simulation.
- **Strategy**: Leverages SPY indicators (RSI > 70 Long, RSI < 30 Short) to trade Korean ETFs.

## Project Structure
- `etf_bot/`: Main package
  - `data_loader.py`: Data fetching and caching.
  - `indicators.py`: Technical indicator calculations.
  - `strategy.py`: Trading logic.
  - `backtester.py`: Backtesting engine.
- `fetch_data.py`: Script to download and cache data.
- `main.py`: Main script to run the simulation.
- `config.yaml`: Configuration file.

## Configuration (`config.yaml`)
You can adjust the following parameters:
- **Tickers**: SPY and ETF symbols.
- **Trading**:
  - `start_money`: Initial capital.
  - `entry_time`: Time of day to enter trades (e.g. "09:00").
  - `leverage`/`inverse`: Specific settings for each ETF type:
    - `stop_loss_pct`: Stop loss percentage (e.g., 0.03 for 3%).
    - `max_hold_days`: Maximum holding period in days.
    - `cooldown_days`: Days to wait after a loss before re-entering.
- **Data**:
  - `start_date` / `end_date`: Backtest period.
  - `cache_dir`: Directory for storing CSV files.

## Usage

### 1. Install Dependencies
```bash
pip install pandas numpy yfinance pyyaml tabulate
```

### 2. Fetch Data
Download and cache the data first:
```bash
python fetch_data.py
```
This will created a `data/` directory with CSV files.

### 3. Run Backtest
Execute the trading simulation:
```bash
python main.py
```
The results (Win Rate, PnL, etc.) will be printed to the console.
