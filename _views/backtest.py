import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.cache import cached_backtest

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"
AX    = dict(gridcolor="rgba(0,245,212,0.05)", showgrid=True, zeroline=False,
             color="#3A6A7A", tickfont=dict(family="Space Mono",size=9,color="#3A6A7A"))

@st.cache_data(ttl=300, show_spinner=False)
def cached_backtest(symbol, initial_balance, periods):
    return run_backtest(symbol, initial_balance=initial_balance, periods=periods)

def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>BACKTEST ENGINE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>Historical strategy simulation</p>",
                unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        symbol          = st.selectbox("PAIR", ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT"])
        initial_balance = st.number_input("INITIAL BALANCE ($)", 1000, 1_000_000, 10000, 500)
        periods         = st.slider("CANDLES (15m)", 100, 1000, 300, 50)
        run_btn         = st.button("RUN BACKTEST")

    with col2:
        if run_btn:
            with st.spinner("Simulating..."):
                r = cached_backtest(symbol, initial_balance, periods)

            ret = r["total_return_pct"]
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("FINAL BALANCE", f"${r['final_balance']:,.2f}", f"{ret:+.1f}%")
            c2.metric("TOTAL TRADES",  r["total_trades"])
            c3.metric("WIN RATE",      f"{r['win_rate']:.1f}%")
            c4.metric("SHARPE RATIO",  f"{r['sharpe_ratio']:.2f}")
            c5.metric("MAX DRAWDOWN",  f"{r['max_drawdown_pct']:.1f}%")

            x   = list(range(len(r["equity_curve"])))
            arr = np.array(r["equity_curve"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=r["equity_curve"], mode="lines",
                line=dict(color=TEAL,width=2.2), fill="tozeroy", fillcolor="rgba(0,245,212,0.06)", name="Equity"))
            peak = np.maximum.accumulate(arr)
            fig.add_trace(go.Scatter(x=x, y=peak, mode="lines",
                line=dict(color=AZURE,width=1,dash="dot"), name="Peak", opacity=0.5))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=300,
                margin=dict(l=4,r=4,t=36,b=4), font=dict(family="Rajdhani",color="#3A6A7A"),
                title=dict(text=f"{symbol} · EQUITY CURVE", font=dict(family="Orbitron",color=TEAL,size=12)),
                legend=dict(font=dict(color=AZURE),bgcolor="rgba(0,0,0,0)"), xaxis=AX, yaxis=AX)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            dd = (arr - peak) / peak * 100
            fig_dd = go.Figure(go.Scatter(x=x, y=dd, mode="lines",
                line=dict(color=RED,width=1.5), fill="tozeroy", fillcolor="rgba(255,77,109,0.1)"))
            fig_dd.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=140,
                margin=dict(l=4,r=4,t=28,b=4), showlegend=False,
                title=dict(text="DRAWDOWN (%)", font=dict(family="Orbitron",color=RED,size=11)),
                xaxis=AX, yaxis=AX)
            st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})

            if r["trades"]:
                wins   = [t for t in r["trades"] if t["pnl"] > 0]
                losses = [t for t in r["trades"] if t["pnl"] <= 0]
                aw = np.mean([t["pnl"] for t in wins])   if wins   else 0
                al = np.mean([t["pnl"] for t in losses]) if losses else 0
                rr = abs(aw / al) if al != 0 else 0
                st.markdown(
                    f"<div class='card-glass' style='display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;'>"
                    f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>AVG WIN</div>"
                    f"<div style='font-family:Space Mono,monospace;color:{TEAL};font-size:0.88rem;'>${aw:+,.2f}</div></div>"
                    f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>AVG LOSS</div>"
                    f"<div style='font-family:Space Mono,monospace;color:{RED};font-size:0.88rem;'>${al:+,.2f}</div></div>"
                    f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>RISK/REWARD</div>"
                    f"<div style='font-family:Space Mono,monospace;color:{GOLD};font-size:0.88rem;'>{rr:.2f}</div></div>"
                    f"<div style='text-align:center;'><div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;'>NET P&L</div>"
                    f"<div style='font-family:Space Mono,monospace;color:{'#00F5D4' if r['total_pnl']>0 else RED};font-size:0.88rem;'>${r['total_pnl']:+,.2f}</div></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("<h3>TRADE LOG</h3>", unsafe_allow_html=True)
                df_t = pd.DataFrame(r["trades"])
                df_t["P&L"]   = df_t["pnl"].apply(lambda x: f"${x:+,.2f}")
                df_t["ENTRY"] = df_t["entry"].apply(lambda x: f"${x:,.4f}")
                df_t["EXIT"]  = df_t["price"].apply(lambda x: f"${x:,.4f}")
                df_t["DATE"]  = df_t["date"].astype(str).str[:19]
                st.dataframe(df_t[["DATE","ENTRY","EXIT","P&L","reason"]]
                    .rename(columns={"reason":"REASON"}),
                    use_container_width=True, hide_index=True)
        else:
            st.markdown(
                f"<div class='card-glass' style='text-align:center;padding:3rem;opacity:0.55;'>"
                f"<div style='font-family:Orbitron,monospace;font-size:0.75rem;color:{AZURE};letter-spacing:0.2em;'>CONFIGURE & RUN BACKTEST</div>"
                f"<div style='font-family:Rajdhani,sans-serif;font-size:0.85rem;color:#3A6A7A;margin-top:0.4rem;'>Multi-strategy AI simulation on historical data</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
