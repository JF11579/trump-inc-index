"""Build the Trump Inc Index from data/prices.csv and render social-ready PNGs to plots/."""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

START = "2025-12-31"  # last close of 2025 = base 100 (Jan 1 2026 = 100)
RED, GRAY, INK, INK2, GRID, SURF = "#e34948", "#8a8985", "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
SOURCE = "Data: Yahoo Finance via yfinance · github.com/JF11579/trump-inc-index"

plt.rcParams.update({
    "text.parse_math": False,  # titles use literal $ signs
    "font.family": "DejaVu Sans", "font.size": 14, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 1, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
})

holdings = pd.read_csv("holdings.csv")
names = dict(zip(holdings.ticker, holdings.name))
basket = holdings[holdings.type.isin(["stock", "spac"])].ticker.tolist()
crypto = holdings[holdings.type == "crypto"].ticker.tolist()

prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
p = prices[prices.index >= START]
p = p[p.index.day_of_week < 5].ffill()  # trading days; crypto/Tokyo forward-filled

# Equal-weighted index, rebalanced daily: average of each holding's daily return.
# Late listings (NWAX Jan, CLBR Mar) join the average from their first trading day.
index = 100 * (1 + p[basket].pct_change().mean(axis=1).fillna(0)).cumprod()
market = 100 * p["IWV"] / p["IWV"].iloc[0]
Path("data").mkdir(exist_ok=True)
pd.DataFrame({"trump_inc_index": index, "russell_3000": market}).round(2).to_csv("data/index.csv")

out = Path("plots"); out.mkdir(exist_ok=True)
asof = p.index[-1].strftime("%b %-d, %Y")


SHORT = {"AIFC": "AI Financial (ex-ALT5 Sigma)", "DTCX": "Datacentrex (ex-Thumzup)",
         "MCGA": "Yorkville SPAC (Trump Media CRO)", "PSQH": "PSQ Holdings (PublicSquare)",
         "DJT": "Trump Media (DJT)", "NWAX": "New America Acq. I (SPAC)", "CLBR": "Colombier Acq. III (SPAC)",
         "PEW": "GrabAGun", "WLFI33251-USD": "World Liberty token (WLFI)"}
short = lambda t: SHORT.get(t, names[t])
MONTHS = plt.matplotlib.dates.DateFormatter("%b")


def header(fig, title, subtitle, h_in):
    """Title + subtitle pinned to the top-left; returns the top edge for tight_layout."""
    fig.text(0.01, 1 - 0.30 / h_in, title, fontsize=22, fontweight="bold", va="top")
    fig.text(0.01, 1 - 0.80 / h_in, subtitle, fontsize=12, color=INK2, va="top")
    return 1 - 1.15 / h_in


def footer(fig, extra=""):
    fig.text(0.01, 0.015, (extra + "\n" if extra else "") + SOURCE, fontsize=10, color=INK2, va="bottom")


# ---- 1. Index vs market -------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6.75), dpi=150)
ax.plot(market, color=GRAY, lw=2)
ax.plot(index, color=RED, lw=2.5)
ax.axhline(100, color=INK2, lw=1)
for s, c, label in [(index, RED, "Trump Inc Index"), (market, GRAY, "Russell 3000")]:
    ax.scatter(s.index[-1], s.iloc[-1], color=c, s=50, zorder=3, edgecolor=SURF, linewidth=2)
    ax.annotate(f"{label}\n{s.iloc[-1]:.0f}", (s.index[-1], s.iloc[-1]), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=13, color=INK, fontweight="bold")
ax.set_xlim(p.index[0], p.index[-1] + pd.Timedelta(days=45))
ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(bymonth=[1, 3, 5, 7, 9, 11]))
ax.set_ylim(0, max(index.max(), market.max()) * 1.1)
ax.xaxis.set_major_formatter(MONTHS)
top = header(fig, f"Trump-linked stocks have lost {100 - index.iloc[-1]:.0f}% this year",
             f"Equal-weighted index of {len(basket)} companies with Trump-family ties vs the Russell 3000 · Jan 1 2026 = 100 · through {asof}", 6.75)
footer(fig, "Basket: " + ", ".join(t.replace(".T", " (Tokyo)") for t in basket))
fig.tight_layout(rect=(0, 0.06, 1, top))
fig.savefig(out / "1_index_vs_market.png"); plt.close(fig)

# ---- 2. YTD change per holding (bar) ------------------------------------------
ytd = {t: p[t].iloc[-1] / p[t].dropna().iloc[0] - 1 for t in basket + crypto}
ytd["IWV"] = market.iloc[-1] / 100 - 1
ytd = pd.Series(ytd).sort_values()
fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
labels = ["Russell 3000 (whole US market)" if t == "IWV" else short(t) for t in ytd.index]
colors = [GRAY if t == "IWV" else RED for t in ytd.index]
bars = ax.barh(labels, ytd.values * 100, color=colors, height=0.7)
for b, v in zip(bars, ytd.values):
    ax.text(v * 100 + (-1.5 if v < 0 else 1.5), b.get_y() + b.get_height() / 2, f"{v:+.0%}",
            va="center", ha="right" if v < 0 else "left", fontsize=11, color=INK)
ax.axvline(0, color=INK2, lw=1)
ax.set_xlim(-110, 25)
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", length=0)
top = header(fig, "2026 so far: Trump-linked stocks and coins",
             f"Price change from Dec 31 2025 (or first trading day) through {asof} · gray = whole US market", 8)
footer(fig, "SPACs (NWAX, CLBR, MCGA) hold cash in trust, so they stay near $10 until a deal closes.")
fig.tight_layout(rect=(0, 0.05, 1, top))
fig.savefig(out / "2_ytd_by_holding.png"); plt.close(fig)

# ---- 3. Small multiples ------------------------------------------------------
tickers = [t for t in ytd.index if t != "IWV"]
cols = 4; rows = -(-len(tickers) // cols)
fig, axes = plt.subplots(rows, cols, figsize=(14, 3.0 * rows + 1.2), dpi=150, sharex=True, sharey=True)
for ax, t in zip(axes.flat, tickers):
    s = 100 * p[t] / p[t].dropna().iloc[0]
    ax.plot(market, color=GRAY, lw=1.5)
    ax.plot(s, color=RED, lw=2)
    ax.axhline(100, color=INK2, lw=0.8)
    ax.set_title(f"{short(t)}\n{ytd[t]:+.0%}", loc="left", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 200)
    ax.xaxis.set_major_formatter(MONTHS)
    ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.tick_params(labelsize=10)
for ax in axes.flat[len(tickers):]:
    ax.axis("off")
H = 3.0 * rows + 1.2
top = header(fig, "Each Trump-linked asset vs the market in 2026",
             "Red = asset, gray = Russell 3000 · Jan 1 2026 (or first trading day) = 100 · axis capped at 200 (AI Financial and Unusual Machines spiked higher)", H)
footer(fig)
fig.tight_layout(rect=(0, 0.03, 1, top))
fig.savefig(out / "3_small_multiples.png"); plt.close(fig)

print(f"Index {index.iloc[-1]:.1f} | Russell 3000 {market.iloc[-1]:.1f} | as of {asof}")
print(ytd.map("{:+.0%}".format).to_string())
