import os
import time
import threading
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage

# ───────── CONFIG ─────────
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "").strip()
if not FINNHUB_KEY:
    FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")

TICKERS = ["SPY", "BINANCE:BTCUSDT"]
BASE_URL = "https://finnhub.io/api/v1/quote"
POLL_SECONDS = 5

shared_prices = {s: {"last": 0.0, "high": 0.0, "low": 0.0, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── NOTIFICATIONS ─────────
def send_email_notification(subject, body):
    if not st.session_state.get("notifications_enabled", False):
        return
    try:
        email_user = st.secrets["EMAIL_USER"]
        email_pass = st.secrets["EMAIL_PASS"]
        email_to   = st.secrets["EMAIL_TO"]

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = email_user
        msg["To"] = email_to

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_user, email_pass)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Notification error: {e}")

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
                # Track high/low as the last seen value for simplicity
                cur["last"] = last
                cur["high"] = last
                cur["low"] = last
                cur["updated"] = now
        time.sleep(POLL_SECONDS)

# ───────── AUTO-FENCE RESET ─────────
def auto_reset_fences():
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 15:
            for sym in TICKERS:
                with shared_lock:
                    last = shared_prices[sym]["last"]
                    st.session_state.fence[sym]["low"] = last - 10  # default buffer
                    st.session_state.fence[sym]["high"] = last + 10
            print("Auto-fence reset executed")
            time.sleep(60)  # wait 1 min to avoid multiple resets
        time.sleep(10)

# ───────── STREAMLIT SETUP ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")

# Start poller
if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    threading.Thread(target=auto_reset_fences, daemon=True).start()
    st.session_state.poller_started = True

# Initialize session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("history", [])
st.session_state.setdefault("scoreboard", {s: {"wins": 0, "losses": 0} for s in TICKERS})
st.session_state.setdefault("notifications_enabled", False)

# ───────── LAYOUT ─────────
branding, market = st.columns([1, 2])

# Branding column
with branding:
    st.image("logo.gif", width=120)
    st.markdown("### 🧮 Scoreboard")
    for s, record in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {record['wins']} | ❌ {record['losses']}")
    st.checkbox("Enable Notifications", key="notifications_enabled")

# Market column
with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    st.session_state.bankroll = st.number_input(
        "💰 Bankroll", value=st.session_state.bankroll, step=100.0
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

        buf_key = f"buffer_{sym}"
        st.session_state.setdefault(buf_key, 10)
        buf = st.slider(f"Buffer ± points for {sym}", 0, 50, st.session_state[buf_key], key=buf_key)

        bet_key = f"bet_{sym}"
        st.session_state.setdefault(bet_key, 200)
        bet = st.number_input(f"Bet per {sym} ($)", 0, 5000, st.session_state[bet_key], key=bet_key)

        if st.button(f"Set fence around {sym}", key=f"set_{sym}"):
            st.session_state.fence[sym]["low"] = max(0.0, last - buf)
            st.session_state.fence[sym]["high"] = last + buf

        fl = st.session_state.fence[sym]["low"]
        fh = st.session_state.fence[sym]["high"]
        st.write(f"Fence: Low = {fl if fl else '--'} | High = {fh if fh else '--'}")

        # Fence breach detection + notifications
        if fl and fh and last:
            if last < fl or last > fh:
                st.error(f"🚨 {sym} breached the fence!")
                st.audio("ding-101492.mp3")
                send_email_notification(
                    f"{sym} Fence Breach!",
                    f"{sym} price {last} is outside fence {fl} - {fh}"
                )
            else:
                st.success(f"✅ {sym} is inside the fence.")

        if st.button(f"Settle {sym}", key=f"settle_{sym}"):
            win = fl <= last <= fh
            pnl = bet if win else -bet
            outcome = "WIN" if win else "LOSS"
            st.session_state.bankroll += pnl
            st.session_state.scoreboard[sym]["wins" if win else "losses"] += 1
            st.session_state.history.append({
                "Symbol": sym, "Last": last, "Low": fl, "High": fh,
                "Outcome": outcome, "PnL": pnl, "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            sound = "cash-register-kaching-sound-effect-125042.mp3" if win else "ding-101492.mp3"
            st.audio(sound)
            st.success(f"{sym} settled: {outcome} → ${pnl:.2f}")

        st.markdown("---")

# ───────── History ─────────
st.subheader("📅 Trade History")
if st.button("Reset History"):
    st.session_state.history = []
    st.success("History cleared.")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(df, use_container_width=True)
    st.download_button("📤 Export CSV", df.to_csv(index=False), "redeye_history.csv", "text/csv")

st.caption("This cockpit is paper only. No broker, no real money. Built for RedEyeBatt.")


