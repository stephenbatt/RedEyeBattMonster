import os
import time
import threading
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 5

shared_prices = {s: {"last": 0.0, "high": 0.0, "low": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTE ─────────
def fetch_quote(symbol):
    try:
        if symbol == "BINANCE:BTCUSDT":
            r = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"},
                timeout=5
            )
            return {"c": float(r.json()["price"])}
        else:  # SPY via Finnhub
            r = requests.get(
                BASE_URL,
                params={"symbol": symbol, "token": FINNHUB_KEY},
                timeout=8
            )
            return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

# ───────── POLLER LOOP ─────────
def poller_loop():
    while True:
        for sym in TICKERS:
            data = fetch_quote(sym)
            if not data: 
                continue
            last = float(data.get("c") or 0.0)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if last <= 0: 
                continue
            with shared_lock:
                cur = shared_prices[sym]
                cur["last"] = last
                cur["high"] = last  # placeholder
                cur["low"] = last   # placeholder
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── STREAMLIT UI ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Initialize session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("history", [])
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})

# ───────── LAYOUT ─────────
branding, market = st.columns([1, 2])

# Branding column
with branding:
    st.image("logo.gif", width=120)
    st.markdown("### 🧮 Scoreboard")
    for s, record in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {record['wins']} | ❌ {record['losses']}")

# Market column
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    st.session_state.bankroll = st.number_input("💰 Bankroll




