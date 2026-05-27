import streamlit as st
from core.engine import (
    generate_market_data as _gen,
    compute_indicators,
    score_signal,
    ai_price_prediction,
    run_backtest as _backtest,
)

@st.cache_data(ttl=30, show_spinner=False)
def generate_market_data(symbol, periods=300, interval_minutes=15):
    return _gen(symbol, periods, interval_minutes)

@st.cache_data(ttl=30, show_spinner=False)
def get_analyzed_pair(symbol, periods=300):
    df = compute_indicators(_gen(symbol, periods))
    sig = score_signal(df)
    return df, sig

@st.cache_data(ttl=60, show_spinner=False)
def get_scanner_data():
    pairs = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT"]
    results = []
    for p in pairs:
        df = compute_indicators(_gen(p, 120))
        s  = score_signal(df)
        pr = s["price"]
        ch = (pr - df["close"].iloc[-25]) / df["close"].iloc[-25] * 100
        results.append((p, pr, ch, s["rsi"], s["signal"], s["confidence"], s["composite_score"]))
    return results

@st.cache_data(ttl=300, show_spinner=False)
def cached_backtest(symbol, initial_balance, periods):
    return _backtest(symbol, initial_balance=initial_balance, periods=periods)
