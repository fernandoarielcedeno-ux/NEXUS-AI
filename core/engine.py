import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import math


SEEDS = {
    "BTC/USDT":  (65000, 0.0008, 0.018),
    "ETH/USDT":  (3500,  0.0007, 0.020),
    "SOL/USDT":  (180,   0.0009, 0.025),
    "BNB/USDT":  (580,   0.0006, 0.018),
    "ADA/USDT":  (0.65,  0.0005, 0.022),
    "XRP/USDT":  (0.75,  0.0005, 0.021),
    "AVAX/USDT": (40,    0.0008, 0.024),
    "DOGE/USDT": (0.18,  0.0006, 0.028),
}

def generate_market_data(symbol: str, periods: int = 300, interval_minutes: int = 15):
    np.random.seed(hash(symbol) % 2**32)
    base_price, drift, vol = SEEDS.get(symbol, (100, 0.0006, 0.020))
    now = datetime.now()
    timestamps = [now - timedelta(minutes=interval_minutes * (periods - i)) for i in range(periods)]
    prices = [base_price]
    for _ in range(periods - 1):
        ret = drift + vol * np.random.randn()
        if np.random.random() < 0.02:
            ret += np.random.choice([-1, 1]) * vol * 3
        prices.append(max(prices[-1] * (1 + ret), prices[-1] * 0.5))
    opens, highs, lows, closes, volumes = [], [], [], [], []
    for p in prices:
        o = p * (1 + np.random.randn() * 0.003)
        c = p * (1 + np.random.randn() * 0.004)
        h = max(o, c) * (1 + abs(np.random.randn() * 0.005))
        l = min(o, c) * (1 - abs(np.random.randn() * 0.005))
        v = abs(np.random.randn() * 500 + 1000) * base_price / 100
        opens.append(o); highs.append(h); lows.append(l); closes.append(c); volumes.append(v)
    df = pd.DataFrame({"timestamp": timestamps, "open": opens, "high": highs,
                        "low": lows, "close": closes, "volume": volumes})
    return df.set_index("timestamp")

def get_analyzed_pair(symbol: str, periods: int = 300):
    df_raw = generate_market_data(symbol, periods)
    df = compute_indicators(df_raw)
    sig = score_signal(df)
    return df, sig

def get_scanner_data():
    all_pairs = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","ADA/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT"]
    results = []
    for p in all_pairs:
        df_raw = generate_market_data(p, periods=120)
        d = compute_indicators(df_raw)
        s = score_signal(d)
        pr = s["price"]
        ch = (pr - d["close"].iloc[-25]) / d["close"].iloc[-25] * 100
        results.append((p, pr, ch, s["rsi"], s["signal"], s["confidence"], s["composite_score"]))
    return results

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    c = df["close"]
    h, l, v = df["high"], df["low"], df["volume"]
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df = df.copy()
    df["rsi"] = 100 - 100 / (1 + rs)
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_lower"] = sma20 - 2 * std20
    df["bb_mid"]   = sma20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / sma20
    for span in [9, 21, 50, 200]:
        df[f"ema{span}"] = c.ewm(span=span, adjust=False).mean()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["volume_sma"] = v.rolling(20).mean()
    df["volume_ratio"] = v / df["volume_sma"]
    low14  = l.rolling(14).min()
    high14 = h.rolling(14).max()
    df["stoch_k"] = 100 * (c - low14) / (high14 - low14 + 1e-10)
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    obv = [0]
    for i in range(1, len(df)):
        if c.iloc[i] > c.iloc[i-1]:
            obv.append(obv[-1] + v.iloc[i])
        elif c.iloc[i] < c.iloc[i-1]:
            obv.append(obv[-1] - v.iloc[i])
        else:
            obv.append(obv[-1])
    df["obv"] = obv
    df["obv_ema"] = pd.Series(obv, index=df.index).ewm(span=20, adjust=False).mean()
    df["momentum"] = c / c.shift(10) - 1
    df["roc"] = c.pct_change(5) * 100
    df["pivot"] = (h.shift(1) + l.shift(1) + c.shift(1)) / 3
    df["r1"] = 2 * df["pivot"] - l.shift(1)
    df["s1"] = 2 * df["pivot"] - h.shift(1)
    return df.dropna()

