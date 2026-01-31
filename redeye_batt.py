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
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
ALERT_SOUND = "ding-101492.mp3"  # add this file to your project
DEFAULT_BET = 200

# Shared prices and locks
shared_prices = {s: {"last": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTES ─────────
def fetch_spy_price():
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
        r = requests.get(f"{ALPACA_BASE}/v2/stocks/SPY/quotes/latest", headers=headers, timeout=5)
        if r.status_code != 200: return {}
        data = r.json()
        return {"c": float(data["quote"]["ap"])}
    except Exception:
        return {}

def fetch_btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
        return {"c": float(r.json()["price"])}
    except Exception:
        return {}

# ───────── 5-DAY AVERAGE ─────────
def calculate_spy_fence():
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
        end = datetime.now()
        start = end - timedelta(days=10)
        r = requests.get(f"{ALPACA_BASE}/v2/stocks/SPY/bars",
                         params={"start": start.isoformat(), "end": end.isoformat(), "timeframe": "1Day"},
                         headers=headers, timeout=8)
        if r.status_code != 200: return None, None
        bars = r.json()["bars"][-5:]  # last 5 trading days
        highs = [b["h"] for b in bars]
        lows = [b["l"] for b in bars]
        return round(sum(highs)/len(highs), 2), round(sum(lows)/len(lows), 2)
    except Exception:
        return None, None

# ───────── POLLER LOOP ─────────
def poller_loop():
    fence_reset_done = False
    while True:
        now = datetime.now()
        # Auto-reset fence at market open
        if not fence_reset_done and now.hour == MARKET_OPEN_HOUR and now.minute >= MARKET_OPEN_MINUTE:
            high_avg, low_avg = calculate_spy_fence()
            if high_avg and low_avg:
                st.session_state.fence["SPY"]["high"] = high_avg
                st.session_state.fence["SPY"]["low"] = low_avg
                fence_reset_done = True

        # SPY
        spy_data = fetch_spy_price()
        if spy_data:
            last = spy_data["c"]
            with shared_lock:
                cur = shared_prices["SPY"]
                cur["last"] = last
                cur["updated"] = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # BTC
        btc_data = fetch_btc_price()
        if btc_data:
            last = btc_data["c"]
            with shared_lock:
                cur = shared_prices["BTCUSD"]
                cur["last"] = last
                cur["updated"] = now.strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT UI ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Initialize session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {"SPY": {"low": None, "high": None}})
st.session_state.setdefault("scoreboard", {"SPY": {"wins": 0, "losses": 0}})
st.session_state.setdefault("bet", DEFAULT_BET)
st.session_state.setdefault("history", [])

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

    # Set manual bet
    st.session_state.bet = st.number_input("💰 Bet per SPY ($)", value=st.session_state.bet, step=50)

    # SPY Fence
    fl = st.session_state.fence["SPY"]["low"]
    fh = st.session_state.fence["SPY"]["high"]
    if fl and fh:
        st.markdown(f"**SPY Fence:** Low = {fl} | High = {fh}")
        last_price = spy["last"]
        if last_price:
            # Breach auto-settle
            if last_price > fh or last_price < fl:
                st.error(f"🚨 SPY breached the fence! Price = {last_price}")
                st.session_state.bankroll -= st.session_state.bet
                st.session_state.scoreboard['SPY']['losses'] += 1
                st.session_state.history.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Symbol": "SPY",
                    "Price": last_price,
                    "Outcome": "LOSS",
                    "PnL": -st.session_state.bet
                })
                st.audio(ALERT_SOUND)
            else:
                st.success(f"✅ SPY is inside the fence.")
    else:
        st.markdown("❌ SPY fence not set yet.")

    # Bankroll
    st.number_input("💰 Bankroll", value=st.session_state.bankroll, step=100.0)

# Trade history
if st.session_state.history:
    st.subheader("📅 Trade History")
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)
    st.download_button("📤 Export CSV", df.to_csv(index=False), "redeye_history.csv", "text/csv")

st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

