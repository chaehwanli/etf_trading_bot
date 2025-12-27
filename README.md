# ETF Backtest Trading Bot

This project is a Python-based backtesting bot for tracking and trading KRX ETFs (KODEX Leverage, KODEX 200 Futures Inverse 2X) based on SPY daily technical indicators (RSI, MACD).

## Features
- **Configurable**: Manage all parameters via `config.yaml`.
- **Data Caching**: Downloads and caches `yfinance` data to CSV for faster repeated testing.
- **Intraday Simulation**: Uses 5-minute data for accurate entry/exit simulation.
- **Strategy**: Leverages SPY indicators (RSI > 70 Long, RSI < 30 Short) to trade Korean ETFs.

## Project Structure
- `etf_bot/`: Main package
  - `data/`: Data management
    - `loader.py`: Data fetching and caching.
  - `strategies/`: Trading strategies
    - `strategy.py`: Trading logic.
  - `engine/`: Simulation core
    - `backtester.py`: Backtesting engine.
  - `utils/`: Utilities
    - `indicators.py`: Technical indicator calculations.
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
The bot requires Python 3.9+.

#### Windows
1. Install Python from [python.org](https://www.python.org/downloads/windows/). Ensure "Add Python to PATH" is checked.
2. Open PowerShell or Command Prompt.
3. Install dependencies:
   ```powershell
   pip install pandas numpy yfinance pyyaml
   ```
   *Note: If you encounter errors installing numpy/pandas, you may need to install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).*

#### macOS / Linux
1. Install Python (if not available):
   - **macOS**: `brew install python`
   - **Linux**: `sudo apt install python3 python3-pip`
2. Open Terminal.
3. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install pandas numpy yfinance pyyaml
   ```

### 2. Configuration
Edit `config.yaml`:
- Set `system.os` to your operating system (`windows`, `macos`, or `linux`).
- Adjust trading parameters and dates as needed.

### 3. Fetch Data
Download and cache the data first:
```bash
python fetch_data.py
```
This will create a `data/` directory with CSV files.

### 4. Run Backtest
Execute the trading simulation:
```bash
python main.py
```
The results (Win Rate, PnL, etc.) will be printed to the console.
