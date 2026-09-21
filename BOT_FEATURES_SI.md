# ✈️ AlphaWave Telegram Bot — සියලුම Features වෙන වෙනම සිංහලෙන් පැහැදිලි කිරීම

මෙම ගොනුවේ **bot එකේ ඇති සෑම feature එකක්ම** (commands 52 + dashboard buttons +
auto-alerts) වෙන වෙනම, උදාහරණ සහිතව පැහැදිලි කර ඇත.
(ස්ථාපනය: `SETUP_GUIDE_SI.md` · වෙබ් ඇප් එක: `FEATURE_GUIDE_SI.md`)

> ⚠️ Bot එක analysis/signal මෙවලමකි — orders නොදමයි · Binance keys නොගනී ·
> financial advice නොවේ. සෑම message එකක්ම **protected** වේ (forward/copy/screenshot බැත).

---

## 1️⃣ ඔබේ Personal Interface එක (Dashboard)

ඕනෑම කෙනෙක් `/start` යැවූ විට **ඔහුටම ආවේණික dashboard message එකක්** buttons සහිතව
ලැබේ. එයින් ඔබේ active coin එකට සියල්ල එක click එකෙන්:

| Button | පැහැදිලි කිරීම |
|---|---|
| **⚡ SIGNAL {coin}·{tf}** | ඔබේ active coin එකට + timeframe එකට සම්පූර්ණ AI signal එකක් ජනරේට් කරයි (engines 21 + AI chain). signal text එක + **trade-plan chart photo** එක (entry/SL/TP zones සහිත) ලැබේ |
| **🎲 RANDOM FUNNEL** | coin එකක් තෝරන්නේ නැතුව — හොඳම 1000 → 100 → 10 → **1** funnel එක run කර හොඳම coin එකට signal + chart ලබා දේ |
| **📈 CHART** | ඔබේ coin එකේ candlestick chart PNG එකක්: EMA20/50+VWAP, RSI pane, ▲▼ buy/sell marks සහිතව |
| **🔬 ANALYZE** | engines 21ම ඔබේ coin එක මත run කර engine-by-engine votes + confluence summary එකක් පෙන්වයි |
| **📰 NEWS** | ඔබේ coin එකට අදාළ fundamental news + sentiment score |
| **🪙 COIN: {coin}** | ඔබේ **active coin එක වෙනස් කිරීමට** — click කළ පසු coin නම type කරන්න (උදා: `SOL`) |
| **⏱ TF: {tf}** | timeframe එක cycle කරයි: 5m → 15m → 30m → 1h → 4h |
| **🧰 30 TOOLS** | trading/analysis tools 30ම **buttons ලෙස** — tap කළ ගමන් ඔබේ coin එකට result |
| **🤖 AI** | AI chain එකේ health එක (Groq/OpenRouter/Unorouter/Ollama/local) |
| **🩺 STATUS** | Binance connection, AI mode, ඔබේ coin — කෙටි system status |
| **🔄 REFRESH** | dashboard එක අලුත් කරයි (මිල, funding, 24h%) |
| **❓ HELP** | සියලුම commands ලැයිස්තුව |

**💡 Session එක:** ඔබේ coin/timeframe තේරීම ඔබටම පෞද්ගලිකයි — වෙනත් users ලාගේ
තේරීම් සමඟ ව්යාකූල නොවේ.

---

## 2️⃣ Coin නම Type කිරීම (ඕනෑම තැනක)

* Bot chat එකේ **coin නමක් කෙලින්ම type** කරන්න — උදා: `SOL`, `eth`, `DOGEUSDT` →
  එය ඔබේ active coin එක වී dashboard එක අලුත් වේ. ඉන්පසු සියලු buttons/tools එම coin එකටයි.
* `/coin SOL` — එකම කාර්යය command එකෙන්.
* ඕනෑම command එකකට coin එක දිය හැක: `/signal SOL 1h`, `/chart DOGE 15m` …
  (coin නොදුන්නොත් ඔබේ active coin එක භාවිතා වේ)

---

## 3️⃣ Signal Features

### `/signal [COIN] [TIMEFRAME]`
* **කරන්නේ:** engines 21ක් + Accuracy Engine v2 + AI chain (Groq→OpenRouter→Unorouter→
  Ollama→local) භාවිතයෙන් සම්පූර්ණ signal එකක් ජනරේට් කරයි.
* **උදා:** `/signal BTC 15m` · `/signal ETH` (tf නැත්නම් ඔබේ TF) · `/signal` (active coin)
* **ලැබෙන දේ:** coin · side (LONG/SHORT) · live price · entry · **stop loss (+SL method)** ·
  take profit + TP1/2/3 ladder · confidence % · R:R · **recommended leverage (10–20x, extreme විට 20x+)** ·
  capital දාලා තිබේ නම් **risk USDT/qty/margin** · HTF bias · **reason** (කුමන strategy/technique/logic ද) ·
  trade ID · ඉන්පසු **trade-plan chart photo** එක · 🔒 watermark.

