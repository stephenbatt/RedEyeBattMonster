import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
BASE_URL = "https://finnhub.io/api/v1/quote"
TICKERS = ["SPY", "BINANCE:BTCUSDT"]

# ───────── PRICE FETCH ─────────
def fetch_price(symbol):
    try:
        # Bitcoin (no API key needed)
        if symbol == "BINANCE:BTCUSDT":
            r = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"},
                timeout=5
            )
            return float(r.json()["price"])

        # SPY via Finnhub
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

# ───────── STREAMLIT SETUP ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})
st.session_state.setdefault("history", [])

branding, market = st.columns([1, 2])

# ───────── LEFT COLUMN ─────────
with branding:
    st.markdown("### 🧮 Scoreboard")
    for s, r in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {r['wins']} | ❌ {r['losses']}")

# ───────── MAIN COLUMN ─────────
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    st.session_state.bankroll = st.number_input(
        "💰 Bankroll", value=st.session_state.bankroll, step=100.0
    )

    for sym in TICKERS:
        st.subheader(f"📊 {sym}")

        last = fetch_price(sym)
        updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c1, c2 = st.columns(2)
        c1.metric("🎯 Last", f"{last:,.2f}" if last else "--")
        c2.caption(f"Updated: {updated}" if last else "Waiting for quote...")

        buf = st.slider(f"Buffer ± points for {sym}", 0, 50, 10, key=f"buf_{sym}")
        bet = st.number_input(
            f"Bet per {sym} ($)", 0, 5000, 200, key=f"bet_{sym}"
        )

        if st.button(f"Set fence around {sym}", key=f"set_{sym}") and last:
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

        if st.button(f"Settle {sym}", key=f"settle_{sym}") and last and fl and fh:
            win = fl <= last <= fh
            pnl = bet if win else -bet

            st.session_state.bankroll += pnl
            st.session_state.scoreboard[sym]["wins" if win else "losses"] += 1
            st.session_state.history.append({
                "Symbol": sym,
                "Price": last,
                "Low": fl,
                "High": fh,
                "Result": "WIN" if win else "LOSS",
                "PnL": pnl,
                "Time": updated
            })

            st.success(f"{'WIN' if win else 'LOSS'} → ${pnl:.2f}")

        st.markdown("---")

# ───────── HISTORY ─────────
st.subheader("📅 Trade History")

if st.button("Reset History"):
    st.session_state.history = []

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)

st.caption("Paper only. No broker. Built for RedEyeBatt.")


