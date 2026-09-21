"""
AI provider router.

Chain: Groq (4 models) -> OpenRouter (3 free models + backups) -> Ollama
(2 local models, free & unlimited) -> Custom OpenAI-compatible endpoint ->
BUILT-IN LOCAL ENGINE (always works, 100% free, zero tokens).

Features
- multiple API keys per provider with round-robin rotation
- per-model cooldown after failures (429/5xx/timeout)
- automatic retry with stripped optional params on HTTP 400
- strict JSON extraction from any model output
- global timeout so a signal is NEVER blocked by AI problems
"""

import json
import re
import time
import threading
import logging
from typing import Optional

import requests

from .config import CONFIG

log = logging.getLogger("ai")

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

_lock = threading.Lock()
_model_health = {}   # (provider, model_id) -> {"fails": int, "cooldown_until": ts}
_key_health = {}     # (provider, key) -> {"cooldown_until": ts, "reason": str}
_key_cursor = {}     # provider -> int
_model_cursor = {}   # provider -> int

KEY_DEAD_COOLDOWN = 6 * 3600     # 401/403 -> skip this key for 6 h
RATE_COOLDOWN = 120              # 429 -> skip this model for 2 min


def _health(provider: str, model_id: str) -> dict:
    key = (provider, model_id)
    with _lock:
        if key not in _model_health:
            _model_health[key] = {"fails": 0, "cooldown_until": 0.0, "ok": 0}
        return _model_health[key]


def _mark_fail(provider: str, model_id: str):
    h = _health(provider, model_id)
    cd = CONFIG.get("ai", "model_cooldown_sec", default=90)
    with _lock:
        h["fails"] += 1
        h["cooldown_until"] = time.time() + cd * min(h["fails"], 4)


def _mark_ok(provider: str, model_id: str):
    h = _health(provider, model_id)
    with _lock:
        h["fails"] = 0
        h["cooldown_until"] = 0.0
        h["ok"] += 1


def _model_available(provider: str, model_id: str) -> bool:
    return _health(provider, model_id)["cooldown_until"] <= time.time()


def _key_available(provider: str, key: str) -> bool:
    with _lock:
        h = _key_health.get((provider, key))
        return (h is None) or h["cooldown_until"] <= time.time()


def _mark_key_dead(provider: str, key: str, reason: str):
    with _lock:
        _key_health[(provider, key)] = {"cooldown_until": time.time() + KEY_DEAD_COOLDOWN,
                                        "reason": reason[:120]}


def classify_error(err: str) -> str:
    low = (err or "").lower()
    if "401" in low or "unauthorized" in low or "user not found" in low or "invalid api key" in low:
        return "dead_key"
    if "403" in low and "region" not in low:
        return "dead_key"
    if "429" in low or "rate" in low or "too many" in low:
        return "rate_limited"
    if "timeout" in low or "timed out" in low:
        return "timeout"
    return "other"


def _next_key(provider: str, keys: list) -> str:
    keys = [k for k in keys if k and _key_available(provider, k)]
    if not keys:
        return ""
    with _lock:
        i = _key_cursor.get(provider, 0) % len(keys)
        _key_cursor[provider] = i + 1
    return keys[i]


def _next_model(provider: str, models: list) -> Optional[dict]:
    """Round-robin over models that are not cooling down."""
    avail = [m for m in models if m.get("id") and _model_available(provider, m["id"])]
    if not avail:
        return None
    with _lock:
        i = _model_cursor.get(provider, 0) % len(avail)
        _model_cursor[provider] = i + 1
    return avail[i]


# ---------------------------------------------------------------- callers

def _post_chat_completions(base_url: str, key: str, payload: dict,
                           headers: dict, timeout: float):
    h = {"Content-Type": "application/json", "User-Agent": BROWSER_UA}
    if key:
        h["Authorization"] = f"Bearer {key}"
    h.update(headers)
    url = base_url.rstrip("/") + "/chat/completions"
    r = requests.post(url, headers=h, json=payload, timeout=timeout)
    return r


