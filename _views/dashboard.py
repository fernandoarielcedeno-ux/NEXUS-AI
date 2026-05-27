import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.database import get_config, get_balance_history, get_stats
from core.cache import get_analyzed_pair, get_scanner_data

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"

@st.cache_data(ttl=60, show_spinner=False)
def build_chart(symbol, n=150):
    df, sig = get_analyzed_pair(symbol, 300)
    df = df.iloc[-n:]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        row_heights=[0.55,0.15,0.15,0.15], vertical_spacing=0.018)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        increasing=dict(line=dict(color=TEAL,width=1), fillcolor="rgba(0,245,212,0.75)"),
        decreasing=dict(line=dict(color=RED, width=1), fillcolor="rgba(255,77,109,0.75)"),
        name="OHLC", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"],
        line=dict(color="rgba(0,180,216,0.28)",width=1), showlegend=False, hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"],
        line=dict(color="rgba(0,180,216,0.28)",width=1), fill="tonexty",
        fillcolor="rgba(0,180,216,0.04)", showlegend=False, hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["ema21"],
        line=dict(color=TEAL,width=1.3,dash="dot"), name="EMA21", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["ema50"],
        line=dict(color=GOLD,width=1.3,dash="dot"), name="EMA50", showlegend=False), row=1, col=1)
    vol_c = [TEAL if df["close"].iloc[i] >= df["open"].iloc[i] else RED for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], marker_color=vol_c,
        marker_line_width=0, opacity=0.65, showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"],
        line=dict(color=TEAL,width=1.5), showlegend=False), row=3, col=1)
    fig.add_hrect(y0=70,y1=100,row=3,col=1,fillcolor="rgba(255,77,109,0.06)",line_width=0)
    fig.add_hrect(y0=0, y1=30, row=3,col=1,fillcolor="rgba(0,245,212,0.06)", line_width=0)
    fig.add_hline(y=70,row=3,col=1,line_dash="dot",line_color="rgba(255,77,109,0.4)",line_width=1)
    fig.add_hline(y=30,row=3,col=1,line_dash="dot",line_color="rgba(0,245,212,0.4)", line_width=1)
    hist = df["macd_hist"]
    mc   = [TEAL if v >= 0 else RED for v in hist]
    fig.add_trace(go.Bar(x=df.index, y=hist, marker_color=mc,
        marker_line_width=0, opacity=0.7, showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"],
        line=dict(color=TEAL,width=1.2), showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"],
        line=dict(color=GOLD,width=1.2), showlegend=False), row=4, col=1)
    ax = dict(gridcolor="rgba(0,245,212,0.05)", showgrid=True, zeroline=False,
              color="#3A6A7A", tickfont=dict(family="Space Mono",size=9,color="#3A6A7A"), showline=False)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=560,
        margin=dict(l=4,r=4,t=36,b=4), font=dict(family="Rajdhani",color="#3A6A7A"),
        title=dict(text=f"  {symbol}  ·  15m  ·  NEXUS AI",
                   font=dict(family="Orbitron",color=TEAL,size=13), x=0.0),
        xaxis_rangeslider_visible=False, dragmode="pan",
        hoverlabel=dict(bgcolor="#081426", bordercolor=TEAL,
                        font=dict(family="Space Mono",size=11,color=TEAL)),
    )
    for i in range(1,5):
        fig.update_xaxes(ax, row=i, col=1, showticklabels=(i==4))
        fig.update_yaxes(ax, row=i, col=1)
    fig.update_yaxes(range=[0,100], row=3, col=1)
    return fig, sig


