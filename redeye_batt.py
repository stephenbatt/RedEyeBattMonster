# redeye_batt.py — Monster Cockpit
# Run: streamlit run redeye_batt.py

import os, time, threading, requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# -------- CONFIG --------
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "QQQ", "IWM", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 5

shared_prices = {s: {"last": 0.0, "high": 0.0, "low": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

def fetch_quote(symbol):
    try:
        r = requests.get(BASE_URL, params={"symbol": symbol, "token": FINNHUB_KEY}, timeout=8)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def poller_loop():
    while True:
        for sym in TICKERS:
            data = fetch_quote(sym)
            if not data: continue
            last = float(data.get("c") or 0.0)
            high = float(data.get("h") or 0.0)
            low = float(data.get("l") or 0.0)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if last <= 0: continue
            with shared_lock:
                cur = shared_prices[sym]
                cur["last"] = last
                cur["high"] = max(cur["high"], high) if cur["high"] else high
                cur["low"] = min(cur["low"], low) if cur["low"] else low
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# -------- STREAMLIT UI --------
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="centered")
st.title("🧨 RedEyeBatt Monster Cockpit")
st.caption("Live market simulator — SPY, QQQ, IWM, BTC — paper only")

if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

if "bankroll" not in st.session_state:
    st.session_state.bankroll = 10000.0
if "bet" not in st.session_state:
    st.session_state.bet = 200.0
if "fence" not in st.session_state:
    st.session_state.fence = {s: {"low": None, "high": None} for s in TICKERS}
if "history" not in st.session_state:
    st.session_state.history = []

c1, c2 = st.columns(2)
c1.metric("💰 Bankroll", f"${st.session_state.bankroll:,.2f}")
st.session_state.bet = c2.number_input("Bet per ticker ($)", 1, 5000, int(st.session_state.bet))

with shared_lock:
    prices_snapshot = {k: v.copy() for k, v in shared_prices.items()}

st.markdown("---")

for sym in TICKERS:
    data = prices_snapshot[sym]
    last, high, low, updated = data["last"], data["high"], data["low"], data["updated"]
    st.subheader(f"📊 {sym}")
    c1, c2, c3 = st.columns(3)
    c1.metric("🎯 Last", f"{last:,.2f}" if last else "--")
    c2.metric("📈 High", f"{high:,.2f}" if high else "--")
    c3.metric("📉 Low", f"{low:,.2f}" if low else "--")
    st.caption(f"Last update: {updated}" if updated else "Waiting for quote...")

    buf_key = f"buffer_{sym}"
    if buf_key not in st.session_state:
        st.session_state[buf_key] = 10
    buf = st.slider(f"Buffer ± points for {sym}", 1, 200, st.session_state[buf_key], key=buf_key)

    if st.button(f"Set fence around {sym}", key=f"set_{sym}"):
        st.session_state.fence[sym]["low"] = max(0.0, last - buf)
        st.session_state.fence[sym]["high"] = last + buf

    fl = st.session_state.fence[sym]["low"]
    fh = st.session_state.fence[sym]["high"]
    st.write(f"Fence: Low = {fl if fl else '--'} | High = {fh if fh else '--'}")

    if fl and fh and last:
        if last < fl or last > fh:
            st.error(f"🚨 {sym} breached the fence!")
        else:
            st.success(f"✅ {sym} is inside the fence.")

    st.markdown("---")

# -------- Settle & History --------
st.subheader("📅 Manual Settle")
if st.button("Settle Day"):
    total_pnl = 0.0
    rows = []
    for sym in TICKERS:
        fl = st.session_state.fence[sym]["low"]
        fh = st.session_state.fence[sym]["high"]
        last = prices_snapshot[sym]["last"]
        if fl is None or fh is None: continue
        win = fl <= last <= fh
        pnl = st.session_state.bet if win else -st.session_state.bet
        outcome = "WIN" if win else "LOSS"
        total_pnl += pnl
        rows.append({
            "Symbol": sym, "Last": last, "Low": fl, "High": fh,
            "Outcome": outcome, "PnL": pnl, "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    st.session_state.bankroll += total_pnl
    st.session_state.history.extend(rows)
    st.success(f"Settled {len(rows)} symbols → P&L: ${total_pnl:.2f}")

if st.button("Reset History"):
    st.session_state.history = []
    st.success("History cleared.")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Bankroll Over Time")
    df_chart = df.groupby("Time")["PnL"].sum().cumsum() + 10000
    fig, ax = plt.subplots()
    ax.plot(df_chart.index, df_chart.values, marker="o")
    ax.set_ylabel("Bankroll ($)")
    ax.set_xlabel("Time")
    ax.grid(True)
    st.pyplot(fig)

    st.download_button("📤 Export CSV", df.to_csv(index=False), "redeye_history.csv", "text/csv")

st.caption("This cockpit is paper only. No broker, no real money. Built for RedEyeBatt.")