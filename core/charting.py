"""
Server-side chart rendering (matplotlib, headless 'Agg').

Produces PNG candlestick charts with indicators and BUY/SELL highlight
markers - used by the Telegram bot (/chart) and the GUI download button.
(The interactive GUI chart itself uses TradingView lightweight-charts in JS.)
"""

import io
import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime

from . import binance_client as bc
from . import indicators as ind

log = logging.getLogger("chart")

UP = "#26a69a"
DOWN = "#ef5350"
BG = "#131722"
FG = "#d1d4dc"
GRID = "#2a2e39"


def render_chart_png(symbol: str, interval: str = "15m", limit: int = 150,
                     overlays=("ema20", "ema50", "vwap"), show_marks: bool = True,
                     sub="rsi", width_in=13, height_in=7.5) -> bytes:
    df = bc.klines(symbol, interval, limit)
    if df.empty:
        raise ValueError("no candle data")
    a = ind.build_analysis(df)

    n_panels = 2 + (1 if sub else 0)
    fig, axes = plt.subplots(
        n_panels, 1, figsize=(width_in, height_in), dpi=110,
        gridspec_kw={"height_ratios": [5, 1.2] + ([1.2] if sub else []), "hspace": 0.06},
        sharex=True)
    ax, axv = axes[0], axes[1]
    for x in axes:
        x.set_facecolor(BG)
        x.grid(color=GRID, linewidth=0.4, alpha=0.6)
        x.tick_params(colors=FG, labelsize=8)
        for s in x.spines.values():
            s.set_color(GRID)
    fig.patch.set_facecolor(BG)

    xs = list(range(len(df)))
    times = [datetime.utcfromtimestamp(t / 1000) for t in df.index]

    # candles --------------------------------------------------------------
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    for i in xs:
        col = UP if c[i] >= o[i] else DOWN
        ax.plot([i, i], [l[i], h[i]], color=col, linewidth=0.7, zorder=2)
        body_lo, body_hi = min(o[i], c[i]), max(o[i], c[i])
        body_h = max(body_hi - body_lo, (h[i] - l[i]) * 0.002)
        ax.add_patch(Rectangle((i - 0.32, body_lo), 0.64, body_h,
                               facecolor=col, edgecolor=col, linewidth=0.5, zorder=3))

    # overlays -------------------------------------------------------------
    colors = {"ema9": "#f0b90b", "ema20": "#2962ff", "ema50": "#e040fb",
              "ema200": "#ff6d00", "vwap": "#00e5ff", "bb": "#787b86",
              "supertrend": "#ffd54f"}
    for name in overlays:
        if name == "bb":
            ax.plot(xs, a["bb_upper"], color=colors["bb"], linewidth=0.7, alpha=0.8)
            ax.plot(xs, a["bb_lower"], color=colors["bb"], linewidth=0.7, alpha=0.8)
            ax.fill_between(xs, a["bb_upper"], a["bb_lower"], color=colors["bb"], alpha=0.06)
        elif name == "supertrend":
            ax.plot(xs, a["supertrend"], color=colors[name], linewidth=1.0,
                    label="SuperTrend")
        elif name in a:
            ax.plot(xs, a[name], color=colors.get(name, "#fff"), linewidth=1.0, label=name.upper())

    # buy/sell marks ---------------------------------------------------------
    if show_marks:
        shown = 0
        for e in a["events"]:
            if e["pos"] < len(df) - 90 or shown >= 28:
                continue
            shown += 1
            if e["side"] == "buy":
                ax.scatter(e["pos"], e["price"] * 0.995, marker="^", s=55,
                           color="#00e676", zorder=5, edgecolors="black", linewidths=0.4)
            else:
                ax.scatter(e["pos"], e["price"] * 1.005, marker="v", s=55,
                           color="#ff1744", zorder=5, edgecolors="black", linewidths=0.4)

    price = float(c[-1])
    chg = (c[-1] - c[0]) / c[0] * 100
    ax.axhline(price, color="#f0b90b", linewidth=0.6, linestyle="--", alpha=0.8)
    ax.set_title(f"{symbol}  {interval}   last={price:g}   ({chg:+.2f}% over {len(df)} candles)"
                 f"   ▲/▼ = strategy buy/sell events",
                 color=FG, fontsize=11, loc="left")
    ax.tick_params(labelbottom=False)

    # volume ----------------------------------------------------------------
    vcols = [UP if c[i] >= o[i] else DOWN for i in xs]
    axv.bar(xs, df["volume"].values, color=vcols, width=0.7, alpha=0.85)
    axv.set_ylabel("Vol", color=FG, fontsize=8)

    # sub indicator -----------------------------------------------------------
    if sub == "rsi":
        axr = axes[2]
        axr.set_facecolor(BG)
        axr.grid(color=GRID, linewidth=0.4, alpha=0.6)
        axr.tick_params(colors=FG, labelsize=8)
        axr.plot(xs, a["rsi"], color="#f0b90b", linewidth=1.0)
        axr.axhline(70, color=DOWN, linewidth=0.6, linestyle="--")
        axr.axhline(30, color=UP, linewidth=0.6, linestyle="--")
        axr.set_ylim(0, 100)
        axr.set_ylabel("RSI", color=FG, fontsize=8)
    elif sub == "macd":
        axr = axes[2]
        axr.set_facecolor(BG)
        axr.grid(color=GRID, linewidth=0.4, alpha=0.6)
        axr.tick_params(colors=FG, labelsize=8)
        hist = a["macd_hist"].values
        axr.bar(xs, hist, color=[UP if v >= 0 else DOWN for v in hist], width=0.7, alpha=0.8)
        axr.plot(xs, a["macd"], color="#2962ff", linewidth=1.0)
        axr.plot(xs, a["macd_signal"], color="#ff6d00", linewidth=1.0)
        axr.set_ylabel("MACD", color=FG, fontsize=8)

    # x labels: every ~len/8 candle
    step = max(len(df) // 8, 1)
    ticks = xs[::step]
    axv.set_xticks(ticks)
    if sub:
        axes[-1].set_xticks(ticks)
        axes[-1].set_xticklabels([times[i].strftime("%m-%d %H:%M") for i in ticks],
                                 rotation=0, fontsize=7, color=FG)
        axv.set_xticklabels([])
    else:
        axv.set_xticks(ticks)
        axv.set_xticklabels([times[i].strftime("%m-%d %H:%M") for i in ticks], fontsize=7, color=FG)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------- signal chart

def render_signal_chart_png(symbol: str, interval: str, sig: dict,
                            width_in=14.5, height_in=9) -> bytes:
    """TradingView-style signal plan chart:
    candles + entry / SL / TP lines & risk-reward zones + strategy event
    markers + methods box + 'Analyzed by AlphaWave' corner watermark."""
    df = bc.klines(symbol, interval, 180)
    if df.empty:
        raise ValueError("no candle data")
    a = ind.build_analysis(df)

    fig, (ax, axv) = plt.subplots(
        2, 1, figsize=(width_in, height_in), dpi=170,
        gridspec_kw={"height_ratios": [5, 1.1], "hspace": 0.06}, sharex=True)
    for x in (ax, axv):
        x.set_facecolor(BG)
        x.grid(color=GRID, linewidth=0.4, alpha=0.6)
        x.tick_params(colors=FG, labelsize=8)
        for sp in x.spines.values():
            sp.set_color(GRID)
    fig.patch.set_facecolor(BG)

    xs = list(range(len(df)))
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    for i in xs:
        col = UP if c[i] >= o[i] else DOWN
        ax.plot([i, i], [l[i], h[i]], color=col, linewidth=0.9, zorder=2)
        b_lo, b_hi = min(o[i], c[i]), max(o[i], c[i])
        ax.add_patch(Rectangle((i - 0.34, b_lo), 0.68, max(b_hi - b_lo, (h[i]-l[i])*0.002),
                               facecolor=col, edgecolor=col, linewidth=0.6, zorder=3))
    ax.plot(xs, a["ema20"], color="#2962ff", linewidth=1.3, label="EMA20")
    ax.plot(xs, a["ema50"], color="#e040fb", linewidth=1.3, label="EMA50")
    ax.legend(loc="lower left", fontsize=8, facecolor="#0d1119", edgecolor="#2a2e39",
              labelcolor="#d1d4dc", framealpha=0.9)

    side = sig.get("side", "LONG")
    entry = float(sig.get("entry_price") or 0)
    sl = float(sig.get("stop_loss") or 0)
    tp = float(sig.get("take_profit") or 0)
    n = len(df)
    if entry and sl and tp:
        x0, x1 = max(0, n - 90), n + 12
        ax.axhline(entry, color="#2962ff", linewidth=1.4, zorder=4)
        ax.axhline(sl, color="#ff1744", linewidth=1.4, linestyle="--", zorder=4)
        ax.axhline(tp, color="#00e676", linewidth=1.4, linestyle="--", zorder=4)
        ax.fill_between([x0, x1], entry, sl, color="#ff1744", alpha=0.10, zorder=1)
        ax.fill_between([x0, x1], entry, tp, color="#00e676", alpha=0.08, zorder=1)
        for t in (sig.get("take_profit_levels") or [])[:3]:
            try:
                ax.axhline(float(t["price"]), color="#00e676", linewidth=0.7,
                           linestyle=":", alpha=0.8, zorder=4)
                ax.text(x1 - 1, float(t["price"]), f" {t['name']} {t['price']:g}",
                        color="#00e676", fontsize=7.5, va="center")
            except Exception:
                pass
        ax.text(x1 - 1, entry, f" ENTRY {entry:g}", color="#2962ff", fontsize=8.5,
                va="center", fontweight="bold")
        ax.text(x1 - 1, sl, f" STOP {sl:g}", color="#ff1744", fontsize=8.5,
                va="center", fontweight="bold")
        ax.text(x1 - 1, tp, f" TP {tp:g}", color="#00e676", fontsize=8.5,
                va="center", fontweight="bold")
        ax.set_xlim(0, x1 + 8)

    shown = 0
    for e in a["events"]:
        if e["pos"] < n - 70 or shown >= 20:
            continue
        shown += 1
        if e["side"] == "buy":
            ax.scatter(e["pos"], e["price"] * 0.995, marker="^", s=72, color="#00e676",
                       zorder=5, edgecolors="white", linewidths=0.7)
        else:
            ax.scatter(e["pos"], e["price"] * 1.005, marker="v", s=72, color="#ff1744",
                       zorder=5, edgecolors="white", linewidths=0.7)

    # methods box (which analysis methods produced this signal)
    methods = []
    for v in (sig.get("strategy_breakdown") or []):
        if v.get("direction") == side:
            methods.append(f"{v['strategy']} ({v['strength']:.0f}%)")
    methods = methods[:6]
    box = "\n".join(["ANALYSIS METHODS USED:"] + [f"• {m}" for m in methods] +
                    [f"• HTF {sig.get('htf', {}).get('timeframe', '-')}: "
                     f"{sig.get('htf', {}).get('bias', '-')}",
                     f"• SL method: {sig.get('sl_method', '-')[:44]}"])
    ax.text(0.012, 0.985, box, transform=ax.transAxes, fontsize=8.6, color="#d7dce6",
            va="top", family="monospace", linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.5", fc="#0d1119", ec="#3a445c", alpha=0.94))

    # corner watermark
    fig.text(0.995, 0.995, "Analyzed by AlphaWave", ha="right", va="top",
             color="#f0b90b", fontsize=13, fontweight="bold", alpha=0.95)
    ax.set_title(f"{symbol} {interval} — {side} plan · conf {sig.get('confidence', 0)}% · "
                 f"R:R {sig.get('risk_reward', 0)} · live {sig.get('live_price', 0):g}",
                 color="#eef1f7", fontsize=13, loc="left", fontweight="bold")

    vcols = [UP if c[i] >= o[i] else DOWN for i in xs]
    axv.bar(xs, df["volume"].values, color=vcols, width=0.7, alpha=0.85)
    axv.set_ylabel("Vol", color=FG, fontsize=9)
    step = max(len(df) // 8, 1)
    from datetime import datetime as _dt
    times = [_dt.utcfromtimestamp(t / 1000) for t in df.index]
    axv.set_xticks(xs[::step])
    axv.set_xticklabels([times[i].strftime("%m-%d %H:%M") for i in xs[::step]],
                        fontsize=8.5, color=FG)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return buf.getvalue()
