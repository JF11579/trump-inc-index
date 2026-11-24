"""Trump Inc Index across the second term: Jan 17 2025 (last close before the Jan 20 inauguration) = 100.

Each company joins the index on the day its Trump-family tie became public (holdings.csv `joins_index`),
so pre-tie price history (e.g. a SPAC shell before a merger) never counts.
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from make_charts import INK, INK2, RED, GRAY, SURF, header, footer, short  # reuse styling

BASE = "2025-01-17"
h = pd.read_csv("holdings.csv")
stocks = h[h.type.isin(["stock", "spac"])]
joins = dict(zip(stocks.ticker, pd.to_datetime(stocks.joins_index)))

prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
p = prices[(prices.index >= BASE) & (prices.index.day_of_week < 5)].ffill()

rets = p[list(joins)].pct_change()
for t, d in joins.items():
    rets.loc[rets.index <= d, t] = float("nan")  # a member's returns count only after it joins


def build(cols):
    return 100 * (1 + rets[cols].mean(axis=1).fillna(0)).cumprod()


index = build(list(joins))
no_spac = build(stocks[stocks.type == "stock"].ticker.tolist())
market = 100 * p["IWV"] / p["IWV"].iloc[0]
pd.DataFrame({"trump_inc_index": index, "ex_spacs": no_spac, "russell_3000": market}).round(2).to_csv("data/index_term.csv")

fig, ax = plt.subplots(figsize=(12, 6.75), dpi=150)
ax.axhline(100, color=INK2, lw=1)
ax.plot(market, color=GRAY, lw=2)
ax.plot(index, color=RED, lw=2.5)
for s, c, label in [(index, RED, "Trump Inc Index"), (market, GRAY, "Russell 3000")]:
    ax.scatter(s.index[-1], s.iloc[-1], color=c, s=50, zorder=3, edgecolor=SURF, linewidth=2)
    ax.annotate(f"{label}\n{s.iloc[-1]:.0f}", (s.index[-1], s.iloc[-1]), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=13, color=INK, fontweight="bold")
pk = index.idxmax()
# rug of join dates along the bottom
for t, d in joins.items():
    if d > pd.Timestamp(BASE):
        ax.plot([d, d], [0, 5], color=INK2, lw=1)
ax.text(pd.Timestamp(BASE) + pd.Timedelta(days=4), 7, "| = company joins the index as its Trump tie is announced",
        fontsize=10, color=INK2)
ax.set_ylim(0, max(index.max(), market.max()) * 1.15)
ax.set_xlim(p.index[0], p.index[-1] + pd.Timedelta(days=75))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

asof = p.index[-1].strftime("%b %-d, %Y")
top = header(fig, f"Since inauguration day: Trump Inc {index.iloc[-1] - 100:+.0f}%, US market {market.iloc[-1] - 100:+.0f}%",
             f"Equal-weighted index of Trump-family-linked stocks vs the Russell 3000 · Jan 17 2025 = 100 · through {asof}", 6.75)
footer(fig, f"Without the 3 SPACs (cash in trust, ~flat): {no_spac.iloc[-1]:.0f}. Members: "
            + ", ".join(t.replace(".T", "") for t in joins))
fig.tight_layout(rect=(0, 0.06, 1, top))
Path("plots").mkdir(exist_ok=True)
fig.savefig("plots/4_since_inauguration.png")

print(f"index {index.iloc[-1]:.1f}  ex-SPAC {no_spac.iloc[-1]:.1f}  market {market.iloc[-1]:.1f}  peak {index.max():.1f} on {pk.date()}")
print(index.resample("QE").last().round(0).to_string())
