import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.database import get_portfolio, get_config, get_trades, get_stats
from core.cache import get_analyzed_pair

TEAL  = "#00F5D4"
AZURE = "#00B4D8"
RED   = "#FF4D6D"
GOLD  = "#FFB703"

@st.cache_data(ttl=30, show_spinner=False)
def enrich_positions(positions_json):
    import json
    positions = json.loads(positions_json)
    enriched, total_val = [], 0
    for p in positions:
        _, sig = get_analyzed_pair(p["symbol"], 80)
        live  = sig["price"]
        val   = p["quantity"] * live
        upnl  = (live - p["avg_buy_price"]) * p["quantity"]
        pct   = (live / p["avg_buy_price"] - 1) * 100
        total_val += val
        enriched.append({**p, "live_price": live, "value": val, "unrealized_pnl": upnl, "pnl_pct": pct})
    return enriched, total_val

def show():
    st.markdown("<h1 style='margin-bottom:0.1rem;'>PORTFOLIO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00B4D8;font-family:Space Mono,monospace;font-size:0.7rem;"
                "letter-spacing:0.1em;margin-bottom:1rem;'>Holdings & position management</p>",
                unsafe_allow_html=True)

    balance   = float(get_config("current_balance") or 10000)
    init_b    = float(get_config("initial_balance") or 10000)
    stats     = get_stats()
    raw_pos   = get_portfolio()

    import json
    pos_key   = json.dumps(raw_pos, sort_keys=True, default=str)
    positions, total_pos_val = enrich_positions(pos_key)
    total     = balance + total_pos_val

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("TOTAL PORTFOLIO", f"${total:,.2f}",          f"{(total/init_b-1)*100:+.2f}%")
    c2.metric("CASH BALANCE",    f"${balance:,.2f}",         f"{balance/total*100:.1f}% allocation")
    c3.metric("POSITIONS VALUE", f"${total_pos_val:,.2f}",   f"{len(positions)} open")
    c4.metric("REALIZED P&L",    f"${stats['total_pnl']:+,.2f}", f"WR {stats['win_rate']:.1f}%")

    st.markdown("---")

    if positions:
        col_l, col_r = st.columns([2,1])
        with col_l:
            st.markdown("<h3>OPEN POSITIONS</h3>", unsafe_allow_html=True)
            for pos in positions:
                pnl_c = TEAL if pos["unrealized_pnl"] >= 0 else RED
                st.markdown(
                    f"<div class='card-glass' style='display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr 1.3fr;gap:0.8rem;align-items:center;padding:0.9rem 1.1rem;'>"
                    f"<div><div style='font-family:Orbitron,monospace;font-size:0.75rem;color:#E0FAFF;'>{pos['symbol']}</div>"
                    f"<div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#3A6A7A;'>{pos['quantity']:.6f}</div></div>"
                    f"<div><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;letter-spacing:0.08em;'>ENTRY</div>"
                    f"<div style='font-family:Space Mono,monospace;font-size:0.75rem;color:#A0D4E8;'>${pos['avg_buy_price']:,.4f}</div></div>"
                    f"<div><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;letter-spacing:0.08em;'>LIVE</div>"
                    f"<div style='font-family:Space Mono,monospace;font-size:0.75rem;color:{TEAL};'>${pos['live_price']:,.4f}</div></div>"
                    f"<div><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;letter-spacing:0.08em;'>VALUE</div>"
                    f"<div style='font-family:Space Mono,monospace;font-size:0.75rem;color:#E0FAFF;'>${pos['value']:,.2f}</div></div>"
                    f"<div><div style='font-size:0.5rem;color:{AZURE};font-family:Orbitron,monospace;letter-spacing:0.08em;'>UNREALIZED</div>"
                    f"<div style='font-family:Space Mono,monospace;font-size:0.75rem;font-weight:700;color:{pnl_c};'>${pos['unrealized_pnl']:+,.2f} ({pos['pnl_pct']:+.1f}%)</div></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        with col_r:
            labels = ["Cash"] + [p["symbol"].split("/")[0] for p in positions]
            values = [balance] + [p["value"] for p in positions]
            colors = [AZURE, TEAL, GOLD, "#00C9A7", "#0077B6", "#FF9F1C", "#E71D36"]
            fig_d  = go.Figure(go.Pie(
                labels=labels, values=values, hole=0.62,
                marker=dict(colors=colors[:len(labels)], line=dict(color="#050D1A",width=2)),
                textfont=dict(family="Orbitron",size=9),
                hovertemplate="%{label}<br>$%{value:,.2f} · %{percent}<extra></extra>",
            ))
            fig_d.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", height=270,
                font=dict(color=AZURE,family="Rajdhani"),
                legend=dict(font=dict(color=AZURE,size=9),bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=8,r=8,t=30,b=8),
                title=dict(text="ALLOCATION", font=dict(family="Orbitron",color=TEAL,size=12)),
                annotations=[dict(text=f"<b>${total:,.0f}</b>", x=0.5, y=0.5,
                    font=dict(size=13,color=TEAL,family="Orbitron"), showarrow=False)],
            )
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            f"<div class='card-glass' style='text-align:center;padding:2.5rem;opacity:0.6;'>"
            f"<div style='font-family:Orbitron,monospace;font-size:0.72rem;color:{AZURE};letter-spacing:0.2em;'>NO OPEN POSITIONS</div>"
            f"<div style='font-family:Rajdhani,sans-serif;color:#3A6A7A;margin-top:0.3rem;'>Start the bot or execute manual trades</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("<h3>TRADE HISTORY</h3>", unsafe_allow_html=True)
    trades = get_trades(50)
    if trades:
        df_t = pd.DataFrame(trades)
        df_t["P&L"]   = df_t["pnl"].apply(lambda x: f"${x:+,.2f}")
        df_t["PRICE"]  = df_t["price"].apply(lambda x: f"${x:,.4f}")
        df_t["TOTAL"]  = df_t["total"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(
            df_t[["created_at","symbol","side","quantity","PRICE","TOTAL","P&L","strategy"]]
            .rename(columns={"created_at":"TIME","symbol":"PAIR","side":"SIDE",
                             "quantity":"QTY","strategy":"STRATEGY"}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No trades yet.")
