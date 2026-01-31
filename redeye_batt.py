import os
import time
import requests
import streamlit as st
from datetime import datetime

# ───────── CONFIG ─────────
st.set_page_config(
    page_title="🧨 RedEyeBatt Monster Cockpit",
    layout="wide"
)

FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
BASE_URL = "https://finnhub.io/api/v1/quote"

REFRESH_SECONDS = 5

# ───────── DATA FETCH ─────────
def fetch_btc():
    try:
        r = requests.get(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot",
            timeout=5
        )
        price = float(r.json()["data"]["amount"])
        return price
    except Exception:
        return None

def fetch_spy():
    try:
        r = requests.get(
            BASE_URL,
            params={"symbol": "SPY", "token": FINNHUB_KEY},
            timeout=8
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return float(data.get("c") or 0.0)
    except Exception:
        return None

# ───────── HEADER / BRANDING ─────────
left, right = st.columns([1, 3])

with left:
    st.image("logo.gif", width=130)

with right:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

st.markdown("---")

# ───────── MARKET DATA ─────────
btc_price = fetch_btc()
spy_price = fetch_spy()
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

col1, col2 = st.columns(2)

# ───── BTC (Heartbeat) ─────
with col1:
    st.subheader("📊 BTC-USD (Heartbeat)")
    if btc_price:
        st.metric("Bitcoin Price", f"${btc_price:,.2f}")
        st.caption(f"Updated: {now}")
    else:
        st.error("Waiting for BTC data...")

# ───── SPY ─────
with col2:
    st.subheader("📊 SPY")
    if spy_price and spy_price > 0:
        st.metric("SPY Price", f"${spy_price:,.2f}")
        st.caption(f"Updated: {now}")
    else:
        st.warning("Waiting for SPY quote...")

st.markdown("---")
st.caption("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

# ───────── REFRESH LOOP ─────────
time.sleep(REFRESH_SECONDS)
st.rerun()


