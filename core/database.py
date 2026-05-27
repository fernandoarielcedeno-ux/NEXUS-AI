import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "trading_bot.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            avg_buy_price REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            pnl REAL DEFAULT 0,
            strategy TEXT,
            signal_strength REAL DEFAULT 0,
            status TEXT DEFAULT 'EXECUTED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bot_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            signal TEXT NOT NULL,
            confidence REAL NOT NULL,
            price REAL NOT NULL,
            indicators TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_balance REAL NOT NULL,
            pnl_daily REAL DEFAULT 0,
            pnl_total REAL DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bot_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            trades_count INTEGER DEFAULT 0,
            profit REAL DEFAULT 0,
            status TEXT DEFAULT 'RUNNING'
        );
    """)

    defaults = {
        "initial_balance": "10000",
        "current_balance": "10000",
        "risk_per_trade": "0.02",
        "max_open_trades": "5",
        "bot_running": "false",
        "strategy": "HYBRID_AI",
        "selected_pairs": '["BTC/USDT","ETH/USDT","SOL/USDT"]',
        "stop_loss_pct": "0.03",
        "take_profit_pct": "0.06",
        "leverage": "1",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO bot_config (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

def get_config(key):
    conn = get_conn()
    row = conn.execute("SELECT value FROM bot_config WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None

def set_config(key, value):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO bot_config (key, value, updated_at) VALUES (?, ?, ?)",
        (key, str(value), datetime.now()),
    )
    conn.commit()
    conn.close()

def log_trade(symbol, side, quantity, price, pnl=0, strategy="AI", signal_strength=0):
    total = quantity * price
    conn = get_conn()
    conn.execute(
        """INSERT INTO trades (symbol,side,quantity,price,total,pnl,strategy,signal_strength)
           VALUES (?,?,?,?,?,?,?,?)""",
        (symbol, side, quantity, price, total, pnl, strategy, signal_strength),
    )
    conn.commit()
    conn.close()

def log_signal(symbol, signal, confidence, price, indicators=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO signals (symbol,signal,confidence,price,indicators) VALUES (?,?,?,?,?)",
        (symbol, signal, confidence, price, json.dumps(indicators or {})),
    )
    conn.commit()
    conn.close()

def log_balance(total_balance, pnl_daily=0, pnl_total=0):
    conn = get_conn()
    conn.execute(
        "INSERT INTO balance_history (total_balance,pnl_daily,pnl_total) VALUES (?,?,?)",
        (total_balance, pnl_daily, pnl_total),
    )
    conn.commit()
    conn.close()

def get_trades(limit=100):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_signals(limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_balance_history(limit=200):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM balance_history ORDER BY recorded_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_portfolio():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM portfolio").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_portfolio(symbol, quantity, avg_price):
    conn = get_conn()
    existing = conn.execute(
        "SELECT * FROM portfolio WHERE symbol=?", (symbol,)
    ).fetchone()
    if existing:
        if quantity <= 0:
            conn.execute("DELETE FROM portfolio WHERE symbol=?", (symbol,))
        else:
            conn.execute(
                "UPDATE portfolio SET quantity=?, avg_buy_price=?, updated_at=? WHERE symbol=?",
                (quantity, avg_price, datetime.now(), symbol),
            )
    else:
        if quantity > 0:
            conn.execute(
                "INSERT INTO portfolio (symbol,quantity,avg_buy_price) VALUES (?,?,?)",
                (symbol, quantity, avg_price),
            )
    conn.commit()
    conn.close()

def get_stats():
    conn = get_conn()
    trades = conn.execute("SELECT * FROM trades").fetchall()
    conn.close()
    if not trades:
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0, "best": 0, "worst": 0}
    total = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    losses = sum(1 for t in trades if t["pnl"] < 0)
    total_pnl = sum(t["pnl"] for t in trades)
    pnls = [t["pnl"] for t in trades]
    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / total * 100) if total > 0 else 0,
        "total_pnl": total_pnl,
        "best": max(pnls) if pnls else 0,
        "worst": min(pnls) if pnls else 0,
    }