def _call_openai_style(base_url, key, model_id, prompt, timeout, extra_headers=None,
                       reasoning=False):
    """Returns (text, error_string). error_string is classified by callers."""
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content":
                "You are a crypto futures trading analyst. Respond ONLY with compact valid JSON, no markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 1 if reasoning else 0.4,
        "max_completion_tokens" if reasoning else "max_tokens": 1400 if reasoning else 700,
    }
    try:
        r = _post_chat_completions(base_url, key, payload, extra_headers or {}, timeout)
    except requests.exceptions.Timeout:
        return None, "timeout"
    except Exception as e:
        return None, f"network: {e}"

    if r.status_code == 400:
        # retry once with only mandatory params (some models reject temperature etc.)
        payload2 = {"model": model_id, "messages": payload["messages"]}
        try:
            r = _post_chat_completions(base_url, key, payload2, extra_headers or {}, timeout)
        except Exception as e:
            return None, f"retry failed: {e}"

    if r.status_code >= 400:
        return None, f"HTTP {r.status_code}: {r.text[:160]}"
    try:
        d = r.json()
        ch = d.get("choices") or []
        if not ch:
            return None, f"no choices: {json.dumps(d)[:120]}"
        msg = ch[0].get("message", {})
        content = msg.get("content") or ""
        rc = msg.get("reasoning") or msg.get("reasoning_content") or ""
        text = content if content.strip() else rc
        return text, None
    except Exception as e:
        return None, f"parse: {e}"


def call_groq(prompt: str, timeout: float) -> tuple:
    cfg = CONFIG.get("ai", "groq", default={})
    if not cfg.get("enabled"):
        return None, "disabled"
    models = cfg.get("models", [])
    m = _next_model("groq", models)
    if not m:
        return None, "all groq models cooling down"
    key = _next_key("groq", cfg.get("keys", []))
    if not key:
        return None, "groq: no usable API key"
    text, err = _call_openai_style("https://api.groq.com/openai/v1", key,
                                   m["id"], prompt, timeout, reasoning=m.get("reasoning"))
    if err:
        kind = classify_error(err)
        if kind == "dead_key":
            _mark_key_dead("groq", key, err)
            return None, "groq: API key invalid (401)"
        _mark_fail("groq", m["id"])
        if kind == "rate_limited":
            _health("groq", m["id"])["cooldown_until"] = time.time() + RATE_COOLDOWN
        return None, f"groq/{m['id']}: {err}"
    _mark_ok("groq", m["id"])
    return text, m["id"]


def call_openrouter(prompt: str, timeout: float) -> tuple:
    cfg = CONFIG.get("ai", "openrouter", default={})
    if not cfg.get("enabled"):
        return None, "disabled"
    models = list(cfg.get("models", [])) + list(cfg.get("backup_models", []))
    m = _next_model("openrouter", models)
    if not m:
        return None, "all openrouter models cooling down"
    key = _next_key("openrouter", cfg.get("keys", []))
    headers = {"HTTP-Referer": "https://localhost/binance-ai-signals",
               "X-Title": "AlphaWave"}
    if not key:
        return None, "openrouter: no usable API key (key invalid/expired - replace it in AI tab)"
    text, err = _call_openai_style("https://openrouter.ai/api/v1", key, m["id"],
                                   prompt, timeout, headers, reasoning=m.get("reasoning"))
    if err:
        kind = classify_error(err)
        if kind == "dead_key":
            _mark_key_dead("openrouter", key, err)
            return None, f"openrouter: API key invalid (401) - replace key in GUI AI tab"
        _mark_fail("openrouter", m["id"])
        if kind == "rate_limited":
            _health("openrouter", m["id"])["cooldown_until"] = time.time() + RATE_COOLDOWN
        return None, f"openrouter/{m['id']}: {err}"
    _mark_ok("openrouter", m["id"])
    return text, m["id"]


