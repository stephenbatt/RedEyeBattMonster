import os
import time
import threading
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# ───────── CONFIG ─────────
ALPACA_KEY = os.getenv("ALPACA_KEY", "").strip()
ALPACA_SECRET = os.getenv("ALPACA_SECRET", "").strip()
ALPACA_BASE = "https://paper-api.alpaca.markets"

POLL_SECONDS = 5

TICKERS = ["SPY", "BTC"]

shared_prices = {s: {"last": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH FUNCTIONS ─────────
def fetch_spy_price():
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
        r = requests.get(f"{ALPACA_BASE}/v2/stocks/SPY/quotes/latest", headers=headers, timeout=5)
        if r.status_code != 200:
            raise Exception("SPY API fail")
        data = r.json()
        return float(data["quote"]["ap"])
    except Exception:
        return 691.00  # fallback SPY price

def fetch_btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price",
                         params={"symbol": "BTCUSDT"}, timeout=5)
        return float(r.json()["price"])
    except Exception:
        return 84500.00  # fallback BTC price

# ───────── POLLER LOOP ─────────
def poller_loop():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with shared_lock:
            shared_prices["SPY"]["last"] = fetch_spy_price()
            shared_prices["SPY"]["updated"] = now
            shared_prices["BTC"]["last"] = fetch_btc_price()
            shared_prices["BTC"]["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT UI ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

# Start poller once
if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Initialize session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("bet", 200)
st.session_state.setdefault("fence", {"SPY": {"low": 688.0, "high": 694.0}})
st.session_state.setdefault("scoreboard", {"SPY": {"wins": 0, "losses": 0}})
st.session_state.setdefault("history", [])

# ───────── LAYOUT ─────────
branding, market = st.columns([1, 2])

# Branding column
with branding:
    st.image("redeyebatt_logo.gif", width=120)
    st.markdown("### 🧮 Scoreboard")
    for s, record in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {record['wins']} | ❌ {record['losses']}")

# Market column
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    st.session_state.bankroll = st.number_input("💰 Bankroll", value=st.session_state.bankroll, step=100.0)
    st.session_state.bet = st.number_input("💰 Bet per SPY ($)", value=st.session_state.bet, step=10)

    with shared_lock:
        prices_snapshot = {k: v.copy() for k, v in shared_prices.items()}

    for sym in TICKERS:
        data = prices_snapshot[sym]
        last = data["last"]
        updated = data["updated"]

        st.subheader(f"📊 {sym}" + (" (Heartbeat)" if sym=="BTC" else ""))
        st.write(f"{'❌ Waiting for data...' if last == 0 else f'Price: ${last:,.2f}'}")
        st.write(f"Updated: {updated if updated else '--'}")

        if sym == "SPY":
            fence = st.session_state.fence["SPY"]
            low, high = fence["low"], fence["high"]
            st.write(f"SPY fence: Low = {low} | High = {high}")

            # Optional: automatic win detection placeholder
            if low <= last <= high:
                st.success("✅ SPY inside fence (WIN placeholder)")
                # st.session_state.bankroll += st.session_state.bet
            else:
                st.error("🚨 SPY outside fence (LOSS placeholder)")
                # st.session_state.bankroll -= st.session_state.bet

    st.markdown("---")
    st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")