def score_signal(df: pd.DataFrame) -> dict:
    row  = df.iloc[-1]
    prev = df.iloc[-2]
    scores = {}
    rsi = row["rsi"]
    if rsi < 30:   scores["rsi"] = (30 - rsi) / 30 * 100
    elif rsi > 70: scores["rsi"] = -(rsi - 70) / 30 * 100
    else:          scores["rsi"] = (50 - rsi) / 50 * 30
    macd_cross = row["macd_hist"] > 0 and prev["macd_hist"] <= 0
    macd_death = row["macd_hist"] < 0 and prev["macd_hist"] >= 0
    if macd_cross:   scores["macd"] = 80
    elif macd_death: scores["macd"] = -80
    else:            scores["macd"] = min(max(row["macd_hist"] / (row["atr"] + 1e-10) * 40, -60), 60)
    bb_pos = (row["close"] - row["bb_lower"]) / (row["bb_upper"] - row["bb_lower"] + 1e-10)
    if bb_pos < 0.1:   scores["bollinger"] = 70
    elif bb_pos > 0.9: scores["bollinger"] = -70
    else:              scores["bollinger"] = (0.5 - bb_pos) * 60
    ema_bull = row["ema9"] > row["ema21"] > row["ema50"]
    ema_bear = row["ema9"] < row["ema21"] < row["ema50"]
    if ema_bull:   scores["ema_trend"] = 60
    elif ema_bear: scores["ema_trend"] = -60
    else:          scores["ema_trend"] = (row["ema9"] - row["ema50"]) / row["ema50"] * 500
    scores["volume"]   = min(row["volume_ratio"] * 15, 50) if row["volume_ratio"] > 2.0 else 0
    stoch = row["stoch_k"]
    if stoch < 20:   scores["stoch"] = (20 - stoch) / 20 * 70
    elif stoch > 80: scores["stoch"] = -(stoch - 80) / 20 * 70
    else:            scores["stoch"] = 0
    scores["obv"]      = 40 if row["obv"] > row["obv_ema"] else -40
    scores["momentum"] = min(max(row["momentum"] * 200, -50), 50)
    weights = {"rsi":0.18,"macd":0.22,"bollinger":0.15,"ema_trend":0.20,"volume":0.08,"stoch":0.08,"obv":0.05,"momentum":0.04}
    composite = sum(scores[k] * weights[k] for k in scores)
    confidence = min(abs(composite), 100)
    if composite > 5:   signal = "BUY"
    elif composite < -5: signal = "SELL"
    else:                signal = "HOLD"
    return {
        "signal": signal, "composite_score": round(composite, 2),
        "confidence": round(confidence, 1),
        "scores": {k: round(v, 1) for k, v in scores.items()},
        "price": round(row["close"], 4), "rsi": round(rsi, 2),
        "macd": round(row["macd"], 4), "bb_pos": round(bb_pos * 100, 1),
        "volume_ratio": round(row["volume_ratio"], 2), "atr": round(row["atr"], 4),
        "ema9": round(row["ema9"], 4), "ema21": round(row["ema21"], 4), "ema50": round(row["ema50"], 4),
    }

def calculate_position_size(balance, price, risk_pct, stop_loss_pct):
    risk_amount  = balance * risk_pct
    stop_loss_usd = price * stop_loss_pct
    qty = risk_amount / stop_loss_usd if stop_loss_usd > 0 else 0
    max_qty = (balance * 0.20) / price
    return min(qty, max_qty)

def calculate_pnl(entry_price, exit_price, quantity, side):
    if side == "BUY": return (exit_price - entry_price) * quantity
    return (entry_price - exit_price) * quantity

