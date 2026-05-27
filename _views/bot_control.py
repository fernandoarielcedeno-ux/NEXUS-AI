import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
import json
import random

from core.database import get_config, set_config, log_trade, log_signal, get_trades, update_portfolio, get_portfolio
from core.cache import get_analyzed_pair, get_scanner_data
from core.engine import calculate_position_size, calculate_pnl

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"

def execute_trade(symbol, sig, config):
    balance  = float(get_config("current_balance") or 10000)
    risk     = float(config["risk_per_trade"])
    sl_pct   = float(config["stop_loss_pct"])
    price    = sig["price"]
    portfolio = get_portfolio()
    already  = any(p["symbol"] == symbol for p in portfolio)

    if sig["signal"] == "BUY" and not already and sig["confidence"] > 45:
        qty  = calculate_position_size(balance, price, risk, sl_pct)
        cost = qty * price
        if cost > balance * 0.05:
            set_config("current_balance", balance - cost)
            update_portfolio(symbol, qty, price)
            log_trade(symbol, "BUY", qty, price, pnl=0, strategy=config["strategy"], signal_strength=sig["confidence"])
            log_signal(symbol, "BUY", sig["confidence"], price, sig["scores"])
            return f"BUY {qty:.6f} {symbol} @ ${price:,.4f}  |  Cost: ${cost:,.2f}"

    elif sig["signal"] == "SELL" and already:
        pos  = next(p for p in portfolio if p["symbol"] == symbol)
        pnl  = calculate_pnl(pos["avg_buy_price"], price, pos["quantity"], "BUY")
        set_config("current_balance", balance + pos["quantity"] * price)
        update_portfolio(symbol, 0, 0)
        log_trade(symbol, "SELL", pos["quantity"], price, pnl=pnl, strategy=config["strategy"], signal_strength=sig["confidence"])
        arrow = "+" if pnl >= 0 else ""
        return f"SELL {pos['quantity']:.6f} {symbol} @ ${price:,.4f}  |  PnL: {arrow}${pnl:,.2f}"
    return None

