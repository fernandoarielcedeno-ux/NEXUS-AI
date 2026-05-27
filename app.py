import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.database import init_db

st.set_page_config(
    page_title="NEXUS AI Trading",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

/* ── Hide Streamlit auto-generated page nav ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"] ul,
section[data-testid="stSidebar"] nav {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}

:root {
    --teal:   #00F5D4;
    --azure:  #00B4D8;
    --dark:   #050D1A;
    --card:   #081426;
    --card2:  #0A1A30;
    --border: rgba(0,245,212,0.15);
    --glow:   0 0 22px rgba(0,245,212,0.28);
    --glow2:  0 0 36px rgba(0,180,216,0.18);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--dark) !important;
    font-family: 'Rajdhani', sans-serif;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050D1A 0%, #081426 55%, #0A1A30 100%) !important;
    border-right: 1px solid var(--border);
    box-shadow: 4px 0 28px rgba(0,245,212,0.05);
}
[data-testid="stSidebar"] * { color: #E0FAFF !important; }

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: transparent;
    border: 1px solid rgba(0,245,212,0.14);
    color: #00F5D4 !important;
    font-family: 'Orbitron', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    padding: 0.6rem 1rem;
    border-radius: 6px;
    text-align: left;
    transition: all 0.22s ease;
    margin-bottom: 0.28rem;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(0,245,212,0.09);
    border-color: #00F5D4;
    box-shadow: var(--glow);
    transform: translateX(4px);
}

[data-testid="metric-container"] {
    background: linear-gradient(135deg, var(--card) 0%, var(--card2) 100%) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    box-shadow: var(--glow2) !important;
}
[data-testid="metric-container"] label {
    color: var(--azure) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.15em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--teal) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 1.45rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace !important; }

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    color: var(--teal) !important;
    border-radius: 8px !important;
}

[data-testid="stSlider"] > div { accent-color: #00F5D4; }

.stButton > button {
    background: linear-gradient(135deg, #00F5D4 0%, #00B4D8 100%) !important;
    color: #050D1A !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.58rem 1.3rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 18px rgba(0,245,212,0.22) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,245,212,0.38) !important;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--border) !important;
    gap: 0.2rem;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.63rem !important;
    letter-spacing: 0.12em !important;
    color: rgba(0,245,212,0.45) !important;
    border-radius: 8px 8px 0 0 !important;
    transition: all 0.2s ease !important;
    padding: 0.48rem 1rem !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #00F5D4 !important;
    background: rgba(0,245,212,0.07) !important;
    border-bottom: 2px solid #00F5D4 !important;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #050D1A; }
::-webkit-scrollbar-thumb { background: #00C9A7; border-radius: 3px; }

h1, h2, h3 {
    font-family: 'Orbitron', monospace !important;
    color: #00F5D4 !important;
    letter-spacing: 0.07em;
}

hr { border-color: rgba(0,245,212,0.12) !important; }

[data-testid="stAlert"] {
    background: rgba(0,245,212,0.07) !important;
    border: 1px solid #00F5D4 !important;
    border-radius: 10px !important;
}

.nexus-logo {
    font-family: 'Orbitron', monospace;
    font-size: 1.35rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00F5D4, #00B4D8, #00F5D4);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
    letter-spacing: 0.18em;
}
@keyframes shimmer {
    0%   { background-position: 0%   center; }
    100% { background-position: 200% center; }
}

.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    animation: blink 1.6s ease-in-out infinite;
    margin-right: 7px;
    vertical-align: middle;
}
.dot-green { background: #00F5D4; box-shadow: 0 0 7px #00F5D4; }
.dot-red   { background: #FF4D6D; box-shadow: 0 0 7px #FF4D6D; }
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
}

.card-glass {
    background: linear-gradient(135deg, rgba(8,20,38,0.92) 0%, rgba(10,26,48,0.92) 100%);
    border: 1px solid rgba(0,245,212,0.14);
    border-radius: 13px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 3px 26px rgba(0,180,216,0.09);
    backdrop-filter: blur(8px);
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="nexus-logo">NEXUS AI</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.65rem;color:#00B4D8;letter-spacing:0.2em;"
        "margin-top:0.1rem;margin-bottom:0;font-family:Space Mono,monospace;'>TRADING SYSTEM</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    nav = {
        "DASHBOARD":   "dashboard",
        "BOT CONTROL": "bot",
        "ANALYTICS":   "analytics",
        "BACKTEST":    "backtest",
        "SIGNALS":     "signals",
        "PORTFOLIO":   "portfolio",
        "SETTINGS":    "settings",
    }

    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    for label, key in nav.items():
        if st.button(label, key=f"nav_{key}"):
            st.session_state["page"] = key

    st.markdown("---")

    from core.database import get_config, get_stats
    running   = get_config("bot_running") == "true"
    dot_cls   = "dot-green" if running else "dot-red"
    status_tx = "RUNNING" if running else "STOPPED"
    st.markdown(
        f"<span class='status-dot {dot_cls}'></span>"
        f"<span style='font-family:Orbitron,monospace;font-size:0.65rem;"
        f"color:#00F5D4;letter-spacing:0.12em;'>{status_tx}</span>",
        unsafe_allow_html=True,
    )

    balance  = float(get_config("current_balance") or 10000)
    init_b   = float(get_config("initial_balance") or 10000)
    pnl      = balance - init_b
    pnl_pct  = pnl / init_b * 100
    pnl_clr  = "#00F5D4" if pnl >= 0 else "#FF4D6D"
    st.markdown(f"""
    <div style="margin-top:1rem;">
      <div style="font-family:Orbitron,monospace;font-size:0.55rem;color:#00B4D8;letter-spacing:0.15em;">PORTFOLIO</div>
      <div style="font-family:Orbitron,monospace;font-size:1.15rem;color:#00F5D4;font-weight:700;">${balance:,.2f}</div>
      <div style="font-family:Space Mono,monospace;font-size:0.7rem;color:{pnl_clr};">
        {'▲' if pnl >= 0 else '▼'} ${abs(pnl):,.2f} ({pnl_pct:+.2f}%)
      </div>
    </div>
    """, unsafe_allow_html=True)


page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    from _views import dashboard; dashboard.show()
elif page == "bot":
    from _views import bot_control; bot_control.show()
elif page == "analytics":
    from _views import analytics; analytics.show()
elif page == "backtest":
    from _views import backtest; backtest.show()
elif page == "signals":
    from _views import signals; signals.show()
elif page == "portfolio":
    from _views import portfolio; portfolio.show()
elif page == "settings":
    from _views import settings; settings.show()
