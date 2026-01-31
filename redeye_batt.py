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
                "https://finnhub.io/api/v1/quote",
                params={"symbol": symbol, "token": FINNHUB_KEY},
                timeout=5
            )
            if r.status_code != 200:
                return {}
            data = r.json()
            return {
                "c": float(data.get("c") or 0.0),
                "h": float(data.get("h") or 0.0),
                "l": float(data.get("l") or 0.0)
            }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return {}
