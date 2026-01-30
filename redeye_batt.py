# ============================================================
# RedEyeBatt Monster Cockpit — HARD RESET VERSION
# BTC ONLY — REAL DATA — NO PAPER LOGIC YET
#
# PURPOSE:
# - Prove live data is flowing
# - BTC price must tick up/down in real time
# - No fences, no betting, no score logic
#
# If this does NOT move, the problem is NOT our code.
# ============================================================

import streamlit as st
import requests
from datetime import datetime

# ------------------------------------------------------------
# STREAMLIT PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="RedEyeBatt Monster Cockpit",
    page_icon="🦇",
    layout="centered"
)

# ------------------------------------------------------------
# AUTO REFRESH (THIS IS THE HEARTBEAT)
# Every 1 second Streamlit reruns the script
# ------------------------------------------------------------
st.experimental_set_query_params()

# ------------------------------------------------------------
# BINANCE BTC PRICE FETCH (REAL, LIVE)
# ------------------------------------------------------------
def fetch_btc_price():
    """
    Pulls LIVE BTCUSDT price directly from Binance.
    This endpoint updates constantly.
    """
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=5
        )
        data = r.json()
        return float(data["price"])
    except Exception as e:
        return None


# ------------------------------------------------------------
# UI HEADER
# ------------------------------------------------------------
st.markdown("## 🧨 RedEyeBatt Monster Cockpit")
st.markdown("**Live BTC price — data sanity check**")
st.markdown("---")

# ------------------------------------------------------------
# FETCH PRICE
# ------------------------------------------------------------
btc_price = fetch_btc_price()
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------
st.markdown("### 📊 BINANCE:BTCUSDT")

if btc_price is None:
    st.error("❌ Waiting for BTC data...")
else:
    st.metric(
        label="BTC Last Price",
        value=f"${btc_price:,.2f}"
    )
    st.caption(f"Updated: {now}")

# ------------------------------------------------------------
# FOOTER / DEBUG INFO
# ------------------------------------------------------------
st.markdown("---")
st.caption(
    "Paper trading only • No broker • No fake data • Built for RedEyeBatt"
)

# ------------------------------------------------------------
# FORCED REFRESH (1 SECOND TICK)
# ------------------------------------------------------------
import time
time.sleep(1)
st.experimental_rerun()

