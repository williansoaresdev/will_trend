import requests
from pathlib import Path

def load_api_key(filename="polygon.txt"):
    key_path = Path(__file__).parent / filename
    if not key_path.exists():
        raise FileNotFoundError(f"Arquivo '{filename}' não encontrado.")
    key = key_path.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError(f"Arquivo '{filename}' está vazio.")
    return key

API_KEY = load_api_key()

def get_stock_snapshot(ticker):
    url = f"https://api.massive.com/v3/reference/tickers/{ticker}"
    params = {"apiKey": API_KEY}
    r = requests.get(url, params=params)
    r.raise_for_status()
    print(r.json())
    data = r.json()["ticker"]
    return data["day"]["c"], data["min"]["c"]

def get_forex_snapshot(pair):
    url = f"https://api.polygon.io/v2/snapshot/locale/global/markets/forex/tickers/C:{pair}"
    params = {"apiKey": API_KEY}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()["ticker"]
    return data["lastQuote"]["b"], data["lastQuote"]["a"]

close_meta, last_meta = get_stock_snapshot("META")
print(f"META - fechamento: ${close_meta:.2f} | último: ${last_meta:.2f}")

#bid, ask = get_forex_snapshot("EURUSD")
#print(f"EUR/USD - bid: {bid:.5f} | ask: {ask:.5f}")