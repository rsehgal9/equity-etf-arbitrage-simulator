# Equity & ETF Statistical Arbitrage Simulator

A Python-based trading simulator that identifies and tests pricing inefficiencies between related equities and exchange-traded funds (ETFs) using a mean-reversion framework.

---

## Overview

This project implements a statistical arbitrage strategy designed to capture temporary divergences in price between correlated assets. The model assumes that certain assets—such as companies within the same industry or ETFs tracking similar indices—tend to move together over time.

When the price relationship between two assets deviates significantly from its historical norm, the strategy enters a trade anticipating that the spread will revert.

---

## Strategy Logic

The simulator follows a structured process:

1. **Spread Construction**  
   Computes the log-price spread between two assets to measure relative mispricing.

2. **Signal Generation**  
   Uses a rolling z-score to identify when the spread deviates from its historical mean.

3. **Trade Execution**  
   - Enters positions when deviations exceed predefined thresholds  
   - Exits positions when the spread normalizes  

4. **Regime Filtering**  
   Applies filters based on rolling correlation and spread volatility to avoid trading during unstable market conditions.

5. **Performance Evaluation**  
   Tracks key performance metrics including total return, Sharpe ratio, maximum drawdown, and win rate.

---

## Key Features

- Mean-reversion strategy using statistical signals  
- Regime-aware filtering to improve signal quality  
- Transaction cost modeling for realistic simulation  
- Interactive dashboard built with Streamlit  
- Visualization of price series, signals, and portfolio performance  

---

## Example Asset Pairs

The model can be applied across multiple asset classes:

**Equities**
- KO / PEP  
- V / MA  
- XOM / CVX  

**ETFs**
- IVV / SPY  
- QQQ / XLK  

---

## Installation and Usage

1. Clone the repository:
```bash
git clone https://github.com/rsehgal9/equity-arbitrage-simulator.git
cd equity-arbitrage-simulator