def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>DASHBOARD</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>Real-time market intelligence</p>",
                unsafe_allow_html=True)

    balance = float(get_config("current_balance") or 10000)
    init_b  = float(get_config("initial_balance") or 10000)
    stats   = get_stats()
    pnl     = balance - init_b
    pnl_pct = pnl / init_b * 100
    running = get_config("bot_running") == "true"

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("BALANCE",    f"${balance:,.2f}",            f"${pnl:+,.2f}")
    c2.metric("RETURN",     f"{pnl_pct:+.2f}%",            f"{stats['total']} trades")
    c3.metric("WIN RATE",   f"{stats['win_rate']:.1f}%",    f"{stats['wins']}W / {stats['losses']}L")
    c4.metric("TOTAL P&L",  f"${stats['total_pnl']:+,.2f}", f"Best ${stats['best']:+.2f}")
    c5.metric("BOT",        "ACTIVE" if running else "IDLE", "Auto" if running else "Manual")

    st.markdown("---")

    col_chart, col_panel = st.columns([3, 1])

    with col_chart:
        pairs    = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT"]
        selected = st.selectbox("", pairs, key="dash_pair", label_visibility="collapsed")
        fig, sig = build_chart(selected)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_panel:
        sig_color = TEAL if sig["signal"] == "BUY" else (RED if sig["signal"] == "SELL" else GOLD)
        score     = sig["composite_score"]
        sc_color  = TEAL if score > 0 else RED

        st.markdown(
            f"<div class='card-glass' style='text-align:center;padding:1.1rem 0.8rem 0.9rem;'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:#00B4D8;letter-spacing:0.2em;margin-bottom:0.3rem;'>AI SIGNAL</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:2.4rem;font-weight:900;color:{sig_color};text-shadow:0 0 22px {sig_color};line-height:1;'>{sig['signal']}</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1.05rem;color:{TEAL};font-weight:700;margin-top:0.4rem;'>{sig['confidence']:.1f}%</div>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#3A6A7A;'>confidence</div>"
            f"<div style='background:rgba(255,255,255,0.06);border-radius:4px;height:4px;margin-top:0.7rem;'>"
            f"<div style='width:{sig['confidence']}%;height:100%;background:{sig_color};border-radius:4px;'></div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        indics = [
            ("PRICE",  f"${sig['price']:,.2f}",       TEAL),
            ("RSI",    f"{sig['rsi']:.1f}",            TEAL if sig["rsi"] < 50 else RED),
            ("MACD",   f"{sig['macd']:.4f}",           TEAL if sig["macd"] > 0 else RED),
            ("BB POS", f"{sig['bb_pos']:.1f}%",        AZURE),
            ("VOL",    f"{sig['volume_ratio']:.2f}x",  GOLD),
            ("ATR",    f"{sig['atr']:.2f}",            "#A0D4E8"),
            ("EMA 21", f"${sig['ema21']:,.2f}",        AZURE),
            ("EMA 50", f"${sig['ema50']:,.2f}",        GOLD),
            ("SCORE",  f"{score:+.1f}",                sc_color),
        ]
        rows_html = ""
        for label, value, color in indics:
            rows_html += (
                f"<tr style='border-bottom:1px solid rgba(0,245,212,0.06);'>"
                f"<td style='font-family:Orbitron,monospace;font-size:0.56rem;color:#3A6A7A;letter-spacing:0.06em;padding:0.38rem 0;'>{label}</td>"
                f"<td style='font-family:Space Mono,monospace;font-size:0.72rem;text-align:right;color:{color};font-weight:700;padding:0.38rem 0;'>{value}</td>"
                f"</tr>"
            )
        st.markdown(
            "<div class='card-glass' style='padding:1rem 0.9rem;'>"
            "<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:#00B4D8;letter-spacing:0.15em;margin-bottom:0.6rem;'>LIVE INDICATORS</div>"
            f"<table style='width:100%;border-collapse:collapse;'>{rows_html}</table></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='card-glass' style='text-align:center;padding:0.8rem;'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.52rem;color:#00B4D8;letter-spacing:0.15em;'>COMPOSITE SCORE</div>"
            f"<div style='font-family:Orbitron,monospace;font-size:1.6rem;font-weight:900;color:{sc_color};text-shadow:0 0 14px {sc_color};margin:0.3rem 0;'>{score:+.1f}</div>"
            f"<div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#3A6A7A;'>-100 bearish · +100 bullish</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("<h3>MARKET SCANNER</h3>", unsafe_allow_html=True)

    scan = get_scanner_data()
    cols_hdr = ["PAIR","PRICE","CHANGE","RSI","SIGNAL","CONF%","SCORE"]
    th = "".join(
        f"<th style='font-family:Orbitron,monospace;font-size:0.57rem;color:{AZURE};"
        f"letter-spacing:0.09em;padding:0.5rem 1rem;border-bottom:1px solid rgba(0,245,212,0.1);'>{c}</th>"
        for c in cols_hdr
    )
    tbody = ""
    for pair, price, chg, rsi, sig_s, conf, sc in scan:
        sig_c = TEAL if sig_s == "BUY" else (RED if sig_s == "SELL" else GOLD)
        chg_c = TEAL if chg >= 0 else RED
        sc_c  = TEAL if sc >= 0 else RED
        tbody += (
            f"<tr style='border-bottom:1px solid rgba(0,245,212,0.04);'>"
            f"<td style='font-family:Orbitron,monospace;font-size:0.65rem;color:#E0FAFF;padding:0.42rem 1rem;'>{pair}</td>"
            f"<td style='font-family:Space Mono,monospace;font-size:0.68rem;color:{TEAL};padding:0.42rem 1rem;'>${price:,.4f}</td>"
            f"<td style='font-family:Space Mono,monospace;font-size:0.68rem;color:{chg_c};padding:0.42rem 1rem;'>{chg:+.2f}%</td>"
            f"<td style='font-family:Space Mono,monospace;font-size:0.68rem;color:#A0D4E8;padding:0.42rem 1rem;'>{rsi:.1f}</td>"
            f"<td style='font-family:Orbitron,monospace;font-size:0.68rem;color:{sig_c};font-weight:700;padding:0.42rem 1rem;text-shadow:0 0 8px {sig_c};'>{sig_s}</td>"
            f"<td style='font-family:Space Mono,monospace;font-size:0.68rem;color:{TEAL};padding:0.42rem 1rem;'>{conf:.1f}%</td>"
            f"<td style='font-family:Space Mono,monospace;font-size:0.68rem;color:{sc_c};padding:0.42rem 1rem;'>{sc:+.1f}</td>"
            f"</tr>"
        )
    st.markdown(
        f"<div class='card-glass' style='overflow-x:auto;padding:0;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{th}</tr></thead><tbody>{tbody}</tbody></table></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<h3 style='margin-top:1.4rem;'>EQUITY CURVE</h3>", unsafe_allow_html=True)
    hist_data = get_balance_history(limit=100)
    if len(hist_data) < 5:
        import random, numpy as np
        b = float(get_config("initial_balance") or 10000)
        curve = [b]
        for _ in range(80):
            b += random.gauss(18, 90)
            curve.append(max(b, 1000))
        xs, ys = list(range(len(curve))), curve
    else:
        xs = [h["recorded_at"] for h in reversed(hist_data)]
        ys = [h["total_balance"] for h in reversed(hist_data)]

    fig_eq = go.Figure(go.Scatter(x=xs, y=ys, mode="lines",
        line=dict(color=TEAL, width=2), fill="tozeroy", fillcolor="rgba(0,245,212,0.05)"))
    fig_eq.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=150,
        margin=dict(l=4,r=4,t=6,b=4), showlegend=False,
        xaxis=dict(gridcolor="rgba(0,245,212,0.05)",color="#3A6A7A",showgrid=True,zeroline=False,
                   tickfont=dict(family="Space Mono",size=9)),
        yaxis=dict(gridcolor="rgba(0,245,212,0.05)",color="#3A6A7A",showgrid=True,zeroline=False,
                   tickfont=dict(family="Space Mono",size=9)),
    )
    st.plotly_chart(fig_eq, use_container_width=True, config={"displayModeBar": False})