def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>BOT CONTROL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>AI-powered autonomous trading engine</p>",
                unsafe_allow_html=True)

    running = get_config("bot_running") == "true"

    col1, col2, col3 = st.columns([2,2,3])

    with col1:
        bot_c = TEAL if running else RED
        st.markdown(
            f"<div class='card-glass' style='text-align:center;padding:1.5rem;'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.55rem;color:{AZURE};letter-spacing:0.2em;'>BOT STATUS</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:2.4rem;font-weight:900;color:{bot_c};text-shadow:0 0 28px {bot_c};margin:0.3rem 0;'>{'ACTIVE' if running else 'IDLE'}</div>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#3A6A7A;'>{'Auto-executing trades' if running else 'Awaiting activation'}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if running:
            if st.button("STOP BOT"):
                set_config("bot_running", "false")
                st.rerun()
        else:
            if st.button("START BOT"):
                set_config("bot_running", "true")
                st.rerun()

    with col2:
        strats = ["HYBRID_AI","RSI_DIVERGENCE","MACD_MOMENTUM","BB_SQUEEZE","EMA_CROSSOVER","VOLUME_BREAKOUT"]
        cur    = get_config("strategy") or "HYBRID_AI"
        new_s  = st.selectbox("STRATEGY", strats, index=strats.index(cur))
        if new_s != cur:
            set_config("strategy", new_s)
        desc = {
            "HYBRID_AI":       "Multi-indicator AI ensemble",
            "RSI_DIVERGENCE":  "RSI divergence detection",
            "MACD_MOMENTUM":   "MACD crossover + momentum",
            "BB_SQUEEZE":      "Bollinger Band squeeze",
            "EMA_CROSSOVER":   "Golden / death cross",
            "VOLUME_BREAKOUT": "Volume surge breakout",
        }
        st.markdown(
            f"<div class='card-glass' style='padding:0.8rem;margin-top:0.5rem;'>"
            f"<div style='font-family:Rajdhani,sans-serif;font-size:0.88rem;color:#E0FAFF;'>{desc.get(new_s,'')}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col3:
        risk = st.slider("Risk per Trade (%)", 0.5, 5.0, float(get_config("risk_per_trade") or 0.02)*100, 0.25)
        set_config("risk_per_trade", risk/100)
        sl   = st.slider("Stop Loss (%)",      1.0, 10.0, float(get_config("stop_loss_pct") or 0.03)*100,  0.5)
        set_config("stop_loss_pct", sl/100)
        tp   = st.slider("Take Profit (%)",    2.0, 20.0, float(get_config("take_profit_pct") or 0.06)*100, 0.5)
        set_config("take_profit_pct", tp/100)

    st.markdown("---")
    st.markdown("<h3>LIVE SIGNAL SCANNER</h3>", unsafe_allow_html=True)

    pairs_str = get_config("selected_pairs") or '["BTC/USDT","ETH/USDT","SOL/USDT"]'
    try:    default_pairs = json.loads(pairs_str)
    except: default_pairs = ["BTC/USDT","ETH/USDT","SOL/USDT"]

    all_pairs     = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT"]
    selected_pairs = st.multiselect("TRADING PAIRS", all_pairs, default=default_pairs)
    set_config("selected_pairs", json.dumps(selected_pairs))

    if st.button("SCAN & EXECUTE"):
        cfg = {"risk_per_trade": get_config("risk_per_trade"), "stop_loss_pct": get_config("stop_loss_pct"),
               "take_profit_pct": get_config("take_profit_pct"), "strategy": get_config("strategy")}
        results = []
        for pair in selected_pairs:
            df, sig = get_analyzed_pair(pair, 200)
            action  = execute_trade(pair, sig, cfg) if running else None
            results.append((pair, sig, action))

        for pair, sig, action in results:
            sig_c = TEAL if sig["signal"] == "BUY" else (RED if sig["signal"] == "SELL" else GOLD)
            act_html = (
                f"<span style='font-family:Rajdhani,sans-serif;font-size:0.85rem;color:{TEAL};'>{action}</span>"
                if action else
                f"<span style='font-family:Space Mono,monospace;font-size:0.65rem;color:#3A6A7A;'>{'Bot active' if running else 'Bot idle'}</span>"
            )
            st.markdown(
                f"<div class='card-glass' style='display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;padding:0.9rem 1.1rem;'>"
                f"<div style='font-family:Orbitron,monospace;font-size:0.85rem;color:#E0FAFF;min-width:110px;'>{pair}</div>"
                f"<div style='text-align:center;'><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;letter-spacing:0.1em;'>SIGNAL</div>"
                f"<div style='font-family:Orbitron,monospace;font-size:0.95rem;font-weight:700;color:{sig_c};text-shadow:0 0 10px {sig_c};'>{sig['signal']}</div></div>"
                f"<div style='text-align:center;'><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;'>CONFIDENCE</div>"
                f"<div style='font-family:Space Mono,monospace;font-size:0.85rem;color:{TEAL};'>{sig['confidence']:.1f}%</div></div>"
                f"<div style='text-align:center;'><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;'>PRICE</div>"
                f"<div style='font-family:Space Mono,monospace;font-size:0.85rem;color:#E0FAFF;'>${sig['price']:,.4f}</div></div>"
                f"<div style='text-align:right;min-width:180px;'>{act_html}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("<h3>TRADE HISTORY</h3>", unsafe_allow_html=True)
    trades = get_trades(limit=20)
    if trades:
        df_t = pd.DataFrame(trades)
        df_t["P&L"]   = df_t["pnl"].apply(lambda x: f"${x:+,.2f}")
        df_t["PRICE"]  = df_t["price"].apply(lambda x: f"${x:,.4f}")
        st.dataframe(
            df_t[["created_at","symbol","side","quantity","PRICE","P&L","strategy","signal_strength"]]
            .rename(columns={"created_at":"TIME","symbol":"PAIR","side":"SIDE","quantity":"QTY",
                             "strategy":"STRATEGY","signal_strength":"SIGNAL%"}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No trades yet. Start the bot or run a scan.")
