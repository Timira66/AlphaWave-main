"""
AlphaWave Trade Monitor.

Every generated signal becomes a tracked trade (status OPEN) until it is
closed by TP / SL, cancelled by the user, or expired. While open, the monitor
watches live price and pushes updates to:
  * the Telegram owner of the signal (if generated from Telegram)
  * ALL Telegram admins (every user's signals - web or bot)
  * the web app INBOX (same messages, same order)

Alert kinds:
  TP1_LADDER   - price reached TP1: secure partial profits + move SL to BE
  SL_UPDATE    - structure moved in your favour: a better (trailing) SL
  TP_UPDATE    - trend still strong: consider extending the TP / laddering
  CRASH_WARNING- sudden adverse move: consider CANCELLING the trade now
  CLOSED_TP    - take profit hit -> trade closed in profit
  CLOSED_SL    - stop loss hit -> trade closed at risk amount
  EXPIRE       - open too long without resolution: re-evaluate / cancel
  CANCELLED    - user cancelled the trade

Only one monitor instance is active per machine (leader lock file), so
running GUI + bot together never duplicates alerts.
"""

import json
import os
import time
import threading
import logging

from .config import CONFIG, DATA_DIR
from . import binance_client as bc
from . import signal_engine

log = logging.getLogger("monitor")

INBOX_PATH = os.path.join(DATA_DIR, "inbox.json")
LOCK_PATH = os.path.join(DATA_DIR, "monitor.lock")
_inbox_lock = threading.Lock()

INTERVAL_MS = {"1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000,
               "30m": 1800000, "1h": 3600000, "2h": 7200000, "4h": 14400000,
               "6h": 21600000, "8h": 28800000, "12h": 43200000, "1d": 86400000}

# telegram senders registered by the bot thread: fn(chat_id:int, text:str)
TELEGRAM_SENDERS = []


def register_telegram_sender(fn):
    if fn not in TELEGRAM_SENDERS:
        TELEGRAM_SENDERS.append(fn)


# ------------------------------------------------------------------ inbox

