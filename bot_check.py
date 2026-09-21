#!/usr/bin/env python3
"""
AlphaWave Telegram Bot — Self-Diagnostic Tool (බොට් දෝෂ හොයන මෙවලම)

Usage:  python bot_check.py

Checks, in order:
  1. Python version
  2. python-telegram-bot library
  3. bot token presence & format
  4. Telegram API reachability + token validity (getMe)
  5. webhook leftover (409 conflict cause) + auto-delete option
  6. access mode / admins / protection config
  7. data folder writability
  8. bot application build (handlers registration)
Prints a Sinhala verdict + exact fix for every failure.
"""

import json
import os
import sys
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36"}
OK, FAIL, WARN = "✅", "❌", "⚠️"


def step(n, title):
    print(f"\n[{n}] {title}")


def http_json(url, token=None, timeout=20):
    h = dict(UA)
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return None, {"error": f"{type(e).__name__}: {str(e)[:160]}"}


def main():
    print("=" * 66)
    print("  ALPHAWAVE TELEGRAM BOT — DIAGNOSTIC / දෝෂ හදුනාගැනීම")
    print("=" * 66)
    fails = []

    # 1 python
    step(1, "Python version පරීක්ෂාව")
    v = sys.version_info
    print(f"    Python {v.major}.{v.minor}.{v.micro}")
    if v.major == 3 and v.minor >= 9:
        print(f"    {OK} OK (3.9+ අවශ්‍යයි)")
    else:
        print(f"    {FAIL} Python 3.9+ අවශ්‍යයි — python.org වලින් අලුත්ම එක install කරන්න")
        fails.append("python")

    # 2 library
    step(2, "python-telegram-bot library පරීක්ෂාව")
    try:
        import telegram
        from telegram.ext import Application  # noqa: F401
        print(f"    {OK} python-telegram-bot {telegram.__version__}")
        lib_ok = True
    except Exception as e:
        lib_ok = False
        print(f"    {FAIL} library නැත: {str(e)[:100]}")
        print("    විසඳුම:  pip install -r requirements.txt")
        print("              (venv එකක් ඇතුළත නම්: activate කරලා නැවත)")
        fails.append("library")

    # 3 token
    step(3, "Bot token පරීක්ෂාව")
    from core.config import CONFIG
    CONFIG.load()
    token = (CONFIG.get("telegram", "bot_token") or "").strip()
    if not token:
        print(f"    {FAIL} token එකක් config.json එකේ නැත!")
        print("    විසඳුම:  Telegram → @BotFather → /newbot → token එක copy කර")
        print("              GUI → ✈️ Bot tab → paste → Save token")
        print("              (හෝ config.json → telegram.bot_token)")
        fails.append("token")
    elif ":" not in token or len(token) < 30:
        print(f"    {FAIL} token format එක වැරදියි: {token[:8]}...")
        print("    විසඳුම:  @BotFather වලින් සම්පූර්ණ token එක නැවත copy කරන්න")
        fails.append("token")
    else:
        print(f"    {OK} token ඇත ({token[:10]}...{token[-4:]})")

    # 4 api + token validity
    me = None
    if token and ":" in token:
        step(4, "Telegram API සම්බන්ධතාවය + token වලංගුභාවය (getMe)")
        code, d = http_json(f"https://api.telegram.org/bot{token}/getMe")
        if code == 200 and d.get("ok"):
            me = d["result"]
            print(f"    {OK} API සම්බන්ධයි · bot = @{me.get('username')} ({me.get('first_name')})")
        elif code == 401:
            print(f"    {FAIL} token වලංගු නොවේ (401 Unauthorized)")
            print("    විසඳුම:  @BotFather → /mybots → API Token → නව token එකක්")
            print("              (පැරණි එක revoke වී ඇත) → GUI Bot tab → Save")
            fails.append("token-invalid")
        elif code == 429:
            print(f"    {WARN} rate limit (429) — තත්පර කිහිපයකින් නැවත උත්සාහ කරයි; සාමාන්‍යයි")
        elif code is None:
            print(f"    {FAIL} network එකට api.telegram.org යා නොහැක: {d.get('error')}")
            print("    විසඳුම:  internet/VPN/firewall පරීක්ෂා කරන්න; corporate proxy නම්")
            print("              proxy bypass එකක් අවශ්‍ය විය හැක")
            fails.append("network")
        else:
            print(f"    {FAIL} HTTP {code}: {str(d)[:160]}")
            fails.append("api")

    # 5 webhook
    if token and ":" in token and me:
        step(5, "Webhook leftover පරීක්ෂාව (409 conflict හේතුව)")
        code, d = http_json(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        url = (d.get("result") or {}).get("url", "") if code == 200 else ""
        if url:
            print(f"    {WARN} webhook එකක් set වී ඇත: {url}")
            print("    → මෙය polling එකට conflict (409) දෙයි. AlphaWave bot එක start වන විට")
            print("      මෙය automatic delete කරයි; හෝ දැන්ම මකන්න: y")
            ans = input("    webhook එක දැන්ම delete කරන්නද? (y/N): ").strip().lower()
            if ans == "y":
                c2, d2 = http_json(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
                print("    " + (f"{OK} webhook deleted" if c2 == 200 and d2.get("ok") else f"{FAIL} {str(d2)[:120]}"))
        else:
            print(f"    {OK} webhook නැත — polling එකට හරි")
        # pending updates / other poller hint
        code, d = http_json(f"https://api.telegram.org/bot{token}/getUpdates?limit=1")
        if code == 409:
            print(f"    {WARN} තවත් process එකක් දැන් getUpdates කරයි (409)!")
            print("    විසඳුම:  run_bot.py / පැරණි main.py instance එකක් තිබේ නම් නවත්තන්න")
            fails.append("conflict")

    # 6 config
    step(6, "Access / protection config පරීක්ෂාව")
    mode = CONFIG.get("telegram", "access_mode", default="open")
    ids = CONFIG.get("telegram", "allowed_user_ids", default=[]) or []
    admins = CONFIG.get("telegram", "admin_user_ids", default=[]) or []
    prot = CONFIG.get("telegram", "protect_content", default=True)
    print(f"    mode = {mode} · users = {len(ids)} · admins = {len(admins)} · protect = {prot}")
    if mode == "whitelist" and not ids and not admins:
        print(f"    {WARN} whitelist mode එකේ users නැත — ඕනෑම කෙනෙක් ⛔ වේ!")
        print("    විසඳුම:  /accessmode open  හෝ GUI Access Control → IDs add")
    else:
        print(f"    {OK} OK")

    # 7 data dir
    step(7, "data folder ලිවීමේ හැකියාව")
    try:
        p = os.path.join(BASE, "data", "_write_test")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write("x")
        os.remove(p)
        print(f"    {OK} OK")
    except Exception as e:
        print(f"    {FAIL} data folder එකට ලිවිය නොහැක: {str(e)[:120]}")
        fails.append("data")

    # 8 build
    step(8, "Bot application build පරීක්ෂාව (handlers)")
    if lib_ok:
        try:
            from bot.telegram_bot import build_application, COMMANDS
            app = build_application(token or "123456789:AAF_build_check_only")
            n = sum(len(v) for v in app.handlers.values())
            print(f"    {OK} handlers {n} · menu commands {len(COMMANDS)} — build OK")
        except Exception as e:
            print(f"    {FAIL} build අසාර්ථකයි: {type(e).__name__}: {str(e)[:200]}")
            fails.append("build")

    # verdict
    print("\n" + "=" * 66)
    if not fails:
        print("  ✅ සියල්ල OK! Bot එක දැන් start කරන්න:")
        print("     • GUI:  python main.py  →  ✈️ Bot tab  →  ▶ Start bot")
        print("     • හෝ:  python run_bot.py   (bot එක පමණක්)")
        print("     ඉන්පසු Telegram එකේ ඔබේ bot ට /start යවන්න.")
    else:
        print(f"  ❌ දෝෂ {len(fails)}ක් හමුවිය: {', '.join(fails)}")
        print("  ඉහත එක් එක් පියවරේ 'විසඳුම' පරිදි සකසා නැවත මෙය run කරන්න:")
        print("     python bot_check.py")
    print("  (වැඩිදුර logs: data/bot.log · GUI → Bot tab → Bot logs)")
    print("=" * 66)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
