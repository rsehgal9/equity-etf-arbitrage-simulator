# Equity & ETF Arbitrage Simulator

A simple, interactive trading simulator that finds pricing inefficiencies between related stocks and ETFs and tests whether those differences can be profitably traded.

---

## 🧠 What This Project Does

This project simulates a trading strategy that looks for **temporary mispricing between two related assets** (for example, Coca-Cola vs Pepsi, or two similar ETFs).

When the prices move too far apart:
- the strategy assumes they will move back together
- it places a trade to profit from that “reversion”

This type of strategy is commonly used in quantitative trading and is known as **statistical arbitrage**.

---

## 💡 Example

If two companies or ETFs usually move together:

- If one becomes unusually expensive → the model **sells it**
- If one becomes unusually cheap → the model **buys it**

When prices return to normal, the trade is closed for a profit.

---

## ⚙️ Key Features

- 📊 **Mean-Reversion Strategy**
  - Uses statistical signals to detect when prices diverge from normal levels

- 🧠 **Regime Filter**
  - Avoids trading when the relationship between assets becomes unstable

- 💸 **Transaction Cost Modeling**
  - Simulates realistic trading by including costs

- 📈 **Performance Metrics**
  - Tracks:
    - Total return  
    - Sharpe ratio (risk-adjusted return)  
    - Max drawdown (risk)  
    - Win rate  

- 🖥️ **Interactive Dashboard (Streamlit)**
  - Visualizes:
    - price movements  
    - trading signals  
    - portfolio performance  

---

## 🧪 Assets Tested

The model can be applied to:

### Stocks
- KO / PEP (consumer staples)
- V / MA (financials)
- XOM / CVX (energy)

### ETFs
- IVV / SPY (S&P 500)
- QQQ / XLK (technology)

---

## 🚀 How to Run

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/equity-arbitrage-simulator.git
cd equity-arbitrage-simulator
