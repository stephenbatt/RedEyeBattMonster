import threading
import time
from datetime import datetime
import requests
import streamlit as st

# ───────── CONFIG ─────────
FINNHUB_KEY = st.secrets.get("FINNHUB_KEY", "")
TICKERS = ["SPY", "BINANCE:BTCUSDT"]
POLL_SECONDS = 5

# ───────── SHARED STATE ─────────
shared_prices = {s: {"last": None, "high": None, "low": None, "updated": None} for s in TICKERS}
shared_lock = threading.Lock()

# ───────── FETCH QUOTES ─────────
def fetch_quote(symbol):
    try:
        if symbol == "BINANCE:BTCUSDT":
            r = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"},
                timeout=5
            )
            price = float(r.json()["price"])
            return {"c": price, "h": price, "l": price}
        else:  # SPY via Finnhub
            r = requests.get(
                f"https://finnhub.io/api/v1/quote",
                params={"symbol": symbol, "token": FINNHUB_KEY},
                timeout=5
            )
            if r.status_code != 200:
                return {}
            data = r.json()
            return {"c": float(data.get("c", 0)), "h": float(data.get("h", 0)), "l": float(data.get("l", 0))}
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return {}

# ───────── POLLER THREAD ─────────
def poller_loop():
    while True:
        try:
            for sym in TICKERS:
                data = fetch_quote(sym)
                if not data:
                    continue
                with shared_lock:
                    shared_prices[sym]["last"] = data["c"]
                    shared_prices[sym]["high"] = data.get("h", data["c"])
                    shared_prices[sym]["low"] = data.get("l", data["c"])
                    shared_prices[sym]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(POLL_SECONDS)
        except Exception as e:
            print(f"Poller crashed: {e}")
            time.sleep(POLL_SECONDS)

# ───────── STREAMLIT SETUP ─────────
st.set_page_config(page_title="🧨 RedEyeBatt Monster Cockpit", layout="wide")
if "poller_started" not in st.session_state:
    threading.Thread(target=poller_loop, daemon=True).start()
    st.session_state.poller_started = True

# Session state
st.session_state.setdefault("bankroll", 10000.0)
st.session_state.setdefault("buffer", {s: 0 for s in TICKERS})
st.session_state.setdefault("bet", {s: 200 for s in TICKERS})
st.session_state.setdefault("fence", {s: {"low": None, "high": None} for s in TICKERS})
st.session_state.setdefault("scoreboard", {s: {"wins":0,"losses":0} for s in TICKERS})
st.session_state.setdefault("history", [])

# ───────── LAYOUT ─────────
branding, market = st.columns([1,2])

with branding:
    # Replace with your actual file if small enough
    st.image("logo.gif", width=120)
    st.markdown("### 🧮 Scoreboard")
    for s, rec in st.session_state.scoreboard.items():
        st.write(f"{s}: ✅ {rec['wins']} | ❌ {rec['losses']}")
    st.markdown(f"💰 Bankroll: ${st.session_state.bankroll:,.2f}")

with market:
    st.title("🧨 RedEyeBatt Monster Cockpit")
    st.caption("Live market simulator — paper only. You are the house.")

    for sym in TICKERS:
        st.markdown(f"📊 {sym} {'(Heartbeat)' if sym=='BINANCE:BTCUSDT' else ''}")
        last = shared_prices[sym]["last"]
        updated = shared_prices[sym]["updated"]
        st.write("Price:", f"${last:,.2f}" if last else "❌ Waiting for data...")
        st.write("Updated:", updated if updated else "—")

        buffer_val = st.slider(f"Buffer ± points for {sym}", 0, 50, key=f"buffer_{sym}")
        st.session_state.buffer[sym] = buffer_val

        bet_val = st.number_input(f"Bet per {sym} ($)", min_value=1, max_value=10000, value=st.session_state.bet[sym], key=f"bet_{sym}")
        st.session_state.bet[sym] = bet_val

        low = st.number_input(f"{sym} Fence Low", value=st.session_state.fence[sym]["low"] if st.session_state.fence[sym]["low"] else 0.0, key=f"fence_low_{sym}")
        high = st.number_input(f"{sym} Fence High", value=st.session_state.fence[sym]["high"] if st.session_state.fence[sym]["high"] else 10.0, key=f"fence_high_{sym}")
        st.session_state.fence[sym]["low"] = low
        st.session_state.fence[sym]["high"] = high

    st.markdown("📅 Trade History")
    if not st.session_state.history:
        st.write("No trades yet.")
    else:
        st.table(st.session_state.history)

st.markdown("Paper trading only • No broker • Real market data • Built for RedEyeBatt")

