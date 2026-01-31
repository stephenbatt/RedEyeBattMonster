import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="RedEyeBatt Monster Cockpit", layout="wide")

st.title("🧨 RedEyeBatt Monster Cockpit")
st.caption("Live market simulator — paper only. You are the house.")

# -------------------------
# SESSION STATE INIT
# -------------------------
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 10000.00

# -------------------------
# DATA FETCH (NO CACHE, NO RERUN)
# -------------------------
def get_btc_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=5
        )
        data = r.json()
        return float(data["price"]), datetime.now()
    except Exception:
        return None, None

# -------------------------
# SCOREBOARD
# -------------------------
st.markdown("### 🧮 Scoreboard")
st.write("SPY: ✅ 0 | ❌ 0")
st.write("BINANCE:BTCUSDT: heartbeat only")

st.markdown("---")

# -------------------------
# BANKROLL
# -------------------------
st.markdown("### 💰 Bankroll")
st.metric("Balance", f"${st.session_state.bankroll:,.2f}")

st.markdown("---")

# -------------------------
# BTC HEARTBEAT
# -------------------------
st.markdown("### 📊 BINANCE:BTCUSDT (Heartbeat)")

price, ts = get_btc_price()

if price is None:
    st.error("❌ Waiting for BTC data...")
else:
    st.metric("BTC Price", f"${price:,.2f}")
    st.caption(f"Updated: {ts.strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")

# -------------------------
# SPY PLACEHOLDER (DO NOT TOUCH)
# -------------------------
st.markdown("### 📊 SPY")
st.caption("Market closed or inactive")
st.write("Price: ❌ Waiting for SPY data...")

st.markdown("---")

st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")


