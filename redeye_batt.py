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
                # keep high/low updated over session
                cur["high"] = max(cur["high"], last) if cur["high"] else last
                cur["low"] = min(cur["low"], last) if cur["low"] else last
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

    st.session_state.bankroll = st.number_input(
        "💰 Bankroll",
        value=st.session_state.bankroll,
        step=100.0
    )

    with shared_lock:
        prices_snapshot = {k: v.copy() for k, v in shared_prices.items()}

    for sym in TICKERS:
        data = prices_snapshot[sym]
        last, high, low, updated = data["last"], data["high"], data["low"], data["updated"]

        st.subheader(f"📊 {sym}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 Last", f"{last:,.2f}" if last else "--")
        c2.metric("📈 High", f"{high:,.2f}" if high else "--")
        c3.metric("📉 Low", f"{low:,.2f}" if low else "--")
        st.caption(f"Last update: {updated}" if updated else "Waiting for quote...")

        # Buffer slider
        buf_key = f"buffer_{sym}"
        st.session_state.setdefault(buf_key, 10)
        buf = st.slider(f"Buffer ± points for {sym}", 0, 50, st.session_state[buf_key], key=buf_key)

        # Bet input
        bet_key = f"bet_{sym}"
        st.session_state.setdefault(bet_key, 200)
        bet = st.number_input(f"Bet per {sym} ($)", 0, 5000, st.session_state[bet_key], key=bet_key)

        # Set fence
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

        # Settle bet
        if st.button(f"Settle {sym}", key=f"settle_{sym}"):
            win = fl <= last <= fh
            pnl = bet if win else -bet
            outcome = "WIN" if win else "LOSS"
            st.session_state.bankroll += pnl
            st.session_state.scoreboard[sym]["wins" if win else "losses"] += 1
            st.session_state.history.append({
                "Symbol": sym,
                "Last": last,
                "Low": fl,
                "High": fh,
                "Outcome": outcome,
                "PnL": pnl,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            sound = "cash-register-kaching-sound-effect-125042.mp3" if win else "ding-101492.mp3"
            st.audio(sound)
            st.success(f"{sym} settled: {outcome} → ${pnl:.2f}")

        st.markdown("---")

# ───────── History & Chart ─────────
st.subheader("📅 Trade History")
if st.button("Reset History"):
    st.session_state.history = []
    st.success("History cleared.")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Bankroll Over Time")
    df_chart = df.groupby("Time")["PnL"].sum().cumsum() + st.session_state.bankroll
    fig, ax = plt.subplots()
    ax.plot(df_chart.index, df_chart.values, marker="o")
    ax.set_ylabel("Bankroll ($)")
    ax.set_xlabel("Time")
    ax.grid(True)
    st.pyplot(fig)

    st.download_button("📤 Export CSV", df.to_csv(index=False), "redeye_history.csv", "text/csv")

st.caption("This cockpit is paper only. No broker, no real money. Built for RedEyeBatt.")


