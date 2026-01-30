import os
import time
import threading
import requests
import streamlit as st
from datetime import datetime

# ================= CONFIG =================
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 5

shared_prices = {
    s: {"last": None, "updated": None} for s in TICKERS
}
shared_lock = threading.Lock()

# ================= DATA =================
def fetch_price(symbol):
    try:
        r = requests.get(
            BASE_URL,
            params={"symbol": symbol, "token": FINNHUB_KEY},
            timeout=8
        )
        if r.status_code != 200:
            return None
        return float(r.json().get("c") or 0)
    except Exception:
        return None

def poller_loop():
    while True:
        for sym in TICKERS:
            price = fetch_price(sym)
            if not price:
                continue
            with shared_lock:
                shared_prices[sym]["last"] = price
                shared_prices[sym]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(POLL_SECONDS)

# ================= STREAMLIT =================
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})

branding, market = st.columns([1, 2])

# ================= LEFT COLUMN =================
with branding:
    try:
        st.image("logo.gif", width=140)
    except:
        st.markdown("### 🦇 RedEyeBatt")

    st.markdown("### 🧮 Scoreboard")
    for s, r in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {r['wins']} | ❌ {r['losses']}")

# ================= MAIN COLUMN =================
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    st.session_state.bankroll = st.number_input(
        "💰 Bankroll",
        value=st.session_state.bankroll,
        step=100.0
    )

    with shared_lock:
        prices = {k: v.copy() for k, v in shared_prices.items()}

    for sym in TICKERS:
        st.markdown("---")
        st.subheader(f"📊 {sym}")

        last = prices[sym]["last"]
        updated = prices[sym]["updated"]

        if last:
            st.metric("🎯 Last", f"{last:,.2f}")
            st.caption(f"Updated: {updated}")
        else:
            st.info("Waiting for quote...")

        buf = st.slider(
            f"Buffer ± points for {sym}",
            min_value=0,
            max_value=50,
            value=10,
            key=f"buf_{sym}"
        )

        bet = st.number_input(
            f"Bet per {sym} ($)",
            min_value=0,
            max_value=5000,
            value=200,
            key=f"bet_{sym}"
        )

        if st.button(f"Set fence for {sym}", key=f"set_{sym}") and last:
            st.session_state.fence[sym]["low"] = last - buf
            st.session_state.fence[sym]["high"] = last + buf

        fl = st.session_state.fence[sym]["low"]
        fh = st.session_state.fence[sym]["high"]

        st.write(f"Fence: Low = {fl if fl else '--'} | High = {fh if fh else '--'}")

        if last and fl and fh:
            if last < fl or last > fh:
                st.error("🚨 Fence breached")
            else:
                st.success("✅ Inside fence")

# ================= FOOTER =================
st.markdown("---")
st.caption("Paper trading only. No broker. No real money. Built for RedEyeBatt.")

