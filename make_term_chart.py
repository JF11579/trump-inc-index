"""Second-term chart: $100 into each Trump-linked company on the day its tie was announced,
vs the same $100 put into small-company stocks (iShares IWC, Russell Microcap) on the same day.

DJT, PSQH and UMAC ties predate the inauguration, so they are bought at the Jan 17 2025 close
(last close before the Jan 20 inauguration). Every other company is bought at the close on its
announcement date (holdings.csv `joins_index`). No rebalancing: each $100 just rides.
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from make_charts import INK, INK2, RED, GRAY, SURF, header, footer, short  # reuse styling

BASE = pd.Timestamp("2025-01-17")
STAKE = 100

h = pd.read_csv("holdings.csv")
stocks = h[h.type.isin(["stock", "spac"])]
joins = {t: max(pd.Timestamp(d), BASE) for t, d in zip(stocks.ticker, stocks.joins_index)}
spacs = set(stocks[stocks.type == "spac"].ticker)

prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
p = prices[(prices.index >= BASE) & (prices.index.day_of_week < 5)].ffill()


def entry_price(s, d):
    return s.loc[:d].dropna().iloc[-1]


def position(ticker, join):
    """Dollar value over time of $100 put into `ticker` at the close on `join` (0 before)."""
    s = p[ticker]
    return (STAKE * s / entry_price(s, join)).where(p.index >= join, 0.0)


trump_pos = {t: position(t, d) for t, d in joins.items()}
small_pos = {t: position("IWC", d) for t, d in joins.items()}   # matched $100 on the same day
whole_pos = {t: position("IWV", d) for t, d in joins.items()}
trump, small, whole = (pd.DataFrame(x).sum(axis=1) for x in (trump_pos, small_pos, whole_pos))
invested = pd.DataFrame({t: (p.index >= d) * STAKE for t, d in joins.items()}, index=p.index).sum(axis=1)

ex = [t for t in joins if t not in spacs]
trump_ex = sum(trump_pos[t].iloc[-1] for t in ex)
small_ex = sum(small_pos[t].iloc[-1] for t in ex)

pd.DataFrame({"invested": invested, "trump_portfolio": trump, "small_cap_portfolio": small,
              "whole_market_portfolio": whole}).round(2).to_csv("data/portfolio_term.csv")

# ---- figure ------------------------------------------------------------------
W, H = 16, 9
fig = plt.figure(figsize=(W, H), dpi=150)
gs = fig.add_gridspec(1, 2, width_ratios=[1.75, 1], wspace=0.10)
ax, tab = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

ax.step(invested.index, invested, where="post", color=INK2, lw=1.2, ls=(0, (4, 3)))
ax.plot(small, color=GRAY, lw=2)
ax.plot(trump, color=RED, lw=2.5)
for s, c, label in [(small, GRAY, "Same $ in small-\ncompany stocks"), (trump, RED, "Trump-linked\nstocks"),
                    (invested, INK2, "Total put in")]:
    ax.scatter(s.index[-1], s.iloc[-1], color=c, s=50, zorder=3, edgecolor=SURF, linewidth=2)
    ax.annotate(f"{label}\n${s.iloc[-1]:,.0f}", (s.index[-1], s.iloc[-1]), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=12.5, color=INK,
                fontweight="normal" if c == INK2 else "bold")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
ax.set_ylim(0, max(small.max(), invested.max()) * 1.12)
ax.set_xlim(p.index[0], p.index[-1] + pd.Timedelta(days=110))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.text(pd.Timestamp("2025-10-20"), 1060, "dashed = money put in so far\n(steps up $100 as each company joins)",
        fontsize=10, color=INK2, va="top")

# ---- members panel ----------------------------------------------------------
TIE = {"DJT": "Trump: largest shareholder (also holds bitcoin)", "PSQH": "Don Jr: board", "UMAC": "Don Jr: adviser, shareholder",
       "DOMH": "Don Jr & Eric: advisers, >10% owners", "3350.T": "Eric: adviser · bitcoin treasury", "DTCX": "Don Jr: shareholder · crypto treasury/mining",
       "PEW": "Don Jr: board · online gun store", "MCGA": "Merging with Trump Media's crypto vehicle", "AIFC": "Eric: adviser · holds WLFI tokens",
       "ABTC": "Eric: co-founder; Don Jr: stake · bitcoin mining", "MMA": "Don Jr: adviser · combat sports", "NWAX": "Don Jr & Eric: advisers",
       "CLBR": "Don Jr: board"}
GROUPS = [("Crypto businesses", ["ABTC", "3350.T", "DTCX", "AIFC"], "BTC-USD", "bitcoin"),
          ("Other businesses", ["DJT", "PSQH", "UMAC", "DOMH", "PEW", "MMA"], "IWC", "small-company stocks"),
          ("SPACs (cash shells)", ["MCGA", "NWAX", "CLBR"], None, None)]
tab.axis("off"); tab.set_xlim(0, 1); tab.set_ylim(0, 1)
tab.text(0, 1.0, "$100 in each of the 13 members", fontsize=14, fontweight="bold", va="top")
tab.text(0.72, 0.955, "bought", fontsize=10, color=INK2, ha="right", va="top")
tab.text(1.0, 0.955, "worth now", fontsize=10, color=INK2, ha="right", va="top")
n_units = sum(len(m) for _, m, _, _ in GROUPS) + 1.45 * len(GROUPS)
step = 0.92 / n_units
y = 0.915
gsum = {}
for gname, members, bench, bname in GROUPS:
    members = sorted(members, key=lambda t: joins[t])
    now = sum(trump_pos[t].iloc[-1] for t in members)
    y -= 0.25 * step
    tab.text(0, y, gname, fontsize=12.5, fontweight="bold", va="top", color=RED)
    tab.text(1.0, y, f"${STAKE * len(members):,} → ${now:,.0f}", fontsize=12.5, fontweight="bold", va="top", ha="right", color=RED)
    if bench:
        b_now = sum(position(bench, joins[t]).iloc[-1] for t in members)
        gsum[gname] = (STAKE * len(members), now, b_now)
        tab.text(0, y - 0.028, f"Same $ in {bname} on the same days: ${b_now:,.0f}", fontsize=9.5, va="top", color=INK2)
    else:
        tab.text(0, y - 0.028, "Hold investors' cash in trust until a merger, so prices barely move", fontsize=9.5, va="top", color=INK2)
    tab.plot([0, 1], [y - 0.052, y - 0.052], color=INK2, lw=0.8)
    y -= step * 1.2
    for t in members:
        tab.text(0.02, y, {"MCGA": "Yorkville SPAC (MCGA)"}.get(t, short(t)), fontsize=11, fontweight="bold", va="top")
        tab.text(0.02, y - 0.026, TIE[t], fontsize=9, va="top", color=INK2)
        tab.text(0.72, y, "Jan 17 2025" if joins[t] == BASE else joins[t].strftime("%b %-d %Y"),
                 fontsize=10, va="top", ha="right", color=INK2)
        tab.text(1.0, y, f"${trump_pos[t].iloc[-1]:,.0f}", fontsize=11.5, va="top", ha="right", fontweight="bold")
        y -= step

# ---- callout: answers "did they only fall because crypto crashed?" -------------------
(ci, cn, cb), (oi, on, ob) = gsum["Crypto businesses"], gsum["Other businesses"]
ax.text(p.index[0] + pd.Timedelta(days=8), ax.get_ylim()[1] * 0.97, "Did Trump-linked stocks fall just because crypto crashed? No:",
        fontsize=13, fontweight="bold", va="top", color=INK,
        bbox=dict(facecolor=SURF, edgecolor="none", pad=2))
ax.text(p.index[0] + pd.Timedelta(days=8), ax.get_ylim()[1] * 0.97 - 95,
        f"The 4 Trump-linked crypto businesses: ${ci:,} → ${cn:,.0f}\n   The same $ in bitcoin itself: ${cb:,.0f}\n"
        f"The 6 Trump-linked non-crypto businesses: ${oi:,} → ${on:,.0f}\n   The same $ in small-company stocks: ${ob:,.0f}",
        fontsize=11.5, va="top", color=INK, linespacing=1.5,
        bbox=dict(facecolor=SURF, edgecolor="none", pad=2))

asof = p.index[-1].strftime("%b %-d, %Y")
total = STAKE * len(joins)
top = header(fig, f"${total:,} in Trump-linked stocks is now worth ${trump.iloc[-1]:,.0f}. In small-company stocks: ${small.iloc[-1]:,.0f}",
             "$100 into each company on the day its Trump-family tie was announced, vs $100 into small-company stocks "
             f"(iShares Russell Microcap ETF, IWC) on the same day · through {asof}", H)
footer(fig, "Size check: 10 of the 13 were worth under $1B when bought, the same size class as the microcap index; "
            f"the 3 bigger ones fell too (Trump Media, American Bitcoin, Metaplanet).\n"
            f"Same $ in the whole US market (Russell 3000): ${whole.iloc[-1]:,.0f}. Without the 3 SPACs (cash in trust, ~flat): "
            f"${len(ex) * STAKE:,} → ${trump_ex:,.0f}, vs ${small_ex:,.0f} in small stocks. "
            "DJT, PSQH, UMAC ties predate the inauguration, so they're bought Jan 17 2025.")
fig.subplots_adjust(left=0.06, right=0.985, top=top - 0.02, bottom=0.16)
Path("plots").mkdir(exist_ok=True)
fig.savefig("plots/4_since_inauguration.png")

print(f"invested ${total}  trump ${trump.iloc[-1]:,.0f}  small ${small.iloc[-1]:,.0f}  whole ${whole.iloc[-1]:,.0f}  "
      f"ex-SPAC ${trump_ex:,.0f} vs ${small_ex:,.0f}")
