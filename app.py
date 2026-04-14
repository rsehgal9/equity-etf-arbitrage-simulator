import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="Equity Arbitrage Simulator V2", layout="wide")

st.title("Equity Arbitrage Simulator V2")
st.markdown("Pairs trading backtest with optional regime filtering based on rolling correlation and spread volatility.")

# Sidebar inputs
st.sidebar.header("Strategy Settings")
ticker_1 = st.sidebar.text_input("Ticker 1", value="KO")
ticker_2 = st.sidebar.text_input("Ticker 2", value="PEP")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2025-01-01"))
window = st.sidebar.slider("Rolling Window", min_value=5, max_value=120, value=20)
entry_z = st.sidebar.slider("Entry Z-Score", min_value=0.5, max_value=3.0, value=2.0, step=0.1)
exit_z = st.sidebar.slider("Exit Z-Score", min_value=0.0, max_value=1.5, value=0.5, step=0.1)
transaction_cost_bps = st.sidebar.slider("Transaction Cost (bps)", min_value=0, max_value=50, value=10)

st.sidebar.subheader("Regime Filter")
use_regime_filter = st.sidebar.checkbox("Enable Regime Filter", value=True)
correlation_window = st.sidebar.slider("Correlation Window", min_value=10, max_value=120, value=60)
min_correlation = st.sidebar.slider("Minimum Correlation", min_value=0.0, max_value=1.0, value=0.6, step=0.05)
volatility_lookback = st.sidebar.slider("Volatility Lookback", min_value=20, max_value=180, value=60)
volatility_multiplier = st.sidebar.slider("Max Volatility Multiplier", min_value=0.5, max_value=3.0, value=1.5, step=0.1)
show_trade_markers = st.sidebar.checkbox("Show Trade Markers", value=True)