### `/random [TIMEFRAME]`
* **කරන්නේ:** Random-coin funnel — best 1000 (volume) → top 100 (liquidity+range score) →
  top 10 (1h structure scan) → **best 1** (full confluence) → signal.
* **උදා:** `/random 15m`
* **ලැබෙන දේ:** stage-by-stage progress message එක, finalists ලැයිස්තුව, අවසාන signal + chart.

### `/journal [N]`
* **කරන්නේ:** ඔබේ/සියල්ලන්ගේ ජනරේට් වූ signals ඉතිහාසය (journal එක) පෙන්වයි.
* **උදා:** `/journal 10` → අලුත්ම signals 10ක් (side, levels, confidence සහිතව).

### `/backtest COIN [TF]`
* **කරන්නේ:** EMA9/21 cross + RSI filter strategy එක candles 500ක backtest කරයි
  (0.05% fee සහිත) — win rate, trades count, net return, equity curve.
* **උදා:** `/backtest BTC 1h`

---

## 4️⃣ විශ්ලේෂණ (Analysis) Features — engine-by-engine

සෑම command එකක්ම ඔබේ coin එක (හෝ ලියන coin එක) මත එක් විශ්ලේෂණ ක්‍රමයක් run කරයි:

| Command | පැහැදිලි කිරීම · උදාහරණ |
|---|---|
| `/analyze COIN TF` | **සම්පූර්ණ විශ්ලේෂණය** — engines 21ේ votes, weights, confluence side/confidence. උදා: `/analyze ETH 1h` |
| `/accuracy [COIN] [TF]` | **ඉගෙන ගත් weights** — engine එකක් මේ coin/TF එක මත කොතරම් නිවැරදිද (walk-forward + live win/loss record). උදා: `/accuracy BTC 15m` |
| `/trend COIN` | timeframes 4ක (15m/1h/4h/1d) trend එක + ADX — "සියල්ල එක පැත්තකද?" බලයි. උදා: `/trend BTC` |
| `/sr COIN` | MNSR support/resistance levels (touches සහිත clusters). උදා: `/sr ETH` |
| `/fib COIN` | Fibonacci retracements + extensions + **OTE zone** (61.8–79%). උදා: `/fib SOL` |
| `/flow COIN` | Order flow: CVD, delta, taker buy/sell ratio — "aggressive buyers ද sellers ද". උදා: `/flow BTC` |
| `/liq COIN` | liquidity/liquidation zones — ඉහළ/පහළ stop-loss pools (price raids කරන තැන්). උදා: `/liq DOGE` |
| `/divergence COIN` | RSI divergence scan (price vs RSI විරුද්ධ වීම = reversal හැඟවීම). උදා: `/divergence ETH` |
| `/macd COIN` | MACD cross/momentum තත්ත්වය. උදා: `/macd BTC` |
| `/supertrend COIN` | SuperTrend direction + අලුත්ම flip එක කවදාද. උදා: `/supertrend SOL` |
| `/ribbon COIN` | EMA 9/20/50/100/200 alignment (perfect bull/bear stack ද). උදා: `/ribbon BTC` |
| `/ichimoku COIN` | Ichimoku cloud: price vs cloud, TK cross, Senkou bias. උදා: `/ichimoku ETH` |
| `/vwap COIN` | VWAP deviation — overextended ද fair value ද. උදා: `/vwap BTC` |
| `/spikes COIN` | අලුත්ම volume spikes (2x+ average) — candle color + delta සහිතව. උදා: `/spikes PEPE` |
| `/breakout COIN` | Donchian breakout + Bollinger squeeze තත්ත්වය. උදා: `/breakout SOL` |
| `/corr COIN` | BTC/ETH සමඟ correlation — "BTC වැටුණොත් මේකත් වැටෙනවාද?". උදා: `/corr AVAX` |

---

## 5️⃣ වෙළඳපොළ තොරතුරු (Market Info)