def inbox_add(item: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with _inbox_lock:
        try:
            with open(INBOX_PATH, "r", encoding="utf-8") as f:
                box = json.load(f)
        except Exception:
            box = []
        box.insert(0, item)
        box = box[:400]
        tmp = INBOX_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(box, f, indent=1, ensure_ascii=False)
        os.replace(tmp, INBOX_PATH)


def inbox_list(limit=100):
    try:
        with open(INBOX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)[:limit]
    except Exception:
        return []


def inbox_clear():
    with _inbox_lock:
        try:
            os.replace(INBOX_PATH, INBOX_PATH + ".bak")
        except Exception:
            pass


# ------------------------------------------------------------- leader lock

def _leader() -> bool:
    """Single-monitor-per-machine lock (stale after 45 s)."""
    now = time.time()
    try:
        with open(LOCK_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        if now - d.get("ts", 0) < 45 and d.get("pid") != os.getpid():
            return False
    except Exception:
        pass
    try:
        with open(LOCK_PATH, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "ts": now}, f)
        return True
    except Exception:
        return False


# ------------------------------------------------------------- trade store

def _save_trade(trade: dict):
    """Patch one journal entry by trade_id."""
    hist = signal_engine.journal_list(500)
    for h in hist:
        if h.get("trade_id") == trade["trade_id"]:
            h.update(trade)
            break
    signal_engine.journal_replace(hist)


def open_trades(limit=60):
    return [t for t in signal_engine.journal_list(500)
            if t.get("status") == "OPEN" and t.get("side") in ("LONG", "SHORT")][:limit]


# ------------------------------------------------------------- alerting

def _alert(trade: dict, kind: str, text: str):
    ts = int(time.time())
    item = {"ts": ts, "kind": kind, "coin": trade.get("coin"),
            "trade_id": trade.get("trade_id"), "message": text}
    inbox_add(item)
    upd = trade.setdefault("updates", [])
    upd.append({"ts": ts, "kind": kind, "msg": text})
    _save_trade({"trade_id": trade["trade_id"], "updates": upd,
                 "last_update_kind": kind, "last_update_ts": ts})
    owner = trade.get("owner") or {}
    targets = set()
    if owner.get("type") == "bot" and owner.get("chat_id"):
        targets.add(int(owner["chat_id"]))
    for adm in (CONFIG.get("telegram", "admin_user_ids", default=[]) or []):
        targets.add(int(adm))
    msg = f"{'='*10}\n{text}"
    for tid in targets:
        for fn in TELEGRAM_SENDERS:
            try:
                fn(tid, msg)
            except Exception as e:
                log.warning("tg send failed: %s", e)


# ------------------------------------------------------------- evaluation

def _price(trade):
    return bc.quick_price(trade["coin"])


def evaluate_trade(trade: dict) -> dict:
    """One monitoring pass over a single open trade. Mutates trade flags."""
    out = {"events": []}
    coin = trade["coin"]
    side = trade["side"]
    entry = float(trade.get("entry_price") or 0)
    sl = float(trade.get("stop_loss") or 0)
    tp = float(trade.get("take_profit") or 0)
    if not (entry and sl and tp):
        return out
    sign = 1 if side == "LONG" else -1
    risk = abs(entry - sl) or 1e-9
    try:
        snap = _price(trade)
        px = float(snap["last_price"])
    except Exception:
        return out
    iv_ms = INTERVAL_MS.get(trade.get("timeframe", "15m"), 900000)
    age_candles = (time.time() * 1000 - _ts_of(trade)) / iv_ms

    # --- closed by TP / SL -------------------------------------------------
    if sign == 1:
        if px >= tp:
            out["events"].append(("CLOSED_TP",
                f"✅ CLOSED - TAKE PROFIT HIT\n{coin} {side}: price {px:g} reached TP {tp:g}.\n"
                f"Profit ~+{abs(tp-entry)/risk:.1f}R. Trade closed - no further alerts."))
            out["status"] = "CLOSED_TP"
            return out
        if px <= sl:
            out["events"].append(("CLOSED_SL",
                f"🛑 CLOSED - STOP LOSS HIT\n{coin} {side}: price {px:g} touched SL {sl:g}.\n"
                f"Loss ~-1.0R (risk amount). Trade closed - no further alerts."))
            out["status"] = "CLOSED_SL"
            return out
    else:
        if px <= tp:
            out["events"].append(("CLOSED_TP",
                f"✅ CLOSED - TAKE PROFIT HIT\n{coin} {side}: price {px:g} reached TP {tp:g}.\n"
                f"Profit ~+{abs(tp-entry)/risk:.1f}R. Trade closed - no further alerts."))
            out["status"] = "CLOSED_TP"
            return out
        if px >= sl:
            out["events"].append(("CLOSED_SL",
                f"🛑 CLOSED - STOP LOSS HIT\n{coin} {side}: price {px:g} touched SL {sl:g}.\n"
                f"Loss ~-1.0R (risk amount). Trade closed - no further alerts."))
            out["status"] = "CLOSED_SL"
            return out

    profit_r = (px - entry) * sign / risk

    # --- market crash early-warning ---------------------------------------
    if not trade.get("crash_warned"):
        try:
            df = bc.klines(coin, trade.get("timeframe", "15m"), 8)
            base = float(df["close"].iloc[-4])
            move = (px - base) / base * 100
            atr_pct = float(bc.klines(coin, trade.get("timeframe", "15m"), 60)["close"].pct_change().abs().tail(30).mean()) * 100
            crash_thr = max(1.5, atr_pct * 2.5)
            if move * sign < -crash_thr:
                trade["crash_warned"] = True
                out["events"].append(("CRASH_WARNING",
                    f"🚨 MARKET CRASH WARNING - consider CANCELLING now\n"
                    f"{coin} {side}: adverse move {move:+.2f}% in 3 candles "
                    f"(threshold {-crash_thr*sign*sign:.2f}% against you).\n"
                    f"Current price {px:g} vs entry {entry:g} ({profit_r:+.2f}R).\n"
                    f"Action: cancel the trade, or tighten SL to "
                    f"{entry + sign*0.5*risk:g} (0.5R) if you want to stay in."))
        except Exception:
            pass

    # --- TP1 ladder suggestion --------------------------------------------
    if not trade.get("laddered") and profit_r >= 1.15:
        trade["laddered"] = True
        out["events"].append(("TP1_LADDER",
            f"💰 TP1 REACHED - LADDER THE TRADE\n{coin} {side} is +{profit_r:.2f}R "
            f"(price {px:g}).\nSuggested ladder:\n"
            f"  1) secure ~50% profit here ({px:g})\n"
            f"  2) move STOP LOSS to break-even {entry:g}\n"
            f"  3) let the runner aim at TP2/TP3 {tp:g}"))

    # --- trailing SL update suggestion -------------------------------------
    last_sl_alert = trade.get("last_sl_alert_ts", 0)
    if profit_r >= 1.5 and time.time() - last_sl_alert > 600:
        try:
            df = bc.klines(coin, trade.get("timeframe", "15m"), 60)
            from . import indicators as ind
            sw_hi, sw_lo = ind.swing_points(df, 3, 3)
            atr_v = float(ind.atr(df, 14).iloc[-1])
            if side == "LONG":
                cands = [v for _, v in sw_lo[-4:] if v < px - 0.5 * atr_v]
                new_sl = (max(cands) - 0.3 * atr_v) if cands else entry + 0.5 * risk
            else:
                cands = [v for _, v in sw_hi[-4:] if v > px + 0.5 * atr_v]
                new_sl = (min(cands) + 0.3 * atr_v) if cands else entry - 0.5 * risk
            if (new_sl - sl) * sign > 0.2 * atr_v and (px - new_sl) * sign > 0.5 * atr_v:
                trade["last_sl_alert_ts"] = time.time()
                trade["suggested_sl"] = round(new_sl, 8)
                out["events"].append(("SL_UPDATE",
                    f"🔁 STOP LOSS UPDATE AVAILABLE\n{coin} {side}: structure moved in "
                    f"your favour (+{profit_r:.2f}R).\nCurrent SL {sl:g} -> suggested NEW SL "
                    f"{new_sl:g} (below/above newest swing, locks "
                    f"{abs(new_sl-entry)/risk:.1f}R).\nUpdate your exchange SL or /cancel to ignore."))
        except Exception:
            pass

    # --- TP extension suggestion -------------------------------------------
    if not trade.get("tp_ext") and profit_r >= 0.85:
        try:
            from . import accuracy
            htf = accuracy.htf_bias(coin, trade.get("timeframe", "15m"))
            if htf.get("bias") == side and (htf.get("adx") or 0) >= 28:
                trade["tp_ext"] = True
                ext = tp + sign * abs(tp - entry) * 0.5
                out["events"].append(("TP_UPDATE",
                    f"🎯 TAKE PROFIT UPDATE / LADDER OPTION\n{coin} {side}: HTF "
                    f"{htf.get('timeframe')} still {htf['bias']} (ADX {htf['adx']}) with price at "
                    f"+{profit_r:.2f}R.\nOptions: (a) extend TP {tp:g} -> {ext:g}, or "
                    f"(b) ladder: take 1/3 here and keep TP {tp:g} for the rest."))
        except Exception:
            pass

    # --- expiry -------------------------------------------------------------
    if age_candles > 72 and not trade.get("expire_warned"):
        trade["expire_warned"] = True
        out["events"].append(("EXPIRE",
            f"⏳ TRADE STALE - RE-EVALUATE\n{coin} {side} open for {age_candles:.0f} candles at "
            f"{profit_r:+.2f}R without hitting TP/SL.\nMomentum edge has likely decayed: "
            f"consider cancelling, or regenerate a fresh signal for {coin}."))
    return out


def _ts_of(trade):
    try:
        import pandas as pd
        return pd.Timestamp(trade["generated_at"]).timestamp() * 1000
    except Exception:
        return time.time() * 1000


# ------------------------------------------------------------- main loop

_stop = threading.Event()


def monitor_loop():
    log.info("trade monitor thread started")
    while not _stop.is_set():
        try:
            if _leader():
                for trade in open_trades():
                    res = evaluate_trade(dict(trade))
                    patch = {}
                    for k in ("crash_warned", "laddered", "tp_ext",
                              "expire_warned", "last_sl_alert_ts", "suggested_sl"):
                        if k in trade or k in res or trade.get(k) is not None:
                            pass
                    # persist flag changes
                    flags = {k: trade[k] for k in
                             ("crash_warned", "laddered", "tp_ext", "expire_warned",
                              "last_sl_alert_ts", "suggested_sl") if k in trade}
                    if flags:
                        patch.update(flags)
                    if res.get("status"):
                        patch["status"] = res["status"]
                    if patch:
                        patch["trade_id"] = trade["trade_id"]
                        _save_trade(patch)
                    for kind, text in res.get("events", []):
                        _alert(trade, kind, text)
        except Exception as e:
            log.warning("monitor pass error: %s", e)
        _stop.wait(20)
    log.info("trade monitor stopped")


def start_monitor() -> threading.Thread:
    t = threading.Thread(target=monitor_loop, daemon=True, name="trade-monitor")
    t.start()
    return t


def stop_monitor():
    _stop.set()


def cancel_trade(trade_id: str) -> tuple:
    hist = signal_engine.journal_list(500)
    for h in hist:
        if h.get("trade_id") == trade_id and h.get("status") == "OPEN":
            h["status"] = "CANCELLED"
            signal_engine.journal_replace(hist)
            _alert(h, "CANCELLED",
                   f"❎ TRADE CANCELLED by user\n{h.get('coin')} {h.get('side')} "
                   f"(entry {h.get('entry_price')}) - monitoring stopped, no further alerts.")
            return True, "cancelled"
    return False, "trade not found or not open"
