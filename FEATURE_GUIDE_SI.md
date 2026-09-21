# 🌊 AlphaWave — සම්පූර්ණ භාවිත මාර්ගෝපදේශය (Features Guide - සිංහලෙන්)

මෙය **වෙබ් ඇප් එකේ සහ Telegram bot එකේ ඇති සෑම feature එකක්ම වෙන වෙනම භාවිතා කරන
ආකාරය** සහ ඒවායේ හැඳින්වීමයි. (ස්ථාපනය ගැන නම්: `SETUP_GUIDE_SI.md`)

> ⚠️ AlphaWave යනු **analysis/signal tool එකකි** — auto-trading නොකරයි, orders නොදමයි,
> Binance API keys අවශ්‍ය නොවේ. Financial advice නොවේ.

---

## 📌 කොටස 1 — වෙබ් ඇප් එක (GUI) feature by feature

App එක start කළ පසු (http://127.0.0.1:8787) වම් පැත්තේ menu එකෙන් tab 10ක් ඇත.

### 1. 📊 Dashboard
* **හැඳින්වීම:** සමස්ත වෙළඳපොළ තත්ත්වය එකම තැනක.
* **භාවිතය:** tab එක විවෘත කළ ගමන් auto-load: BTC/ETH මිල සහ 24h %, Fear & Greed index,
  market breadth (coins 60ක් EMA20-4h ට උඩින්ද), futures volume, top gainers/losers,
  අලුත්ම signals සහ news. Coin නමක් click → chart එකට; ⚡ → එවලේම signal.

### 2. 🪙 Markets (සියලුම coins)
* **හැඳින්වීම:** Binance USDT-M futures වල සියලුම perpetual contracts (700+).
* **භාවිතය:** search box එකේ coin නම ලියන්න; sort: volume / 24h% / funding / name.
  row එකක: price, 24h%, high/low, volume, funding, trades.
  📈 button → chart · ⚡ button → එම coin එකට signal.

### 3. 📈 Chart & Indicators (live chart)
* **හැඳින්වීම:** TradingView-ශෛලී live chart එක — candles උඩ/පහල යනවා live.
* **භාවිතය:**
  1. coin එක + timeframe (1m–1d) තෝරා **Load / Watch** ඔබන්න
  2. **Style menu:** Candles · Hollow · Bars(OHLC) · Line · Area · Baseline · Heikin-Ashi
  3. **Overlays:** EMA9/20/50/200, Hull MA, Bollinger, Keltner, VWAP, SuperTrend,
     Parabolic SAR, Ichimoku, Pivot Points, Fib levels (checkbox on/off)
  4. **Sub-pane:** RSI, MACD, Stochastic, StochRSI, CCI, Williams %R, MFI, ADX+DI, OBV, ROC, ATR, CVD
  5. **▲▼ marks:** strategy buy/sell events chart එක උඩ
  6. **LIVE badge:** තත්පර 4කට වරක් අවසන් candle එක ගමන් කරයි; මිල flash වී ▲/▼
  7. ⬇ PNG → chart එක image එකක් ලෙස save.

### 4. 🎯 AI Signals (සිග්නල් ජනරේටරය)
* **හැඳින්වීම:** engines 21ක් + Accuracy Engine v2 + AI chain එකෙන් සම්පූර්ණ signal එකක්.
* **භාවිතය:**
  1. **💰 Account capital** දාන්න (උදා: 5000) + risk % → Save. එවිට සෑම signal එකකම
     **trade එකට risk කරන USDT ප්‍රමාණය, position qty, notional, margin** ලැබේ.
     (0 = off → පෙර පරිදි සාමාන්‍ය advanced signal)
  2. coin + timeframe + AI mode (assist/full/off) + strategies checkboxes
  3. **⚡ GENERATE SIGNAL**
* **Signal එකේ ඇතුළත් දේ:** coin, live price, LONG/SHORT, entry, stop loss (+SL method),
  take profit + TP1/2/3 ladder, confidence, R:R, recommended leverage (10–20x; extreme විට 20x+),
  capital sizing, HTF alignment, **📊 trade-plan chart image** (entry/SL/TP zones + methods +
  "Analyzed by AlphaWave" watermark), reason (strategy+technique+logic), trade ID + status.

### 5. 📥 Inbox (අලුත්ම!)
* **හැඳින්වීම:** ඔබේ සියලුම trades වල **live updates** එන තැන — trade එක close වෙනකම්.
* **ලැබෙන alerts:** ✅ TP hit · 🛑 SL hit · 💰 TP1 ladder suggestion (50% secure + SL→BE) ·
  🔁 SL update suggestion (structure trail) · 🎯 TP extend/ladder suggestion ·
  🚨 **market crash early warning (cancel කරන්න කියලා)** · ⏳ stale trade re-evaluate · ❎ cancelled.
* **භාවිතය:** tab එක විවෘත කරන්න — auto-refresh (8s). Admin නම් **සියලුම users ලාගේ**
  signals වල updates ද මෙතන පෙනේ. 🗑 = clear.

### 6. 🎲 Random Coin Funnel
* **හැඳින්වීම:** හොඳම coin එක තනිවම සොයා signal එකක්.
* **භාවිතය:** timeframe + AI mode තෝරා **FIND BEST COIN** → stages 4ක් live පෙනේ:
  best 1000 → top 100 → top 10 → **best 1** → සම්පූර්ණ signal + chart.

### 7. 📰 News & Fundamentals
* **භාවිතය:** coin filter එක දී **Load News** → RSS news + sentiment score,
  Fear & Greed card, Binance announcements.

### 8. 🧰 Tools 30
* **භාවිතය:** උඩින් coin එක දාලා tool card එකක් click කරන්න — ප්‍රතිඵලය පහළින්.
  (trend scanner, S/R, fib, orderflow, funding, OI, L/S ratio, liq zones, breadth, movers,
  spikes, breakout, divergence, MACD, supertrend, ribbon, ichimoku, VWAP, position size,
  R:R, liq price, funding cost, correlation, vol rank, news sentiment, dominance, journal, backtest)

### 9. 🤖 AI Providers
* **භාවිතය:** chain එකේ status (Groq 4 · OpenRouter 3+ · **Unorouter 6** · Ollama 2 · custom ·
  local 3), model cooldowns, **Test now** buttons, keys/models edit, AI mode save.
  Engines 21න් free local engines 3ක් ඇත: **NeuroQuant ML, Spectral FFT, Hurst R/S** — keys නැතුවම.

### 10. ✈️ Telegram Bot + 👥 Access Control
* **Bot:** token save → Start → Telegram එකේ භාවිතා කරන්න (පහත කොටස 2).
* **Access Control:** mode open/whitelist · IDs add (note සහිතව) · **bulk import** (IDs 100+
  paste කර එක click) · max users (default 1000 — ලිමිට් ප්‍රශ්න නැත) · admins · remove · counter.

---

## 📌 කොටස 2 — Telegram bot එක feature by feature

Bot එකට `/start` යැවූ ගමන් **ඔබේම personal dashboard එක** (buttons සහිත) විවෘත වේ.
Coin නමක් කෙලින්ම type කළොත් එය ඔබේ active coin එක වේ.

### Dashboard buttons
| Button | වැඩ |
|---|---|
| ⚡ SIGNAL {coin}·{tf} | ඔබේ coin/timeframe එකට signal + **trade-plan chart photo** |
| 🎲 RANDOM FUNNEL | 1000→100→10→1 funnel + signal + chart |
| 📈 CHART | indicators + ▲▼ marks සහිත chart PNG |
| 🔬 ANALYZE | engines 21ේ සම්පූර්ණ විශ්ලේෂණය |
| 📰 NEWS | coin news + sentiment |
| 🪙 COIN / ⏱ TF | ඔබේ active coin/timeframe වෙනස් කිරීම |
| 🧰 30 TOOLS | tools 30ම buttons ලෙස (ඔබේ coin එකට) |
| 🤖 AI / 🩺 STATUS / 🔄 / ❓ | chain health · system status · refresh · help |

### ප්‍රධාන commands (සියල්ලටම coin නම දිය හැක)
```
/signal SOL 1h     → signal + trade-plan chart
/random 15m        → best-coin funnel
/analyze ETH 4h    → full analysis      /chart DOGE 15m → chart PNG
/price BTC  /funding BTC  /oi BTC  /ls BTC  /trend BTC  /sr BTC  /fib BTC
/flow BTC  /liq BTC  /breadth  /movers  /spikes BTC  /breakout BTC
/divergence BTC  /macd BTC  /supertrend BTC  /ribbon BTC  /ichimoku BTC
/vwap BTC  /corr SOL  /volrank  /dominance  /journal 10  /backtest BTC 1h
/size 60000 58500 1000 1 10   → position size   /rr 60000 58500 64500
/liqprice 60000 10 long       /fundcost BTC 1000 long
/news BTC  /fear  /menu  /help  /status  /accuracy
/watch add BTC     → watchlist alerts
```

### 💰 Capital (අලුත්!)
```
/capital 5000      → ඔබේ account capital එක save (risk % default 1)
/capital 5000 2    → capital + 2% risk
/capital 0         → ඉවත් කරන්න (සාමාන්‍ය signals)
/capital           → දැනට ඇති capital එක + trade එකක risk USDT එක පෙන්වයි
```
Capital එක ඇති විට සෑම signal එකකම: **risk USDT/trade, qty, notional, margin** ලැබේ.

### 📡 Live trade updates (අලුත්!)
```
/trades            → ඔබේ open monitored trades + last update
/cancel T123456    → trade එක cancel (monitoring නවතී)
```
Trade එක open වී සිටින තුරු bot එක **automatically** මේවා යවයි:
* 🚨 **CRASH WARNING** — market එකක් කඩාගෙන යනවා නම් **කලින්ම** "trade එක cancel කරන්න" කියලා
* 🔁 **SL UPDATE** — අලුත් stop loss එකක් suggest වෙනවා නම් (structure trail)
* 💰 **TP1 LADDER** — TP1 ළඟා වූ විට "50% secure කර SL → break-even" කියලා
* 🎯 **TP UPDATE** — trend තවම ශක්තිමත් නම් TP extend/ladder කරන්න කියලා
* ✅/🛑 TP/SL hit → trade close වූ බව
* ⏳ trade එක කල් යට ගියොත් re-evaluate කරන්න කියලා
**Admin ලාට:** ඕනෑම user කෙනෙකුගේ (web හෝ bot) සියලුම signals වල updates ද ලැබේ.

### 👥 Multi-user access (IDs 100+)
```
/request           → whitelist එකේ නැති කෙනෙක් access ඉල්ලන්න (admin ට Approve button එකක් යයි)
/allow 123456789 Nimal   → (admin) user add
/revoke 123456789        → (admin) user remove
/users                   → (admin) list + counter
/accessmode open|whitelist → (admin) mode මාරු
```
GUI Access Control panel එකෙන් ද IDs 100ක්+ bulk import කළ හැක (max_users default 1000).

### 🔒 Content Protection (signal ආරක්ෂාව)
Bot එක යවන **සෑම message එකක්ම** (signals, charts, alerts, dashboards) Telegram හි
**protected content** ලෙස සලකුණු වේ — official Telegram apps වල:
* ❌ **Forward කිරීම බැත** (protect_content flag)
* ❌ **Copy / select කිරීම බැත**
* ❌ **Save / download කිරීම බැත** (media)
* ❌ **Screenshot ගැනීම block වේ** (official iOS/Android/desktop clients)
* 🔍 සෑම signal එකකම **per-user watermark** එකක් ඇත ("licensed to <ඔබේ ID>") —
  leak එකක් වුවහොත් කවුදැයි හොයාගත හැක
* 🚫 Signals **DM-only** වේ — groups/channels වල bot එක වැඩ නොකරයි (leak එක නැත)

Settings: `config.json → telegram.protect_content` (on/off), `telegram.allow_groups`
(groups වලට ද අවශ්‍ය නම් true කරන්න).
> සටහන: modified/third-party Telegram clients වලට සීමාවන් මඟහැරවිය හැක —
> Telegram platform එකෙන්ම ලබාදෙන උපරිම ආරක්ෂාව මෙයයි.

---

## 📌 කොටස 3 — හැඳින්වීම් (කෙටි ග්ලොසරි)

* **Engines 21:** ඔබේ methods 8 (Order Flow, Niyowew, MNSR, SMC, ICT2022, Eliyat Vew, SK, Y-KOF)
  + 10 (Ichimoku, Keltner/TTM, Candlesticks, Wyckoff, Pivots, ADX/DI, Stochastic, OBV,
  Golden Pocket, Funding Contrarian) + **free local 3** (NeuroQuant ML, Spectral FFT, Hurst R/S)
* **Accuracy Engine v2:** walk-forward weights + live TP/SL outcome learning + HTF gate + quality gates
* **AI chain:** Groq → OpenRouter → **Unorouter** → Ollama → custom → local (කිසිදා නතර නොවේ)
* **Leverage policy:** 10–20x සාමාන්‍ය; 20x+ = extreme setups පමණි
* **Trade Monitor:** සෑම signal එකක්ම TP/SL/cancel වෙනකම් live නිරීක්ෂණය

**සුබ trades! 🌊📈**