| Command | පැහැදිලි කිරීම · උදාහරණ |
|---|---|
| `/price COIN` | live price, mark price, 24h %, high/low, volume, funding. උදා: `/price BTC` |
| `/funding COIN` | funding rate + next funding time + "longs pay / shorts pay" අර්ථය. උදා: `/funding ETH` |
| `/oi COIN` | Open Interest + 24h change — "අලුත් සල්ලි එනවාද positions unwind ද". උදා: `/oi BTC` |
| `/ls COIN` | top traders long/short ratio + global taker ratio. උදා: `/ls SOL` |
| `/fear` | Crypto Fear & Greed index + interpretation. උදා: `/fear` |
| `/breadth` | market breadth — coins 60ක් 4h EMA20 ට උඩින්ද → risk-on/risk-off regime. උදා: `/breadth` |
| `/movers` | 24h top gainers 10 + losers 10. උදා: `/movers` |
| `/volrank` | 24h range අනුව volatile ම coins 15 + ඔබේ coin එකේ rank එක. උදා: `/volrank` |
| `/dominance` | BTC/ETH futures volume dominance snapshot. උදා: `/dominance` |
| `/news [COIN]` | RSS news + per-article sentiment + coin filter. උදා: `/news BTC` |

---

## 6️⃣ Chart Feature

### `/chart [COIN] [TF]`
* **කරන්නේ:** server එකේ render වූ **candlestick chart PNG** එකක් photo ලෙස යවයි —
  EMA20/50 + VWAP overlays, volume pane, RSI pane, **▲▼ strategy buy/sell events**,
  කොනේ "Analyzed by AlphaWave" watermark.
* **උදා:** `/chart BTC 1h` · `/chart DOGE 15m` · `/chart` (active coin)

---

## 7️⃣ Calculators (risk management)

| Command | පැහැදිලි කිරීම · උදාහරණ |
|---|---|
| `/size ENTRY SL [BALANCE] [RISK%] [LEV]` | position size: risk USDT, qty, notional, margin. උදා: `/size 60000 58500 1000 1 10` |
| `/rr ENTRY SL TP` | risk:reward ratio + breakeven win rate + verdict. උදා: `/rr 60000 58500 64500` |
| `/liqprice ENTRY LEV SIDE` | estimated liquidation price + distance %. උදා: `/liqprice 60000 10 long` |
| `/fundcost COIN [NOTIONAL] [SIDE]` | funding cost per funding / per day. උදා: `/fundcost BTC 1000 long` |

---

## 8️⃣ Account Capital Feature 💰

### `/capital [USDT] [RISK%]`
* **කරන්නේ:** ඔබේ account capital එක bot එකට දන්වයි. එවිට **සෑම signal එකකම**
  trade එකට risk කළ යුතු **USDT ප්‍රමාණය**, position qty, notional, margin ලැබේ.
* **උදා:** `/capital 5000` → 1% risk = 50 USDT/trade · `/capital 5000 2` → 2% = 100 USDT
* `/capital` (arguments නැතුව) → දැනට ඇති capital එක + per-trade risk පෙන්වයි
* `/capital 0` → ඉවත් කරයි → signals පෙර පරිදි සාමාන්‍ය advanced mode එකෙන්.

---

## 9️⃣ Live Trade Monitoring + Auto Alerts 📡

Signal එකක් ජනරේට් වූ ගමන් එය **trade එකක් ලෙස register** වී close වෙනකම් (TP/SL/cancel)
monitor වේ. Updates **automatically** ලැබේ:

| Alert එක | කවදාද · කියන්නේ මොකක්ද |
|---|---|
| 🚨 **CRASH WARNING** | market එකක් ඔබට විරුද්ධව හදිසියේ කඩාගෙන යනවා නම් — **"trade එක cancel කරන්න"** කියලා **කලින්ම** දැනුම් දේ (threshold: 3 candles වල ATR×2.5+ විරුද්ධ move) |
| 🔁 **SL UPDATE** | price ඔබේ පැත්තට ගිය පසු අලුත් structure එකට අනුව **හොඳ (trailing) SL එකක්** suggest වේ — අගය සහිත alert එකක් |
| 💰 **TP1 LADDER** | TP1 (1.2R) ළඟා වූ විට: "50% secure කරන්න + SL → break-even + runner තියන්න" කියලා ladder plan එක |
| 🎯 **TP UPDATE** | HTF trend තවම ශක්තිමත් නම්: TP එක extend කරන්න හෝ 1/3 ladder කරන්න කියලා suggestion එක |
| ✅ **CLOSED_TP** | take profit hit → trade close (ලාභ ~+R පෙන්වයි) — alerts නවතී |
| 🛑 **CLOSED_SL** | stop loss hit → trade close (−1R) — alerts නවතී |
| ⏳ **EXPIRE** | candles 72ක් යනතුරු TP/SL නොවැදුණොත් — "re-evaluate / cancel කරන්න" |
| ❎ **CANCELLED** | ඔබ cancel කළ බව තහවුරු කිරීම |

### `/trades`
* ඔබේ **open monitored trades** සියල්ල: entry/SL/TP, last update kind, updates ගණන, cancel hint.
### `/cancel TRADE_ID`
* trade එක cancel කරයි → monitoring නවතී → ❎ alert එකක් + web Inbox එකට ද වැටේ.

