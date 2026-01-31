import os
import time
import threading
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ───────── CONFIG ─────────
ALPACA_KEY = st.secrets.get("ALPACA_KEY", "")
ALPACA_SECRET = st.secrets.get("ALPACA_SECRET", "")
ALPACA_BASE = "https://paper-api.alpaca.markets"
TICKERS = ["SPY", "BTCUSD"]
POLL_SECONDS = 5

# Shared prices and locks
shared_prices = {s: {"last": 0.0, "high": 0.0, "low": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTES ─────────
def fetch_spy_price():
    """Fetch latest SPY price from Alpaca"""
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
        r = requests.get(f"{ALPACA_BASE}/v2/stocks/SPY/quotes/latest", headers=headers, timeout=5)
        if r.status_code != 200:
            return {}
        data = r.json()
        price = float(data["quote"]["ap"])  # Last ask price
        return {"c": price}
    except Exception:
        return {}

def fetch_btc_price():
    """Fetch BTC price from Binance"""
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
        return {"c": float(r.json()["price"])}
    except Exception:
        return {}

# ───────── FETCH 5-DAY HIGH/LOW AVERAGE ─────────
def calculate_spy_fence():
    """Fetch last 5 trading days and compute avg high/low"""
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
        end = datetime.now()
        start = end - timedelta(days=10)  # buffer for weekends/holidays
        r = requests.get(f"{ALPACA_BASE}/v2/stocks/SPY/bars",
                         params={"start": start.isoformat(), "end": end.isoformat(), "timeframe": "1Day"},
                         headers=headers,
                         timeout=8)
        if r.status_code != 200:
            return None, None
        bars = r.json()["bars"]
        last_5 = bars[-5:]
        highs = [b["h"] for b in last_5]
        lows = [b["l"] for b in last_5]
        return round(sum(highs)/len(highs), 2), round(sum(lows)/len(lows), 2)
    except Exception:
        return None, None

# ───────── POLLER LOOP ─────────
def poller_loop():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # SPY
        spy_data = fetch_spy_price()
        if spy_data:
            last = spy_data["c"]
            with shared_lock:
                cur = shared_prices["SPY"]
                cur["last"] = last
                cur["updated"] = now
        # BTC
        btc_data = fetch_btc_price()
        if btc_data:
            last = btc_data["c"]
            with shared_lock:
                cur = shared_prices["BTCUSD"]
                cur["last"] = last
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT UI ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {"SPY": {"low": None, "high": None}})
st.session_state.setdefault("scoreboard", {"SPY": {"wins": 0, "losses": 0}})

# Layout
branding, market = st.columns([1, 2])

# Branding
with branding:
    st.image("logo.gif", width=120)
    st.markdown("### 🧮 Scoreboard")
    st.write(f"SPY: ✅ {st.session_state.scoreboard['SPY']['wins']} | ❌ {st.session_state.scoreboard['SPY']['losses']}")
    st.write("BTC: ✅ heartbeat only")

# Market
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    with shared_lock:
        spy = shared_prices["SPY"].copy()
        btc = shared_prices["BTCUSD"].copy()

    # BTC Heartbeat
    st.subheader("📊 BTC-USD (Heartbeat)")
    st.write(f"Bitcoin Price: ${btc['last']:,.2f}" if btc["last"] else "❌ Waiting for BTC data...")
    st.caption(f"Updated: {btc['updated']}" if btc["updated"] else "")

    # SPY
    st.subheader("📊 SPY")
    st.write(f"SPY Price: ${spy['last']:,.2f}" if spy["last"] else "❌ Waiting for SPY data...")
    st.caption(f"Updated: {spy['updated']}" if spy["updated"] else "")

    # Auto-calculate fence (5-day avg)
    high_avg, low_avg = calculate_spy_fence()
    if high_avg and low_avg:
        st.session_state.fence["SPY"]["high"] = high_avg
        st.session_state.fence["SPY"]["low"] = low_avg
        st.markdown(f"**SPY Fence (5-day avg):** Low = {low_avg} | High = {high_avg}")

        # Check for breach
        last_price = spy["last"]
        if last_price:
            if last_price > high_avg:
                st.error(f"🚨 SPY breached the HIGH fence! Price = {last_price}")
                st.session_state.scoreboard['SPY']['losses'] += 1
            elif last_price < low_avg:
                st.error(f"🚨 SPY breached the LOW fence! Price = {last_price}")
                st.session_state.scoreboard['SPY']['losses'] += 1
            else:
                st.success(f"✅ SPY is inside the fence.")
    else:
        st.markdown("❌ Could not calculate SPY fence. Waiting for data...")

    # Bankroll
    st.session_state.bankroll = st.number_input("💰 Bankroll", value=st.session_state.bankroll, step=100.0)

st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")
 