def call_ollama(prompt: str, timeout: float) -> tuple:
    cfg = CONFIG.get("ai", "ollama", default={})
    if not cfg.get("enabled"):
        return None, "disabled"
    base = cfg.get("base_url", "http://localhost:11434").rstrip("/")
    try:
        rq = requests.get(base + "/api/tags", timeout=3)
        have = [mm.get("name", "") for mm in rq.json().get("models", [])]
    except Exception:
        return None, ("ollama: not running on this PC - install https://ollama.com then "
                      "'ollama pull llama3.1:8b' (free & unlimited)")
    models = cfg.get("models", [])
    m = _next_model("ollama", models)
    if not m:
        return None, "all ollama models cooling down"
    if not any(h.startswith(m["id"].split(":")[0]) for h in have):
        return None, f"ollama: model not pulled yet - run: ollama pull {m['id']}"
    key = _next_key("ollama", cfg.get("keys", []))
    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    payload = {
        "model": m["id"],
        "messages": [
            {"role": "system", "content":
                "You are a crypto futures trading analyst. Respond ONLY with compact valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.4, "num_predict": 700},
    }
    try:
        r = requests.post(base + "/api/chat", headers=headers, json=payload, timeout=timeout)
    except Exception as e:
        _mark_fail("ollama", m["id"])
        return None, f"ollama unreachable ({m['id']}): {str(e)[:100]}"
    if r.status_code >= 400:
        _mark_fail("ollama", m["id"])
        return None, f"ollama/{m['id']}: HTTP {r.status_code} {r.text[:120]}"
    try:
        text = r.json()["message"]["content"]
        _mark_ok("ollama", m["id"])
        return text, m["id"]
    except Exception as e:
        _mark_fail("ollama", m["id"])
        return None, f"ollama parse: {e}"


def call_custom(prompt: str, timeout: float) -> tuple:
    cfg = CONFIG.get("ai", "custom", default={})
    if not cfg.get("enabled") or not cfg.get("base_url"):
        return None, "disabled"
    models = [m for m in cfg.get("models", []) if m.get("id")]
    m = _next_model("custom", models)
    if not m:
        return None, "no custom model configured"
    key = _next_key("custom", cfg.get("keys", []))
    text, err = _call_openai_style(cfg["base_url"], key, m["id"], prompt, timeout,
                                   reasoning=m.get("reasoning"))
    if err:
        _mark_fail("custom", m["id"])
        return None, f"custom/{m['id']}: {err}"
    _mark_ok("custom", m["id"])
    return text, m["id"]


def call_unorouter(prompt: str, timeout: float) -> tuple:
    cfg = CONFIG.get("ai", "unorouter", default={}) or {}
    if not cfg.get("enabled"):
        return None, "disabled"
    base = cfg.get("base_url", "https://api.unorouter.com/v1")
    models = list(cfg.get("models", [])) + list(cfg.get("backup_models", []))
    m = _next_model("unorouter", models)
    if not m:
        return None, "all unorouter models cooling down"
    key = _next_key("unorouter", cfg.get("keys", []))
    if not key:
        return None, "unorouter: no API key configured"
    text, err = _call_openai_style(base, key, m["id"], prompt, timeout,
                                   reasoning=m.get("reasoning"))
    if err:
        kind = classify_error(err)
        if kind == "dead_key":
            _mark_key_dead("unorouter", key, err)
            return None, "unorouter: API key invalid (401)"
        _mark_fail("unorouter", m["id"])
        if kind == "rate_limited":
            _health("unorouter", m["id"])["cooldown_until"] = time.time() + RATE_COOLDOWN
            return None, f"unorouter/{m['id']}: rate limited (free tier 1 req/min) - cooled 2 min"
        return None, f"unorouter/{m['id']}: {err}"
    _mark_ok("unorouter", m["id"])
    return text, m["id"]


CALLERS = {
    "groq": call_groq,
    "unorouter": call_unorouter,
    "openrouter": call_openrouter,
    "ollama": call_ollama,
    "custom": call_custom,
}


# ------------------------------------------------------------- JSON parse

def extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of an LLM reply (tolerant)."""
    if not text:
        return None
    text = text.strip()
    # strip code fences
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except Exception:
        pass
    # first balanced { ... }
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        break
        start = text.find("{", start + 1)
    return None


# ------------------------------------------------------------ main router

def ask_ai(prompt: str, max_attempts_per_provider: int = 3) -> dict:
    """
    Walk the provider chain (each provider gets `max_attempts_per_provider`
    tries, rotating its models/keys). Returns:
      {"ok": bool, "text": str|None, "provider": str, "model": str|None,
       "errors": [str], "elapsed": float}
    """
    t0 = time.time()
    timeout = CONFIG.get("ai", "request_timeout_sec", default=40)
    order = CONFIG.get("ai", "provider_order",
                       default=["groq", "openrouter", "ollama", "custom"])
    errors = []
    for prov in order:
        if prov == "local" or prov not in CALLERS:
            continue
        fn = CALLERS[prov]
        for _attempt in range(max_attempts_per_provider):
            text, info = fn(prompt, timeout)
            if text:
                return {"ok": True, "text": text, "provider": prov, "model": info,
                        "errors": errors, "elapsed": round(time.time() - t0, 2)}
            errors.append(str(info))
            if time.time() - t0 > timeout * 2.5:
                errors.append("global AI budget exhausted")
                return {"ok": False, "text": None, "provider": None, "model": None,
                        "errors": errors, "elapsed": round(time.time() - t0, 2)}
    return {"ok": False, "text": None, "provider": None, "model": None,
            "errors": errors, "elapsed": round(time.time() - t0, 2)}


def health_snapshot() -> dict:
    """Provider/model status for the GUI 'AI' tab."""
    out = {"providers": [], "checked_at": int(time.time())}
    for prov in ["groq", "openrouter", "unorouter", "ollama", "custom"]:
        cfg = CONFIG.get("ai", prov, default={}) or {}
        models = []
        for m in list(cfg.get("models", [])) + list(cfg.get("backup_models", [])):
            mid = m.get("id")
            if not mid:
                continue
            h = _health(prov, mid)
            models.append({
                "id": mid,
                "enabled": cfg.get("enabled", False),
                "ok_calls": h["ok"],
                "fails": h["fails"],
                "cooling_down": h["cooldown_until"] > time.time(),
                "cooldown_left_sec": max(0, int(h["cooldown_until"] - time.time())),
            })
        keys = [k for k in cfg.get("keys", []) if k]
        key_info = []
        for k in keys:
            with _lock:
                kh = _key_health.get((prov, k))
            dead = bool(kh and kh["cooldown_until"] > time.time())
            key_info.append({"preview": k[:8] + "..." + k[-4:],
                             "status": "INVALID/EXPIRED (cooldown 6h)" if dead else "ok",
                             "reason": (kh or {}).get("reason", "")[:80] if dead else ""})
        extra = {}
        if prov == "ollama":
            try:
                requests.get(cfg.get("base_url", "http://localhost:11434") + "/api/tags", timeout=2)
                extra["online"] = True
            except Exception:
                extra["online"] = False
                extra["hint"] = ("Ollama = 100% free local AI. Install from ollama.com, then: "
                                 "ollama pull llama3.1:8b")
        out["providers"].append({
            "name": prov,
            "enabled": bool(cfg.get("enabled")),
            "keys_configured": len(keys),
            "key_preview": [k[:8] + "..." + k[-4:] for k in keys],
            "keys": key_info,
            "models": models,
            **extra,
        })
    out["local_engine"] = {"name": "local", "enabled": True,
                           "note": "Built-in rule-based engine - always free, always works."}
    return out


def quick_test(provider: str) -> dict:
    """Send a tiny prompt through one provider -> connectivity report."""
    fn = CALLERS.get(provider)
    if not fn:
        return {"ok": False, "error": "unknown provider"}
    t0 = time.time()
    text, info = fn('Reply with JSON {"status":"ok"}', 25)
    return {"ok": bool(text), "model": info if text else None,
            "error": None if text else str(info),
            "elapsed": round(time.time() - t0, 2)}