> **Admin ලාට:** ඕනෑම user කෙනෙකුගේ (bot හෝ web) සියලුම signals වල updates ද Telegram එකෙන්ම ලැබේ.
> සියලු alerts web app එකේ **📥 Inbox** එකට ද එකසේ වැටේ.

---

## 🔟 Watchlist Feature 👀

### `/watch add|del|list [COIN]`
* **කරන්නේ:** coins watchlist එකකට දාලා **හොඳම confluence එකක් (≥70%, engines ≥4) ආ විට
  auto alert** එකක් ලබා ගැනීම (සෑම ~3 min scan එකකම; coin එකකට 30 min cooldown).
* **උදා:** `/watch add BTC` · `/watch del BTC` · `/watch list`

---

## 1️⃣1️⃣ AI Management 🤖

| Command | පැහැදිලි කිරීම · උදාහරණ |
|---|---|
| `/aimode assist\|full\|off` | AI mode මාරු කිරීම: **assist** = TA තීරණය කරයි, AI ලියයි · **full** = AI ට levels adjust කළ හැක · **off** = 100% free local engines පමණි. උදා: `/aimode off` |
| `/aistatus` | providers/model health: keys, ok-calls, cooldowns, local engine note. උදා: `/aistatus` |
| `/aitest PROVIDER` | provider එකක් live test කරයි (model + latency). උදා: `/aitest groq` |

---

## 1️⃣2️⃣ Access Management (Admin) 👥

| Command | පැහැදිලි කිරීම · උදාහරණ |
|---|---|
| `/allow ID [NOTE]` | (admin) user කෙනෙකුට access දෙයි. උදා: `/allow 123456789 Nimal` |
| `/revoke ID` | (admin) access අහිමි කරයි. උදා: `/revoke 123456789` |
| `/users` | (admin) whitelist එක + counter (x/max) + notes/dates. උදා: `/users` |
| `/accessmode open\|whitelist` | (admin) ඕනෑම කෙනෙක් / ලියාපදිංචි අය පමණක්. උදා: `/accessmode whitelist` |
| `/request` | (user) whitelist එකේ නැති කෙනෙක් access ඉල්ලයි → admin ට **✅ Approve button** එකක් යයි → approve වූ ගමන් user ට "access approved — /start කරන්න" message එකක් |

> GUI එකේ **Access Control panel** එකෙන් ද IDs 100+ (max default 1000) bulk import කළ හැක.

---

## 1️⃣3️⃣ Button Menu එක 🧰

### `/menu`
* **කරන්නේ:** tools 30ම **inline buttons** ලෙස pages 3කින් පෙන්වයි (+ quick buttons:
  Signal / Random / Chart / News). Button එකක් tap කළ ගමන් **ඔබේ active coin එකට**
  එම tool එක run වී result එක එම තැනම පෙනේ.
* **උදා tools:** trend scanner, S/R levels, fib+OTE, order flow, funding, OI, L/S ratio,
  liq zones, Fear&Greed, breadth, movers, volume spikes, breakout, divergence, MACD,
  SuperTrend, EMA ribbon, Ichimoku, VWAP, position size, R:R, liq price, funding cost,
  correlation, vol rank, news sentiment, dominance, journal, backtest.

---

## 1️⃣4️⃣ රක්ෂාව 🔒 (Content Protection)

* Bot එක යවන **සියලුම messages**: Telegram **protected content** — official apps වල
  **forward ❌ · copy ❌ · save ❌ · screenshot **.
* සෑම signal එකකම **per-user watermark**: "licensed to <ඔබේ ID>" → leak tracing.
* **DM-only**: groups/channels වල bot එක වැඩ නොකරයි (leak prevention).
* Settings: `config.json → telegram.protect_content` / `telegram.allow_groups`.

---

## 1️⃣5️⃣ උපදෙස් සහ සීමාවන් ⚠️

* Messages protected නිසා **ඔබටම signal එක copy කරගැනීම ද බැත** — අවශ්‍ය නම් web app එකේ
  Inbox/Signals tab එකෙන් (ඔබේම terminal එක) බලන්න.
* Bot එක **orders නොදමයි** — entry/SL/TP/leverage ඔබේ exchange එකේ ඔබම ඇතුළත් කරන්න.
* Signals = analysis පමණි; confidence ඉහළ වුවත් වෙළඳපොළ අවදානම සැමවිටම පවතී.
* ගැටලුවක් නම්: web GUI → Bot tab → **Bot logs** panel එක බලන්න (401 token / 409 conflict
  වගේ දෝෂ පැහැදිලිව සඳහන් වේ).

**සුබ trades! 🌊📈**
