import os
import time
import threading
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 3  # Timex-style updates

shared_prices = {s: {"last": 0.0, "high": 0.0, "low": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTES ─────────
def fetch_quote(symbol):
    try:
        if symbol == "BINANCE:BTCUSDT":
            r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
            price = float(r.json()["price"])
            return {"c": price, "h": price, "l": price}
        else:  # SPY via Finnhub
            r = requests.get(BASE_URL, params={"symbol": symbol, "token": FINNHUB_KEY}, timeout=5)
            if r.status_code != 200: return {}
            data = r.json()
            c = float(data.get("c") or 0.0)
            h = float(data.get("h") or c)
            l = float(data.get("l") or c)
            return {"c": c, "h": h, "l": l}
    except Exception:
        return {}

# ───────── POLLER LOOP ─────────
def poller_loop():
    while True:
        for sym in TICKERS:
            data = fetch_quote(sym)
            if not data: continue
            last = data["c"]
            high = data["h"]
            low = data["l"]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if last <= 0: continue
            with shared_lock:
                cur = shared_prices[sym]
                cur["last"] = last
                cur["high"] = max(cur["high"], high) if cur["high"] else high
                cur["low"] = min(cur["low"], low) if cur["low"] else low
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT UI ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Initialize session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("history", [])
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})

# ───────── LAYOUT ─────────
branding, market = st.columns([1, 2])

# Branding
with branding:
    try:
        st.image("logo.gif", width=120)
    except Exception:
        st.write("🧨 RedEyeBatt Monster Cockpit")
    st.markdown("### 🧮 Scoreboard")
    for s, record in st.session_state.scoreboard.items():
        status = "heartbeat only" if s=="BINANCE:BTCUSDT" else f"✅ {record['wins']} | ❌ {record['losses']}"
        st.write(f"{s}: {status}")

# Market Column
with market:
    st.caption("Live market simulator — paper only. You are the house.")

    st.session_state.bankroll = st.number_input("💰 Bankroll", value=st.session_state.bankroll, step=100.0)

    with shared_lock:
        prices_snapshot = {k: v.copy() for k, v in shared_prices.items()}

    for sym in TICKERS:
        data = prices_snapshot[sym]
        last, high, low, updated = data["last"], data["high"], data["low"], data["updated"]

        st.subheader(f"📊 {sym}" + (" (Heartbeat)" if sym=="BINANCE:BTCUSDT" else ""))
        c1, c2 = st.columns([2, 1])
        c1.metric("Price", f"${last:,.2f}" if last else "❌ Waiting for data...")
        c2.metric("Updated", updated if updated else "--")

        buf_key = f"buffer_{sym}"
        st.session_state.setdefault(buf_key, 10)
        buf = st.slider(f"Buffer ± points for {sym}", 0, 50, st.session_state[buf_key], key=buf_key)

        bet_key = f"bet_{sym}"
        st.session_state.setdefault(bet_key, 200)
        bet = st.number_input(f"Bet per {sym} ($)", 0, 5000, st.session_state[bet_key], key=bet_key)

        if st.button(f"Set fence for {sym}", key=f"fence_{sym}"):
            st.session_state.fence[sym]["low"] = max(0.0, last - buf)
            st.session_state.fence[sym]["high"] = last + buf

        fl = st.session_state.fence[sym]["low"]
        fh = st.session_state.fence[sym]["high"]
        st.write(f"Fence: Low = {fl if fl else '--'} | High = {fh if fh else '--'}")

# ───────── Trade History ─────────
st.subheader("📅 Trade History")
if st.button("Reset History"):
    st.session_state.history = []
    st.success("History cleared.")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)