def load_data(t1: str, t2: str, start, end) -> pd.DataFrame:
    data = yf.download([t1, t2], start=start, end=end, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError("No data returned. Check ticker symbols and date range.")

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            prices = data["Close"].copy()
        else:
            prices = data.xs("Close", axis=1, level=0, drop_level=True).copy()
    else:
        prices = data.copy()

    prices = prices[[t1, t2]].dropna()
    prices.columns = ["price_1", "price_2"]
    return prices


def build_signals(
    prices: pd.DataFrame,
    rolling_window: int,
    corr_window: int,
    min_corr: float,
    vol_lookback: int,
    vol_multiplier: float,
    use_regime: bool,
) -> pd.DataFrame:
    df = prices.copy()

    df["ret_1"] = df["price_1"].pct_change()
    df["ret_2"] = df["price_2"].pct_change()

    df["spread"] = np.log(df["price_1"]) - np.log(df["price_2"])
    df["spread_mean"] = df["spread"].rolling(rolling_window).mean()
    df["spread_std"] = df["spread"].rolling(rolling_window).std()
    df["z_score"] = (df["spread"] - df["spread_mean"]) / df["spread_std"]

    df["rolling_corr"] = df["ret_1"].rolling(corr_window).corr(df["ret_2"])
    df["spread_vol"] = df["spread"].rolling(rolling_window).std()
    df["spread_vol_baseline"] = df["spread_vol"].rolling(vol_lookback).mean()

    df["regime_on"] = (
        (df["rolling_corr"] >= min_corr)
        & (df["spread_vol"] <= df["spread_vol_baseline"] * vol_multiplier)
    )

    if not use_regime:
        df["regime_on"] = True

    df = df.dropna().copy()
    return df


def run_backtest(
    df: pd.DataFrame,
    entry_threshold: float,
    exit_threshold: float,
    cost_bps: int,
) -> pd.DataFrame:
    bt = df.copy()
    bt["signal"] = 0
    bt["position"] = 0
    bt["entry_long"] = 0
    bt["entry_short"] = 0
    bt["exit_trade"] = 0

    current_position = 0

    for i in range(len(bt)):
        z = bt.iloc[i]["z_score"]
        regime = bool(bt.iloc[i]["regime_on"])
        prev_position = current_position
        signal = 0

        if regime:
            if current_position == 0:
                if z > entry_threshold:
                    current_position = -1
                    signal = -1
                elif z < -entry_threshold:
                    current_position = 1
                    signal = 1
            elif current_position == 1:
                if z >= -exit_threshold:
                    current_position = 0
                    signal = 0
            elif current_position == -1:
                if z <= exit_threshold:
                    current_position = 0
                    signal = 0
        else:
            current_position = 0
            signal = 0

        bt.iloc[i, bt.columns.get_loc("signal")] = signal
        bt.iloc[i, bt.columns.get_loc("position")] = current_position

        if prev_position == 0 and current_position == 1:
            bt.iloc[i, bt.columns.get_loc("entry_long")] = 1
        elif prev_position == 0 and current_position == -1:
            bt.iloc[i, bt.columns.get_loc("entry_short")] = 1
        elif prev_position != 0 and current_position == 0:
            bt.iloc[i, bt.columns.get_loc("exit_trade")] = 1

    bt["strategy_return_gross"] = bt["position"].shift(1).fillna(0) * (bt["ret_1"] - bt["ret_2"])
    bt["trade_flag"] = bt["position"].diff().abs().fillna(0)
    bt["transaction_cost"] = bt["trade_flag"] * (cost_bps / 10000)
    bt["strategy_return_net"] = bt["strategy_return_gross"] - bt["transaction_cost"]

    bt["equity_curve"] = (1 + bt["strategy_return_net"].fillna(0)).cumprod()
    bt["cumulative_market_1"] = (1 + bt["ret_1"].fillna(0)).cumprod()
    bt["cumulative_market_2"] = (1 + bt["ret_2"].fillna(0)).cumprod()
    bt["drawdown"] = bt["equity_curve"] / bt["equity_curve"].cummax() - 1

    return bt


def compute_metrics(bt: pd.DataFrame) -> dict:
    returns = bt["strategy_return_net"].dropna()
    equity = bt["equity_curve"]

    if len(returns) < 2 or returns.std() == 0:
        sharpe = 0.0
    else:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

    total_return = equity.iloc[-1] - 1
    max_drawdown = bt["drawdown"].min()
    win_rate = float((returns > 0).mean()) if len(returns) > 0 else 0.0
    num_trades = int((bt["entry_long"] + bt["entry_short"]).sum())
    avg_daily_return = float(returns.mean()) if len(returns) > 0 else 0.0
    regime_active_pct = float(bt["regime_on"].mean()) if "regime_on" in bt.columns else 1.0

    return {
        "Total Return": total_return,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown,
        "Win Rate": win_rate,
        "Trades": num_trades,
        "Average Daily Return": avg_daily_return,
        "Regime Active %": regime_active_pct,
    }


def plot_trade_markers(ax, bt: pd.DataFrame, series_name: str) -> None:
    long_entries = bt[bt["entry_long"] == 1]
    short_entries = bt[bt["entry_short"] == 1]
    exits = bt[bt["exit_trade"] == 1]

    ax.scatter(long_entries.index, long_entries[series_name], marker="^", s=60, label="Long Entry")
    ax.scatter(short_entries.index, short_entries[series_name], marker="v", s=60, label="Short Entry")
    ax.scatter(exits.index, exits[series_name], marker="o", s=40, label="Exit")


try:
    prices_df = load_data(ticker_1, ticker_2, start_date, end_date)
    signal_df = build_signals(
        prices=prices_df,
        rolling_window=window,
        corr_window=correlation_window,
        min_corr=min_correlation,
        vol_lookback=volatility_lookback,
        vol_multiplier=volatility_multiplier,
        use_regime=use_regime_filter,
    )
    backtest_df = run_backtest(
        df=signal_df,
        entry_threshold=entry_z,
        exit_threshold=exit_z,
        cost_bps=transaction_cost_bps,
    )
    metrics = compute_metrics(backtest_df)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Return", f"{metrics['Total Return']:.2%}")
    col2.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
    col3.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
    col4.metric("Win Rate", f"{metrics['Win Rate']:.2%}")
    col5.metric("Trades", f"{metrics['Trades']}")
    col6.metric("Regime Active", f"{metrics['Regime Active %']:.2%}")

    st.subheader("Price Series")
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    norm_1 = prices_df["price_1"] / prices_df["price_1"].iloc[0]
    norm_2 = prices_df["price_2"] / prices_df["price_2"].iloc[0]
    price_plot_df = pd.DataFrame(index=prices_df.index)
    price_plot_df["norm_1"] = norm_1
    price_plot_df["norm_2"] = norm_2
    price_plot_df = price_plot_df.loc[backtest_df.index]

    ax1.plot(price_plot_df.index, price_plot_df["norm_1"], label=ticker_1)
    ax1.plot(price_plot_df.index, price_plot_df["norm_2"], label=ticker_2)
    if show_trade_markers:
        plot_trade_markers(ax1, backtest_df.assign(norm_1=price_plot_df["norm_1"]), "norm_1")
    ax1.set_ylabel("Normalized Price")
    ax1.legend(loc="best")
    st.pyplot(fig1)

    st.subheader("Spread Z-Score")
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    ax2.plot(backtest_df.index, backtest_df["z_score"], label="Z-Score")
    ax2.axhline(entry_z, linestyle="--", label="Short Entry Threshold")
    ax2.axhline(-entry_z, linestyle="--", label="Long Entry Threshold")
    ax2.axhline(exit_z, linestyle=":", label="Short Exit Threshold")
    ax2.axhline(-exit_z, linestyle=":", label="Long Exit Threshold")
    ax2.axhline(0, linestyle="-")

    if show_trade_markers:
        long_entries = backtest_df[backtest_df["entry_long"] == 1]
        short_entries = backtest_df[backtest_df["entry_short"] == 1]
        exits = backtest_df[backtest_df["exit_trade"] == 1]
        ax2.scatter(long_entries.index, long_entries["z_score"], marker="^", s=60, label="Long Entry")
        ax2.scatter(short_entries.index, short_entries["z_score"], marker="v", s=60, label="Short Entry")
        ax2.scatter(exits.index, exits["z_score"], marker="o", s=40, label="Exit")

    ax2.legend(loc="best")
    st.pyplot(fig2)

    st.subheader("Strategy Equity Curve")
    fig3, ax3 = plt.subplots(figsize=(12, 4))
    ax3.plot(backtest_df.index, backtest_df["equity_curve"], label="Strategy")
    ax3.set_ylabel("Portfolio Value")
    ax3.legend(loc="best")
    st.pyplot(fig3)

    st.subheader("Regime Filter State")
    fig4, ax4 = plt.subplots(figsize=(12, 2.5))
    ax4.plot(backtest_df.index, backtest_df["regime_on"].astype(int), label="Regime On")
    ax4.set_ylim(-0.1, 1.1)
    ax4.set_ylabel("On / Off")
    ax4.legend(loc="best")
    st.pyplot(fig4)

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Rolling Correlation")
        fig5, ax5 = plt.subplots(figsize=(12, 3))
        ax5.plot(backtest_df.index, backtest_df["rolling_corr"], label="Rolling Correlation")
        ax5.axhline(min_correlation, linestyle="--", label="Min Correlation")
        ax5.legend(loc="best")
        st.pyplot(fig5)

    with right_col:
        st.subheader("Spread Volatility")
        fig6, ax6 = plt.subplots(figsize=(12, 3))
        ax6.plot(backtest_df.index, backtest_df["spread_vol"], label="Spread Vol")
        ax6.plot(backtest_df.index, backtest_df["spread_vol_baseline"] * volatility_multiplier, linestyle="--", label="Vol Limit")
        ax6.legend(loc="best")
        st.pyplot(fig6)

    with st.expander("View Backtest Data"):
        st.dataframe(backtest_df.tail(150))

except Exception as exc:
    st.error(f"Error: {exc}")
    st.info("Try valid ticker symbols like KO and PEP, or adjust the date range and filter parameters.")