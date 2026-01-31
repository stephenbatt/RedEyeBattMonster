import os
import time
import threading
from datetime import datetime
import requests
import streamlit as st
import pandas as pd

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 1  # Super fast updates

# Shared state
shared_prices = {s: {"last": None, "high": None, "low": None, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTES ─────────
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
            r = requests.get(BASE_URL, params={"symbol": symbol, "token": FINNHUB_KEY}, timeout=5)
            if r.status_code != 200:
                return {}
            data = r.json()
            return {
                "c": float(data.get("c") or 0.0),
                "h": float(data.get("h") or 0.0),
                "l": float(data.get("l") or 0.0)
            }
    except Exception:
        return {}

# ───────── POLLER THREAD ─────────
def poller_loop():
    while True:
        for sym in TICKERS:
            data = fetch_quote(sym)
            if not data:
                continue
            with shared_lock:
                shared_prices[sym]["last"] = data["c"]
                shared_prices[sym]["high"] = data.get("h", data["c"])
                shared_prices[sym]["low"] = data.get("l", data["c"])
                shared_prices[sym]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT UI ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

# Start poller thread once
if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Session state initialization
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("history", [])
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("buffer", {s: 0 for s in TICKERS})
st.session_state.setdefault("bet_amount", {s: 200 for s in TICKERS})

# ───────── LAYOUT ─────────
branding_col, market_col = st.columns([1, 2])

# Branding column
with branding_col:
    try:
        st.image("logo.gif", width=120)
    except Exception:
        st.write("🦇 RedEyeBatt Logo missing")
    st.markdown("### 🧮 Scoreboard")
    for s, rec in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {rec['wins']} | ❌ {rec['losses']}")

# Market column
with market_col:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    st.number_input("💰 Bankroll", value=st.session_state.bankroll, key="bankroll_input")

    for sym in TICKERS:
        st.markdown(f"📊 {sym}" + (" (Heartbeat)" if sym.startswith("BINANCE") else ""))
        price_data = shared_prices[sym]
        last = price_data["last"]
        updated = price_data["updated"]

        st.write("Price")
        st.write(f"${last:,.2f}" if last else "❌ Waiting for data...")
        st.write("Updated")
        st.write(updated or "—")

        # Fence sliders
        st.session_state.buffer[sym] = st.slider(
            f"Buffer ± points for {sym}",
            0, 50, st.session_state.buffer.get(sym, 0), key=f"buffer_{sym}"
        )
        st.session_state.bet_amount[sym] = st.number_input(
            f"Bet per {sym} ($)", value=st.session_state.bet_amount.get(sym, 200), key=f"bet_{sym}"
        )

        st.session_state.fence[sym]["low"] = last - st.session_state.buffer[sym] if last else None
        st.session_state.fence[sym]["high"] = last + st.session_state.buffer[sym] if last else None

        st.write(f"Fence: Low = {st.session_state.fence[sym]['low'] if last else '—'} | High = {st.session_state.fence[sym]['high'] if last else '—'}")

    st.markdown("📅 Trade History")
    if not st.session_state.history:
        st.write("No trades yet.")
    else:
        df_hist = pd.DataFrame(st.session_state.history)
        st.dataframe(df_hist)

st.markdown("Paper trading only • No broker • Real market data • Built for RedEyeBatt")
