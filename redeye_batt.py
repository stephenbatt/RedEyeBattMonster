import streamlit as st
import requests
import time
from datetime import datetime

# -------------------------
# CONFIGURATION
# -------------------------
st.set_page_config(
    page_title="RedEyeBatt Monster Cockpit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# APP STATE
# -------------------------
if "btc_price" not in st.session_state:
    st.session_state.btc_price = None
if "btc_updated" not in st.session_state:
    st.session_state.btc_updated = None

# Placeholder for scoreboard, bankroll, and SPY data remain untouched
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 10000.0

# -------------------------
# UI HEADER
# -------------------------
st.markdown("🧨 **RedEyeBatt Monster Cockpit**")
st.markdown("Live market simulator — paper only. You are the house.")

# -------------------------
# SCOREBOARD
# -------------------------
st.markdown("🧮 **Scoreboard**")
col1, col2 = st.columns(2)
with col1:
    st.write("SPY: ✅ 0 | ❌ 0")
with col2:
    st.write("BINANCE:BTCUSDT: ✅ 0 | ❌ 0")

st.markdown(f"💰 **Bankroll:** ${st.session_state.bankroll:,.2f}")

# -------------------------
# SPY SECTION (LEFT ALONE)
# -------------------------
st.markdown("📊 **SPY**")
st.write("Price: ❌ Waiting for data...")
st.write("Updated: —")
st.slider("Buffer ± points for SPY", 0, 50, 0, key="buffer_SPY")
st.number_input("Bet per SPY ($)", value=200, key="bet_SPY")
st.number_input("SPY Fence Low", value=0.0, key="spy_fence_low")
st.number_input("SPY Fence High", value=10.0, key="spy_fence_high")

# -------------------------
# BTC SECTION (HEARTBEAT LIVE)
# -------------------------
st.markdown("📊 **BINANCE:BTCUSDT (Heartbeat)**")
btc_col1, btc_col2 = st.columns(2)
btc_price_placeholder = btc_col1.empty()
btc_updated_placeholder = btc_col2.empty()

st.slider("Buffer ± points for BINANCE:BTCUSDT", 0, 50, 0, key="buffer_BTC")
st.number_input("Bet per BINANCE:BTCUSDT ($)", value=200, key="bet_BTC")
st.number_input("BINANCE:BTCUSDT Fence Low", value=0.0, key="btc_fence_low")
st.number_input("BINANCE:BTCUSDT Fence High", value=10.0, key="btc_fence_high")

# -------------------------
# TRADE HISTORY
# -------------------------
st.markdown("📅 Trade History")
st.write("No trades yet.")

st.markdown("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

# -------------------------
# FUNCTION TO FETCH BTC PRICE
# -------------------------
def fetch_btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
        price = float(r.json()["price"])
        return price
    except Exception:
        return None

# -------------------------
# LIVE UPDATE LOOP (HEARTBEAT)
# -------------------------
def update_btc():
    btc_price = fetch_btc_price()
    if btc_price:
        st.session_state.btc_price = btc_price
        st.session_state.btc_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        btc_price_placeholder.write(f"Price: ${btc_price:,.2f}")
        btc_updated_placeholder.write(f"Updated: {st.session_state.btc_updated}")
    else:
        btc_price_placeholder.write("Price: ❌ Waiting for BTC data...")
        btc_updated_placeholder.write("Updated: —")

# Run once on page load
update_btc()

# Auto-refresh every 5 seconds for BTC heartbeat
st.experimental_set_query_params(_ts=int(time.time()))
st.experimental_rerun()
