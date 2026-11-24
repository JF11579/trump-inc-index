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

W, H = 16, 8
fig = plt.figure(figsize=(W, H), dpi=150)
gs = fig.add_gridspec(1, 2, width_ratios=[1.75, 1], wspace=0.10)
ax, tab = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
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
ax.set_xlim(p.index[0], p.index[-1] + pd.Timedelta(days=120))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

asof = p.index[-1].strftime("%b %-d, %Y")
# ---- members panel: who is "Trump Inc", when they joined, change since joining
TIE = {"DJT": "Trump: largest shareholder", "PSQH": "Don Jr: board", "UMAC": "Don Jr: adviser, shareholder",
       "DOMH": "Don Jr & Eric: advisers, >10% owners", "3350.T": "Eric: adviser", "DTCX": "Don Jr: shareholder",
       "PEW": "Don Jr: board", "MCGA": "Trump Media crypto deal", "AIFC": "Eric: adviser (WLFI tokens)",
       "ABTC": "Eric: co-founder; Don Jr: stake", "MMA": "Don Jr: adviser", "NWAX": "Don Jr & Eric: advisers",
       "CLBR": "Don Jr: board"}
tab.axis("off")
tab.set_xlim(0, 1); tab.set_ylim(0, 1)
rows = sorted(joins, key=lambda t: joins[t])
tab.text(0, 1.0, "The 13 members of Trump Inc", fontsize=14, fontweight="bold", va="top")
tab.text(0.70, 0.945, "joined", fontsize=10, color=INK2, ha="right", va="top")
tab.text(1.0, 0.945, "since\njoining", fontsize=10, color=INK2, ha="right", va="top")
step = 0.88 / len(rows)
for i, t in enumerate(rows):
    y = 0.88 - i * step
    s_ = p[t].dropna()
    chg = s_.iloc[-1] / s_.loc[:joins[t]].iloc[-1] - 1 if joins[t] >= s_.index[0] else s_.iloc[-1] / s_.iloc[0] - 1
    tab.text(0, y, {"MCGA": "Yorkville SPAC (MCGA)"}.get(t, short(t)), fontsize=11.5, fontweight="bold", va="top", color=INK)
    tab.text(0, y - 0.028, TIE[t], fontsize=9.5, va="top", color=INK2)
    tab.text(0.70, y, ("Day 1" if joins[t] <= pd.Timestamp(BASE) else joins[t].strftime("%b %Y")), fontsize=11, va="top", ha="right", color=INK2)
    tab.text(1.0, y, ("0%" if round(chg, 2) == 0 else f"{chg:+.0%}"), fontsize=12, va="top", ha="right", color=INK, fontweight="bold")
    if i:
        tab.plot([0, 1], [y + 0.012, y + 0.012], color="#e6e5e1", lw=1)

top = header(fig, f"Since inauguration day: Trump Inc {index.iloc[-1] - 100:+.0f}%, US market {market.iloc[-1] - 100:+.0f}%",
             f"Equal-weighted index of Trump-family-linked stocks vs the Russell 3000 · Jan 17 2025 = 100 · through {asof}", H)
footer(fig, f"Without the 3 SPACs (cash in trust, ~flat) the index is at {no_spac.iloc[-1]:.0f}. "
            "DJT, PSQH and UMAC ties predate the inauguration; the rest join on announcement.")
fig.subplots_adjust(left=0.05, right=0.985, top=top - 0.02, bottom=0.14)
Path("plots").mkdir(exist_ok=True)
fig.savefig("plots/4_since_inauguration.png")

print(f"index {index.iloc[-1]:.1f}  ex-SPAC {no_spac.iloc[-1]:.1f}  market {market.iloc[-1]:.1f}  peak {index.max():.1f} on {pk.date()}")
print(index.resample("QE").last().round(0).to_string())
