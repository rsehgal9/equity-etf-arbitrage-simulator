# Equity & ETF Arbitrage Simulator

A regime-aware statistical arbitrage simulator built in Python and Streamlit.

## Features
- Pairs trading using z-score mean reversion
- Regime filtering using rolling correlation and volatility
- Transaction cost modeling
- Trade entry/exit visualization
- Pair screener ranking multiple strategies

## Example Pairs
- KO / PEP
- V / MA
- IVV / SPY

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
