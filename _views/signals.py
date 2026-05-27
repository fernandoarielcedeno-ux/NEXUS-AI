import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_signals
from core.cache import get_analyzed_pair, get_scanner_data
from core.engine import ai_price_prediction

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"
PAIRS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT"]

def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>SIGNAL CENTER</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>Real-time AI signal generation & prediction</p>",
                unsafe_allow_html=True)

    if st.button("REFRESH SIGNALS"):
        get_scanner_data.clear()
        get_analyzed_pair.clear()
        st.rerun()

    scan = get_scanner_data()
    st.markdown("<h3>LIVE SIGNALS</h3>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (pair, price, chg, rsi, sig_s, conf, sc) in enumerate(scan):
        sig_c = TEAL if sig_s == "BUY" else (RED if sig_s == "SELL" else GOLD)
        chg_c = TEAL if chg >= 0 else RED
        with cols[i % 4]:
            st.markdown(
                f"<div class='card-glass' style='text-align:center;padding:1rem 0.7rem;'>"
                f"<div style='font-family:Orbitron,monospace;font-size:0.65rem;color:#E0FAFF;margin-bottom:0.3rem;'>{pair}</div>"
                f"<div style='font-family:Orbitron,monospace;font-size:1.5rem;font-weight:900;color:{sig_c};text-shadow:0 0 16px {sig_c};line-height:1;'>{sig_s}</div>"
                f"<div style='font-family:Space Mono,monospace;font-size:0.7rem;color:{TEAL};margin-top:0.3rem;'>{conf:.1f}% conf</div>"
                f"<div style='font-family:Space Mono,monospace;font-size:0.68rem;color:#A0D4E8;'>${price:,.4f}</div>"
                f"<div style='font-family:Space Mono,monospace;font-size:0.65rem;color:{chg_c};'>{chg:+.2f}%</div>"
                f"<div style='background:rgba(255,255,255,0.06);border-radius:3px;height:3px;margin-top:0.5rem;'>"
                f"<div style='width:{conf}%;height:100%;background:{sig_c};border-radius:3px;'></div></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("<h3>DEEP ANALYSIS</h3>", unsafe_allow_html=True)
    selected = st.selectbox("SELECT PAIR", PAIRS, key="sig_pair")

    df, sig = get_analyzed_pair(selected, 300)
    pred    = ai_price_prediction(df)

    col_a, col_b = st.columns([2,1])

    with col_a:
        ax = dict(gridcolor="rgba(0,245,212,0.05)", showgrid=True, zeroline=False,
                  color="#3A6A7A", tickfont=dict(family="Space Mono",size=9))

        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index[-100:], y=df["rsi"].iloc[-100:],
            mode="lines", line=dict(color=TEAL,width=1.8),
            fill="tozeroy", fillcolor="rgba(0,245,212,0.05)"))
        fig_rsi.add_hline(y=70, line_dash="dot", line_color="rgba(255,77,109,0.5)", line_width=1)
        fig_rsi.add_hline(y=30, line_dash="dot", line_color="rgba(0,245,212,0.5)",  line_width=1)
        fig_rsi.add_hrect(y0=70,y1=100,fillcolor="rgba(255,77,109,0.05)",line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="rgba(0,245,212,0.05)", line_width=0)
        fig_rsi.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=180,
            margin=dict(l=4,r=4,t=28,b=4), showlegend=False,
            title=dict(text="RSI (14)", font=dict(family="Orbitron",color=TEAL,size=11)),
            xaxis=ax, yaxis={**ax, "range":[0,100]})
        st.plotly_chart(fig_rsi, use_container_width=True, config={"displayModeBar": False})

        hist = df["macd_hist"].iloc[-100:]
        mc   = [TEAL if v >= 0 else RED for v in hist]
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Bar(x=df.index[-100:], y=hist, marker_color=mc, marker_line_width=0, opacity=0.75))
        fig_macd.add_trace(go.Scatter(x=df.index[-100:], y=df["macd"].iloc[-100:],
            line=dict(color=TEAL,width=1.4)))
        fig_macd.add_trace(go.Scatter(x=df.index[-100:], y=df["macd_signal"].iloc[-100:],
            line=dict(color=GOLD,width=1.4)))
        fig_macd.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=180,
            margin=dict(l=4,r=4,t=28,b=4), showlegend=False,
            title=dict(text="MACD (12/26/9)", font=dict(family="Orbitron",color=TEAL,size=11)),
            xaxis=ax, yaxis=ax)
        st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        pred_c = TEAL if pred["predicted_change_pct"] > 0 else RED
        dir_arrow = "▲" if pred["predicted_change_pct"] > 0 else "▼"
        st.markdown(
            f"<div class='card-glass'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.15em;margin-bottom:0.7rem;'>AI PRICE PREDICTION</div>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.68rem;color:#3A6A7A;'>Current</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1rem;color:{TEAL};font-weight:700;'>${pred['current_price']:,.4f}</div>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.68rem;color:#3A6A7A;margin-top:0.5rem;'>Forecast (5 candles)</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1rem;color:{pred_c};font-weight:700;'>${pred['predicted_price']:,.4f}</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1.4rem;font-weight:900;color:{pred_c};text-shadow:0 0 12px {pred_c};'>{dir_arrow} {pred['predicted_change_pct']:+.2f}%</div>"
            f"<div style='font-family:Rajdhani,sans-serif;font-size:0.85rem;color:#E0FAFF;'>{pred['direction']}</div>"
            f"<hr style='border-color:rgba(0,245,212,0.1);margin:0.7rem 0;'>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.62rem;color:#3A6A7A;'>68% CI: ±${pred['confidence_68']:,.4f}<br>95% CI: ±${pred['confidence_95']:,.4f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        rows_m = ""
        for model, sc_v in pred["model_scores"].items():
            clr  = TEAL if sc_v > 0 else RED
            pct  = min(abs(sc_v) / 5 * 100, 100)
            rows_m += (
                f"<div style='margin-bottom:0.45rem;'>"
                f"<div style='display:flex;justify-content:space-between;font-family:Space Mono,monospace;font-size:0.6rem;color:#3A6A7A;'>"
                f"<span>{model.replace('_',' ')}</span><span style='color:{clr};'>{sc_v:+.1f}</span></div>"
                f"<div style='background:rgba(255,255,255,0.05);border-radius:3px;height:3px;margin-top:2px;'>"
                f"<div style='width:{pct}%;height:100%;background:{clr};border-radius:3px;'></div></div>"
                f"</div>"
            )
        st.markdown(
            f"<div class='card-glass'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:{AZURE};letter-spacing:0.1em;margin-bottom:0.6rem;'>MODEL ENSEMBLE</div>"
            f"{rows_m}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("<h3>SIGNAL HISTORY</h3>", unsafe_allow_html=True)
    import pandas as pd
    sigs = get_signals(limit=30)
    if sigs:
        st.dataframe(pd.DataFrame(sigs)[["created_at","symbol","signal","confidence","price"]]
            .rename(columns={"created_at":"TIME","symbol":"PAIR","signal":"SIGNAL",
                             "confidence":"CONF%","price":"PRICE"}),
            use_container_width=True, hide_index=True)
    else:
        st.info("No historical signals yet.")
