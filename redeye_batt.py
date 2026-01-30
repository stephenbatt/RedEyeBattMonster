import streamlit as st
import requests
from datetime import datetime
import time

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="RedEyeBatt Monster Cockpit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# SESSION STATE
# -------------------------
if "btc_price" not in st.session_state:
    st.session_state.btc_price = None
if "btc_updated" not in st.session_state:
    st.session_state.btc_updated = None
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 10000.0

# -------------------------
# HEADER / LOGO
# -------------------------
st.markdown("🧨 **RedEyeBatt Monster Cockpit**")
st.markdown("Live market simulator — paper only. You are the house.")
try:
    st.image("logo.gif", width=120)
except Exception:
    st.markdown("*Logo not available*")

# -------------------------
# SCOREBOARD & BANKROLL
# -------------------------
st.markdown("🧮 **Scoreboard**")
st.write("SPY: ✅ 0 | ❌ 0")
st.write("BINANCE:BTCUSDT: ✅ 0 | ❌ 0")
st.write(f"💰 **Bankroll:** ${st.session_state.bankroll:,.2f}")

# -------------------------
# FETCH FUNCTIONS
# -------------------------
def fetch_btc_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=5
        )
        return float(r.json()["price"])
    except Exception:
        return None

# -------------------------
# BTC SECTION (LIVE HEARTBEAT)
# -------------------------
st.markdown("📊 **BINANCE:BTCUSDT (Heartbeat)**")
btc_price = fetch_btc_price()
if btc_price:
    st.session_state.btc_price = btc_price
    st.session_state.btc_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.write(f"Price: {st.session_state.btc_price if st.session_state.btc_price else '❌ Waiting for BTC data...'}")
st.write(f"Updated: {st.session_state.btc_updated if st.session_state.btc_updated else '—'}")

btc_low = st.number_input("BTC Fence Low", min_value=0.0, max_value=1000000.0, value=0.0, step=1.0, key="btc_low")
btc_high = st.number_input("BTC Fence High", min_value=0.0, max_value=1000000.0, value=10.0, step=1.0, key="btc_high")

# -------------------------
# SPY SECTION (STATIC / PAPER)
# -------------------------
st.markdown("📊 **SPY**")
st.write("Price: ❌ Waiting for SPY data... (market closed or frozen)")

spy_buffer = st.number_input("Buffer ± points for SPY", min_value=0, max_value=50, value=0, step=1, key="buffer_SPY")
spy_bet = st.number_input("Bet per SPY ($)", min_value=0, max_value=10000, value=200, step=1, key="bet_SPY")
spy_low = st.number_input("SPY Fence Low", min_value=0.0, max_value=1000.0, value=0.0, step=0.01, key="spy_low")
spy_high = st.number_input("SPY Fence High", min_value=0.0, max_value=1000.0, value=10.0, step=0.01, key="spy_high")

# -------------------------
# TRADE HISTORY
# -------------------------
st.markdown("📅 **Trade History**")
st.write("No trades yet.")

st.markdown("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

# -------------------------
# AUTO-REFRESH LOOP (every 5 sec)
# -------------------------
st.experimental_singleton.clear()  # ensure fresh data each rerun
st.experimental_rerun()  # rerun the script to update BTC price

