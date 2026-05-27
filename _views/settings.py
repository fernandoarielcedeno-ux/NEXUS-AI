import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st

from core.database import get_config, set_config, init_db, get_conn
from core.cache import get_analyzed_pair, get_scanner_data

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"

def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>SETTINGS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>System configuration & account management</p>",
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["ACCOUNT", "BOT CONFIG", "DATABASE"])

    with tab1:
        current = float(get_config("current_balance") or 10000)
        initial = float(get_config("initial_balance") or 10000)
        col1, col2 = st.columns(2)
        with col1:
            new_init = st.number_input("Initial Balance ($)", 100.0, 10_000_000.0, initial, 100.0)
            if st.button("SET BALANCE"):
                set_config("initial_balance", new_init)
                set_config("current_balance", new_init)
                get_analyzed_pair.clear()
                get_scanner_data.clear()
                st.success(f"Balance reset to ${new_init:,.2f}")
                st.rerun()
        with col2:
            pnl_pct = (current / initial - 1) * 100
            pnl_c   = TEAL if current >= initial else RED
            st.markdown(
                f"<div class='card-glass'>"
                f"<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>CURRENT BALANCE</div>"
                f"<div style='font-family:Orbitron,monospace;font-size:1.4rem;color:{TEAL};font-weight:700;'>${current:,.2f}</div>"
                f"<div style='font-family:Space Mono,monospace;font-size:0.7rem;color:{pnl_c};'>{pnl_pct:+.2f}% from initial</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            risk     = float(get_config("risk_per_trade") or 0.02)
            new_risk = st.slider("Risk per Trade (%)", 0.1, 10.0, risk*100, 0.1) / 100
            set_config("risk_per_trade", new_risk)
            max_t    = int(get_config("max_open_trades") or 5)
            new_max  = st.slider("Max Concurrent Trades", 1, 20, max_t)
            set_config("max_open_trades", new_max)
        with col2:
            sl       = float(get_config("stop_loss_pct") or 0.03)
            new_sl   = st.slider("Stop Loss (%)", 0.5, 15.0, sl*100, 0.25) / 100
            set_config("stop_loss_pct", new_sl)
            tp       = float(get_config("take_profit_pct") or 0.06)
            new_tp   = st.slider("Take Profit (%)", 1.0, 30.0, tp*100, 0.25) / 100
            set_config("take_profit_pct", new_tp)
        strats   = ["HYBRID_AI","RSI_DIVERGENCE","MACD_MOMENTUM","BB_SQUEEZE","EMA_CROSSOVER","VOLUME_BREAKOUT"]
        cur_s    = get_config("strategy") or "HYBRID_AI"
        new_s    = st.selectbox("DEFAULT STRATEGY", strats, index=strats.index(cur_s))
        set_config("strategy", new_s)
        st.markdown(
            f"<div class='card-glass' style='margin-top:0.8rem;'>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.72rem;color:#E0FAFF;'>"
            f"Risk/Trade: <span style='color:{TEAL};'>{new_risk*100:.2f}%</span>  ·  "
            f"SL: <span style='color:{RED};'>{new_sl*100:.2f}%</span>  ·  "
            f"TP: <span style='color:{TEAL};'>{new_tp*100:.2f}%</span>  ·  "
            f"R/R: <span style='color:{GOLD};'>{new_tp/new_sl:.1f}x</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    with tab3:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("REINIT DB"):
                init_db()
                st.success("Reinitialized.")
        with col2:
            if st.button("CLEAR TRADES"):
                conn = get_conn()
                conn.execute("DELETE FROM trades")
                conn.commit(); conn.close()
                st.success("Trades cleared.")
        with col3:
            if st.button("CLEAR CACHE"):
                get_analyzed_pair.clear()
                get_scanner_data.clear()
                st.success("Cache cleared.")

        conn = get_conn()
        tc = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        sc = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        bc = conn.execute("SELECT COUNT(*) FROM balance_history").fetchone()[0]
        conn.close()

        st.markdown(
            f"<div class='card-glass' style='display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:0.8rem;'>"
            f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>TRADES</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1.4rem;color:{TEAL};font-weight:700;'>{tc}</div></div>"
            f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>SIGNALS</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1.4rem;color:{TEAL};font-weight:700;'>{sc}</div></div>"
            f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>BALANCE RECORDS</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1.4rem;color:{TEAL};font-weight:700;'>{bc}</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='card-glass' style='margin-top:0.8rem;'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.15em;margin-bottom:0.5rem;'>SYSTEM INFO</div>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.68rem;color:#A0D4E8;line-height:1.7;'>"
            f"Engine: NEXUS AI v3.0<br>"
            f"Strategies: Hybrid AI Ensemble (8 indicators)<br>"
            f"Cache TTL: Market data 30s · Scanner 60s · Backtest 300s<br>"
            f"Database: SQLite3  ·  UI: Streamlit + Plotly"
            f"</div></div>",
            unsafe_allow_html=True,
        )
