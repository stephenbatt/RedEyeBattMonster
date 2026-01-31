import os
import time
import threading
import requests
import streamlit as st
from datetime import datetime

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
POLL_SECONDS = 5

# Shared data structure
shared_prices = {s: {"last": 0.0, "high": 0.0, "low": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTE ─────────
def fetch_quote(symbol):
    try:
        if symbol == "BINANCE:BTCUSDT":
            r = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"},
                timeout=5
            )
            price = float(r.json()["price"])
            return {"c": price, "h": price, "l": price}
        else:  # SPY via Finnhub
            r = requests.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": symbol, "token": FINNHUB_KEY},
                timeout=5
            )
            if r.status_code != 200:
                return {}
            data = r.json()
            return {
                "c": float(data.get("c") or 0.0),
                "h": float(data.get("h") or 0.0),
                "l": float(data.get("l") or 0.0)
            }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return {}

# ───────── POLLER THREAD ─────────
def poller_loop():
    while True:
        for sym in TICKERS:
            data = fetch_quote(sym)
            if not data:
                continue
            last = float(data.get("c") or 0.0)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if last <= 0:
                continue
            with shared_lock:
                cur = shared_prices[sym]
                cur["last"] = last
                cur["high"] = float(data.get("h") or last)
                cur["low"] = float(data.get("l") or last)
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT SETUP ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

# Start poller once
if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Initialize session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": 0.0, "high": 10.0} for s in TICKERS})
st.session_state.setdefault("buffer", {s: 0 for s in TICKERS})
st.session_state.setdefault("bet", {s: 200 for s in TICKERS})
st.session_state.setdefault("history", [])
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})

# ───────── LAYOUT ─────────
branding, market = st.columns([1, 2])

# Branding column
with branding:
    try:
        st.image("logo.gif", width=120)
    except Exception:
        st.write("🧨 RedEyeBatt Monster Cockpit")
    st.markdown("### 🧮 Scoreboard")
    for s, record in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {record['wins']} | ❌ {record['losses']}")
    st.markdown(f"💰 Bankroll: ${st.session_state.bankroll:,.2f}")

# Market column
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    for sym in TICKERS:
        cur = shared_prices[sym]
        price = cur["last"] if cur["last"] != 0 else "❌ Waiting for data..."
        updated = cur["updated"] or "—"

        st.subheader(f"📊 {sym}" + (" (Heartbeat)" if sym.startswith("BINANCE") else ""))
        st.write(f"Price: {price}")
        st.write(f"Updated: {updated}")

        # Buffers and bets
        st.number_input(f"Buffer ± points for {sym}", min_value=0, max_value=50,
                        value=st.session_state.buffer[sym], key=f"buffer_{sym}")
        st.number_input(f"Bet per {sym} ($)", min_value=0, max_value=10000,
                        value=st.session_state.bet[sym], key=f"bet_{sym}")

        # Fence sliders
        low = st.number_input(f"{sym} Fence Low", value=st.session_state.fence[sym]["low"], step=0.01, key=f"fence_low_{sym}")
        high = st.number_input(f"{sym} Fence High", value=st.session_state.fence[sym]["high"], step=0.01, key=f"fence_high_{sym}")
        st.session_state.fence[sym]["low"] = low
        st.session_state.fence[sym]["high"] = high

    # Trade history
    st.markdown("📅 Trade History")
    if st.session_state.history:
        for entry in reversed(st.session_state.history):
            st.write(entry)
    else:
        st.write("No trades yet.")

    st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

