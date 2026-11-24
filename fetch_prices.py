"""Download daily closes for every ticker in holdings.csv -> data/prices.csv"""
import pandas as pd
import yfinance as yf
from pathlib import Path

START = "2024-09-01"  # covers the post-election run-up too

holdings = pd.read_csv("holdings.csv")
closes = {}
for t in holdings.ticker:
    h = yf.Ticker(t).history(start=START, auto_adjust=True)
    if h.empty:
        print(f"WARN no data: {t}")
        continue
    s = h["Close"]
    s.index = s.index.tz_localize(None).normalize()
    closes[t] = s
    print(f"{t:16} {len(s):4} rows  {s.index[0].date()} -> {s.index[-1].date()}")

Path("data").mkdir(exist_ok=True)
df = pd.DataFrame(closes).sort_index()
df.index.name = "date"
df.to_csv("data/prices.csv")
print("saved data/prices.csv", df.shape)