def ai_price_prediction(df: pd.DataFrame, horizon: int = 5) -> dict:
    closes    = df["close"].values[-50:]
    current   = closes[-1]
    trend     = (closes[-1] / closes[-20] - 1) * 100
    volatility = np.std(np.diff(np.log(closes))) * 100
    momentum  = (closes[-1] / closes[-5] - 1) * 100
    model1 = trend * 0.6 + momentum * 0.4
    model2 = -trend * 0.3 + (50 - df.iloc[-1]["rsi"]) * 0.05
    model3 = df.iloc[-1]["macd_hist"] / (df.iloc[-1]["atr"] + 1e-10) * 2
    ensemble = model1 * 0.5 + model2 * 0.3 + model3 * 0.2
    noise    = np.random.randn() * volatility * 0.3
    predicted_change_pct = ensemble * 0.4 + noise
    predicted_price      = current * (1 + predicted_change_pct / 100)
    ci_68 = current * volatility / 100 * math.sqrt(horizon)
    ci_95 = ci_68 * 1.96
    direction = "BULLISH" if predicted_change_pct > 0.5 else ("BEARISH" if predicted_change_pct < -0.5 else "NEUTRAL")
    return {
        "current_price": round(current, 4), "predicted_price": round(predicted_price, 4),
        "predicted_change_pct": round(predicted_change_pct, 2), "direction": direction,
        "confidence_68": round(ci_68, 4), "confidence_95": round(ci_95, 4),
        "horizon_candles": horizon,
        "model_scores": {"trend_following": round(model1,2), "mean_reversion": round(model2,2), "macd_model": round(model3,2)},
    }

def run_backtest(symbol: str, initial_balance: float = 10000, periods: int = 300):
    df_raw = generate_market_data(symbol, periods=periods + 50)
    df = compute_indicators(df_raw).iloc[50:]
    balance, position, entry_price = initial_balance, 0, 0
    trades, equity_curve, dates = [], [initial_balance], [df.index[0]]
    stop_loss_pct, take_profit_pct = 0.03, 0.06
    for i in range(20, len(df)):
        window = df.iloc[:i]
        sig    = score_signal(window)
        price  = window.iloc[-1]["close"]
        if sig["signal"] == "BUY" and position == 0 and sig["confidence"] > 20:
            qty = calculate_position_size(balance, price, 0.02, stop_loss_pct)
            if qty * price < balance:
                position, entry_price = qty, price
                balance -= qty * price
        elif position > 0:
            change   = (price - entry_price) / entry_price
            hit_tp   = change >= take_profit_pct
            hit_sl   = change <= -stop_loss_pct
            sig_sell = sig["signal"] == "SELL" and sig["confidence"] > 25
            if hit_tp or hit_sl or sig_sell:
                pnl     = (price - entry_price) * position
                balance += position * price
                trades.append({"price": price, "entry": entry_price, "pnl": pnl,
                               "reason": "TP" if hit_tp else ("SL" if hit_sl else "SIGNAL"), "date": window.index[-1]})
                position, entry_price = 0, 0
        equity_curve.append(balance + (position * price if position > 0 else 0))
        dates.append(window.index[-1])
    returns  = np.diff(equity_curve) / np.array(equity_curve[:-1])
    sharpe   = (np.mean(returns) / np.std(returns) * np.sqrt(252 * 24)) if np.std(returns) > 0 else 0
    peak, max_dd = equity_curve[0], 0
    for e in equity_curve:
        if e > peak: peak = e
        dd = (peak - e) / peak
        if dd > max_dd: max_dd = dd
    wins = [t for t in trades if t["pnl"] > 0]
    return {
        "equity_curve": equity_curve, "dates": dates, "trades": trades,
        "total_trades": len(trades),
        "win_rate": len(wins) / len(trades) * 100 if trades else 0,
        "total_pnl": sum(t["pnl"] for t in trades),
        "total_return_pct": (equity_curve[-1] / initial_balance - 1) * 100,
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "final_balance": equity_curve[-1],
    }
