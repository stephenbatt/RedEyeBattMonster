# ============================================================
# RedEyeBatt Monster Cockpit — BTC LIVE HEARTBEAT (FINAL)
# Streamlit Cloud SAFE — No deprecated calls
# ============================================================

import streamlit as st
import requests
import time
from datetime import datetime

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="RedEyeBatt Monster Cockpit",
    page_icon="🦇",
    layout="centered"
)

# ------------------------------------------------------------
# LIVE BTC PRICE (COINBASE — WORKS ON STREAMLIT CLOUD)
# ------------------------------------------------------------
def fetch_btc_price():
    try:
        r = requests.get(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot",
            timeout=5
        )
        r.raise_for_status()
        return float(r.json()["data"]["amount"])
    except Exception:
        return None

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.markdown("## 🧨 RedEyeBatt Monster Cockpit")
st.markdown("**Live BTC price — data sanity check**")
st.markdown("---")

btc_price = fetch_btc_price()
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown("### 📊 BTC-USD")

if btc_price is None:
    st.error("❌ Waiting for BTC data...")
else:
    st.metric("BTC Price", f"${btc_price:,.2f}")
    st.caption(f"Updated: {timestamp}")

st.markdown("---")
st.caption("Paper only • No broker • Real data • Built for RedEyeBatt")

# ------------------------------------------------------------
# AUTO REFRESH (CORRECT FOR NEW STREAMLIT)
# ------------------------------------------------------------
time.sleep(1)
st.rerun()
