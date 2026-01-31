import os
import time
import threading
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 5

shared_prices = {s: {"last": None, "high": None, "low": None, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTE ─────────
def fetch_quote(symbol):
    try:
        if symbol == "BINANCE:BTCUSDT":
            r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
            price = float(r.json()["price"])
            return {"c": price, "h": price, "l": price}
        else:
            r = requests.get(BASE_URL, params={"symbol": symbol, "token": FINNHUB_KEY}, timeout=8)
            if r.status_code != 200: return {}
            data = r.json()
            return {
                "c": float(data.get("c") or 0.0),
                "h": float(data.get("h") or 0.0),
                "l": float(data.get("l") or 0.0)
            }
    except Exception:
        return {}

# ───────── POLLER LOOP ─────────
def poller_loop():
    while True:
        for sym in TICKERS:
            data = fetch_quote(sym)
            if not data: 
                continue
            last, high, low = data["c"], data["h"], data["l"]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with shared_lock:
                cur = shared_prices[sym]
                cur["last"] = last
                cur["high"] = max(cur["high"] or 0, high)
                cur["low"] = min(cur["low"] or last, low)
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT SETUP ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("history", [])
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})
st.session_state.setdefault("candles", {"SPY": pd.DataFrame(columns=["time","open","high","low","close"])})

# ───────── UI LAYOUT ─────────
branding, market = st.columns([1,2])

# Branding column
with branding:
    # Placeholder logo
    st.image("https://via.placeholder.com/120x120.png?text=RedEyeBatt", width=120)
    st.markdown("### 🧮 Scoreboard")
    for s, rec in st.session_state.scoreboard.items():
        label = "heartbeat only" if s == "BINANCE:BTCUSDT" else f"✅ {rec['wins']} | ❌ {rec['losses']}"
        st.write(f"{s}: {label}")

# Market column
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")
    st.session_state.bankroll = st.number_input("💰 Bankroll", value=st.session_state.bankroll, step=100.0)

    with shared_lock:
        snapshot = {k:v.copy() for k,v in shared_prices.items()}

    for sym in TICKERS:
        data = snapshot[sym]
        last = data["last"]
        updated = data["updated"]
        st.subheader(f"📊 {sym}")

        if last:
            st.write(f"Price: ${last:,.2f}")
            st.caption(f"Updated: {updated}")
        else:
            st.write("❌ Waiting for data...")

        buf_key = f"buffer_{sym}"
        st.session_state.setdefault(buf_key, 10)
        buf = st.slider(f"Buffer ± points for {sym}", 0, 50, st.session_state[buf_key], key=buf_key)

        bet_key = f"bet_{sym}"
        st.session_state.setdefault(bet_key, 200)
        bet = st.number_input(f"Bet per {sym} ($)", 0, 5000, st.session_state[bet_key], key=bet_key)

        if st.button(f"Set fence around {sym}", key=f"set_{sym}") and last:
            st.session_state.fence[sym]["low"] = max(0.0, last - buf)
            st.session_state.fence[sym]["high"] = last + buf

        fl = st.session_state.fence[sym]["low"]
        fh = st.session_state.fence[sym]["high"]
        st.write(f"Fence: Low = {fl if fl else '--'} | High = {fh if fh else '--'}")

    # ───────── CANDLESTICK (SPY) ─────────
    spy_price = snapshot["SPY"]["last"]
    if spy_price:
        candle_df = st.session_state.candles["SPY"]
        now_time = datetime.now()
        new_row = pd.DataFrame([{
            "time": now_time,
            "open": spy_price,
            "high": spy_price,
            "low": spy_price,
            "close": spy_price
        }])
        st.session_state.candles["SPY"] = pd.concat([candle_df, new_row], ignore_index=True).tail(50)
        fig = go.Figure(data=[go.Candlestick(
            x=st.session_state.candles["SPY"]["time"],
            open=st.session_state.candles["SPY"]["open"],
            high=st.session_state.candles["SPY"]["high"],
            low=st.session_state.candles["SPY"]["low"],
            close=st.session_state.candles["SPY"]["close"]
        )])
        fig.update_layout(height=300, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# ───────── HISTORY ─────────
st.subheader("📅 Trade History")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)
else:
    st.write("No trades yet.")

st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

# ───────── AUTO-REFRESH EVERY POLL ─────────
st.experimental_rerun()


