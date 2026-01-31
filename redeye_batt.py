# ============================================================
# RedEyeBatt Monster Cockpit — CLEAN BASELINE (FIXED)
# BTC ONLY — REAL BINANCE DATA — STREAMLIT CLOUD SAFE
#
# PURPOSE:
# - Prove LIVE BTC data is flowing
# - BTC price must tick up/down
# - No fake data, no models, no logic yet
# ============================================================

import streamlit as st
import requests
import time
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
# BINANCE BTC PRICE FETCH (REAL LIVE DATA)
# ------------------------------------------------------------
def fetch_btc_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=5
        )
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception:
        return None

# ------------------------------------------------------------
# UI HEADER
# ------------------------------------------------------------
st.markdown("## 🧨 RedEyeBatt Monster Cockpit")
st.markdown("**Live BTC heartbeat — sanity check**")
st.markdown("---")

# ------------------------------------------------------------
# FETCH DATA
# ------------------------------------------------------------
btc_price = fetch_btc_price()
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------
st.markdown("### 📊 BINANCE:BTCUSDT")

if btc_price is None:
    st.error("❌ Waiting for BTC price from Binance...")
else:
    st.metric(
        label="BTC Last Price",
        value=f"${btc_price:,.2f}"
    )
    st.caption(f"Updated: {timestamp}")

# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------
st.markdown("---")
st.caption("Paper only • No broker • Real data • Built for RedEyeBatt")

# ------------------------------------------------------------
# HEARTBEAT — FORCE UPDATE EVERY 1 SECOND
# ------------------------------------------------------------
time.sleep(1)
st.experimental_rerun()

