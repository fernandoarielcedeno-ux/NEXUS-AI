import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_trades, get_stats, get_config
from core.engine import generate_market_data, compute_indicators

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"

AX = dict(gridcolor="rgba(0,245,212,0.05)", showgrid=True, zeroline=False,
          color="#3A6A7A", tickfont=dict(family="Space Mono", size=9, color="#3A6A7A"))

@st.cache_data(ttl=60, show_spinner=False)
def get_correlation_data():
    pairs = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT"]
    returns = {}
    for p in pairs:
        df = generate_market_data(p, 120)
        returns[p.split("/")[0]] = df["close"].pct_change().dropna().values[:90]
    return pd.DataFrame(returns).corr()

def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>ANALYTICS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>Performance intelligence & statistical analysis</p>",
                unsafe_allow_html=True)

    stats  = get_stats()
    trades = get_trades(limit=500)

    wins_sum   = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    losses_sum = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    pf = wins_sum / losses_sum if losses_sum > 0 else 0.0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("TOTAL TRADES",   stats["total"])
    c2.metric("WIN RATE",       f"{stats['win_rate']:.1f}%")
    c3.metric("TOTAL P&L",      f"${stats['total_pnl']:+,.2f}")
    c4.metric("BEST TRADE",     f"${stats['best']:+,.2f}")
    c5.metric("WORST TRADE",    f"${stats['worst']:+,.2f}")
    c6.metric("PROFIT FACTOR",  f"{pf:.2f}")

    st.markdown("---")

    if not trades:
        st.info("No trades yet — run the bot to generate data.")
        _show_correlation()
        return

    df = pd.DataFrame(trades)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")
    df["cum_pnl"]     = df["pnl"].cumsum()
    df["balance"]     = float(get_config("initial_balance") or 10000) + df["cum_pnl"]

    tab1, tab2, tab3 = st.tabs(["PERFORMANCE", "TRADE ANALYSIS", "CORRELATION"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["created_at"], y=df["balance"],
            mode="lines", line=dict(color=TEAL,width=2.2),
            fill="tozeroy", fillcolor="rgba(0,245,212,0.05)", name="Equity"))
        peak = df["balance"].cummax()
        fig.add_trace(go.Scatter(x=df["created_at"], y=peak,
            mode="lines", line=dict(color=AZURE,width=1,dash="dot"), name="Peak", opacity=0.5))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=280,
            margin=dict(l=4,r=4,t=36,b=4), font=dict(family="Rajdhani",color="#3A6A7A"),
            title=dict(text="EQUITY CURVE", font=dict(family="Orbitron",color=TEAL,size=12)),
            legend=dict(font=dict(color=AZURE),bgcolor="rgba(0,0,0,0)"),
            xaxis=AX, yaxis=AX)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        col1, col2 = st.columns(2)
        with col1:
            fig_h = go.Figure(go.Histogram(
                x=df["pnl"], nbinsx=25,
                marker=dict(color=[TEAL if v > 0 else RED for v in df["pnl"]],
                            line=dict(width=0.3, color="#050D1A"))))
            fig_h.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=230,
                margin=dict(l=4,r=4,t=36,b=4),
                title=dict(text="P&L DISTRIBUTION", font=dict(family="Orbitron",color=TEAL,size=11)),
                xaxis=AX, yaxis=AX, showlegend=False)
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

        with col2:
            fig_pie = go.Figure(go.Pie(
                labels=["Wins","Losses"], values=[stats["wins"], max(stats["losses"],1)],
                hole=0.62,
                marker=dict(colors=[TEAL,RED], line=dict(color="#050D1A",width=2)),
                textfont=dict(family="Orbitron",size=10),
            ))
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", height=230,
                font=dict(color=AZURE,family="Rajdhani"),
                legend=dict(font=dict(color=AZURE,size=10),bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=10,r=10,t=36,b=10),
                title=dict(text="WIN / LOSS", font=dict(family="Orbitron",color=TEAL,size=11)),
                annotations=[dict(text=f"<b>{stats['win_rate']:.0f}%</b>", x=0.5, y=0.5,
                    font=dict(size=18,color=TEAL,family="Orbitron"), showarrow=False)],
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        fig_sc = go.Figure(go.Scatter(
            x=df["signal_strength"], y=df["pnl"], mode="markers",
            marker=dict(size=8, color=df["pnl"],
                colorscale=[[0,RED],[0.5,GOLD],[1,TEAL]],
                showscale=True, colorbar=dict(title="PnL", tickfont=dict(color=AZURE)),
                line=dict(width=0.4, color="rgba(0,0,0,0.4)")),
            text=df["symbol"],
            hovertemplate="<b>%{text}</b><br>Signal: %{x:.1f}%<br>PnL: $%{y:.2f}<extra></extra>",
        ))
        fig_sc.add_hline(y=0, line_dash="dot", line_color=AZURE, opacity=0.4)
        fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=300,
            margin=dict(l=4,r=4,t=36,b=4),
            title=dict(text="SIGNAL STRENGTH vs P&L", font=dict(family="Orbitron",color=TEAL,size=12)),
            xaxis={**AX, "title":"Signal Confidence (%)"}, yaxis={**AX, "title":"P&L ($)"})
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        pnl_pair = df.groupby("symbol")["pnl"].sum().sort_values()
        fig_bar = go.Figure(go.Bar(
            x=pnl_pair.values, y=pnl_pair.index, orientation="h",
            marker=dict(color=[TEAL if v > 0 else RED for v in pnl_pair.values], line=dict(width=0)),
        ))
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=240,
            margin=dict(l=4,r=4,t=36,b=4),
            title=dict(text="P&L BY PAIR", font=dict(family="Orbitron",color=TEAL,size=12)),
            xaxis=AX, yaxis=AX, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        _show_correlation()


def _show_correlation():
    corr = get_correlation_data()
    fig  = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale=[[0,RED],[0.5,"#050D1A"],[1,TEAL]],
        zmin=-1, zmax=1,
        text=corr.values.round(2), texttemplate="%{text}",
        textfont=dict(family="Space Mono",size=12,color="white"),
        showscale=True, colorbar=dict(tickfont=dict(color=AZURE)),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060E1C", height=340,
        margin=dict(l=4,r=4,t=36,b=4), font=dict(family="Rajdhani",color=AZURE),
        title=dict(text="ASSET CORRELATION MATRIX", font=dict(family="Orbitron",color=TEAL,size=12)),
        xaxis=dict(color=AZURE), yaxis=dict(color=AZURE))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
