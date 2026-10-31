# EUR/USD auto backtest — Historical data pipeline

**Status:** Source code deployed; real-data backtest only becomes valid after a successful GitHub Actions run. No real trading and no Kronos model inference.

This repository automatically retrieves historical EUR/USD H1 Bid/Ask candles from Dukascopy with the `dukascopy-node` library. The strategy is fixed Donchian 18 with ATR14 stop 1.9×, take-profit 2.8×, maximum 48 hours holding, position risk 0.5% of equity, maximum effective leverage 5× and lot step 0.01. An indicative Exness Standard **cost scenario** uses 0.8 pip fixed spread, 0.1 pip slippage per side and zero commission; swap is assumed zero, not verified. Stress runs repeat the full OOS period with spreads of 1.2 and 2.0 pips.

## Automated runs

Click [Actions](https://github.com/thietk-stack/eurusd-auto-backtest/actions/workflows/backtest.yml) → **EURUSD historical download and 2000 trade backtest** → **Run workflow** if you want an additional manual attempt. The workflow runs on supported source-code pushes and can also be started manually. The one-off full-history run completed on 2026-10-30; unnecessary daily reruns have been disabled. It downloads a bounded number of months per run and caches previously verified months, to avoid starting over after timeouts. If data are missing or downloaded trade count is less than 2,000, it exits non-successfully and marks the output INCOMPLETE.

For successful runs, open the `eurusd-report` artifact and inspect `RESULTS.json`, `BAO_CAO_VI.md`, and the exact trade CSVs. The first 2,000 trades must be chronological and out of sample, never selected by profit. No market observations are fabricated when data are missing.

## Run with GitHub Codespaces

Choose Code → Codespaces → Create codespace; run `bash run.sh`. This is useful when a longer-lived environment is necessary to process the full history.

## Caveats

- **Not Exness broker data.** Bid and Ask are Dukascopy observations; actual historical Exness spreads, slippage and swap are different.
- **No Kronos AI executed.** Strategy is a fixed technical benchmark.
- H1 OHLC cannot reconstruct the exact order of intrabar ticks; both stop and target touched is treated as a stop first. Other fill assumptions remain approximations.
- Goal of 8% profit every month is a **research benchmark**, not a guarantee or a result.
- Public source repository contains no account credentials, API keys or live brokerage integrations.

References: [dukascopy-node](https://github.com/Leo4815162342/dukascopy-node), [Exness](https://www.exness.com/)

## Completed historical benchmark

[**Đọc báo cáo thật: 2.000 lệnh + toàn bộ OOS**](BAO_CAO_KIEM_DINH_2000.md) · [GitHub Actions run #3](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41083461646) — verified successful run, 104,967 H1 candles, 3,113 full-OOS trades, negative all-OOS return. No 8%/month edge demonstrated.

## Bounded three-strategy follow-up research (2026-10-30)

[Đọc báo cáo vòng 2](BAO_CAO_NGHIEN_CUU_VONG_2.md) · [Kết quả GitHub Actions](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41085764980). Tested trend filter, mean reversion and UTC session breakout against Donchian18 on actual historical Dukascopy EURUSD H1 (not Exness tick history). **None met the precommitted validation criterion. No 5–8% monthly edge has been demonstrated.** Live trading is not enabled.

## Four-pair quantitative portfolio research (2026-10-30)

- [**Báo cáo kết quả bốn cặp Forex**](BAO_CAO_DANH_MUC_4_CAP.md)
- [Đề cương nghiên cứu được đóng băng](DE_CUONG_DANH_MUC_4_CAP.md)
- [GitHub Actions: verified run and trade ledgers](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41088543737)

Downloaded real Dukascopy H1 Bid/Ask candles for EUR/USD, GBP/USD, AUD/USD, USD/JPY (42,589 common observations; 246/246 additional monthly records verified). Evaluated weekly time-series momentum, cross-sectional currency strength, and equal-weight control. **The selected momentum strategy lost money on 2023–2026 held-out prices after simulated costs. No reliable 5–8% monthly return was demonstrated.** Research only, no live orders, carry/rollover not modeled.

## Pure price action: four-touch hard support/resistance zones (2026-10-30)

- [Fixed zone/reversal rules before testing](DE_CUONG_PRICE_ACTION_VUNG_CUNG.md)
- [Verified final comparative report](BAO_CAO_PRICE_ACTION_VUNG_CUNG.md)
- [GitHub Actions completed study](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41092879699)

Two different causal rules: 4 confirmed touches/reversals with the same support or resistance role; and 4 confirmed reactions including both support and resistance (role flips). Fixed 0.5% intended per-position risk, after-cost RR >=1.5, maximum one trade/week across all four FX pairs, NO live trading. **Same-role: -1.06% validation and -2.77% holdout; mixed-role: +2.58% validation but -4.71% holdout. Neither demonstrated durable edge.** Prices are real historical Dukascopy H1, not Exness tick fills. No swap/rollover model.

## H4/D1 hard zones + H1 body engulfing (30 Oct 2026)

- [Full audited Vietnamese report](BAO_CAO_HTF_H4_D1_ENGULFING.md)
- [Frozen method / risk and exit rules](DE_CUONG_HTF_H4_D1_ENGULFING.md)
- [Successful GitHub Actions run and source CSV ledgers](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41094413654)

Tested 4 preregistered strategies on genuine historical Dukascopy bid/ask H1 across four currency pairs. Hard zone required >=4 confirmed price reversals on H4/D1; entries required next H1 open after closed body engulfing; SL placed beyond farther of zone edge or engulfing wick plus 1.5 pips, TP gross 2R capped by existing opposing zone, no orders if after-cost RR <1.5, 0.5% equity risk budget, <=1 entry per week across all pairs. **None met validation-and-holdout criteria; no real trading enabled.** No Exness tick/rollover data, no 5–8% monthly edge shown.

## Year-by-year price action LIMIT midpoint entry (2019–2025)

- [Báo cáo kiểm định 7 năm 2019–2025: H4/D1, engulfing H1, LIMIT 50%, SL ±1 pip](BAO_CAO_LIMIT_50_ENGULFING_2019_2025.md)
- [Pre-registered detailed rule changes](DE_CUONG_LIMIT_50_ENGULFING_2019_2025.md)
- [Successful GitHub Actions with all 28 yearly CSV ledgers](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41095941707)

Data: 49,877 common H1 observations from real Dukascopy historical Bid/Ask for EUR/USD, GBP/USD, AUD/USD and USD/JPY. Backtested seven separate calendar years with $1,000 initial simulated balance **reset for each year**, 4 price-action zone modes and spread stress tests. BUY limit at 50% of full bullish engulfing High–Low, SL 1 pip below its wick; symmetric SELL. Orders have **12 observed H1 bar expiry** and may never fill; 0.5R risk budget, projected net R:R >= 1.5. **None showed reliably positive yearly returns**. No real trading or broker credentials; missing real Exness tick/slippage/swap data. Not a profit guarantee.

## Corrected H1 vs H4 engulfing signals: limit only in NEXT matching candle (Oct 30, 2026)

- [Báo cáo đúng yêu cầu: bảng 2019–2025, tám phiên bản, 1.078 lệnh được khớp](BAO_CAO_H1_H4_ENGULFING_LIMIT_1_NEN.md)
- [Frozen detailed research rules](DE_CUONG_ENGULFING_H1_H4_NEN_KE_TIEP.md)
- [Successful GitHub Actions and all 56 audited CSVs](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41098333270)

H1 engulfing orders wait only for the next ONE H1 bar. H4 engulfing orders wait only for the next ONE H4 bar, evaluated using its underlying four real H1 observations. They are separate candle-pattern timeframes, never a shared H1 signal waiting 4 hours. Both use the midpoint of the **full signal candle range**, stop 1 pip beyond its wick, minimum projected net 1.5 R:R and intended 0.5% equity risk. **None produced a reliable seven-year edge**. Dukascopy H1 OHLC cannot verify exact broker tick fill order or financing, and no live trades are enabled.

## Strict engulfing filter: 2x previous full candle and absolutely no wicks (2019–2025)

[**Vietnamese verified report**](BAO_CAO_ENGULFING_2X_KHONG_RAU_2019_2025.md) · [GitHub Actions](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41099890038). 4 Forex pairs, H1 and H4 engulfing, unchanged next matching candle 50%-range limit. Only **3 H1 and 2 H4 engulfing candles** satisfied the extra strength and zero-wick filter; one limit was placed, none filled after HTF 4-touch qualification. No performance inference is possible from zero fills. No live orders or broker keys.

## New experiment — strong engulfing body >=2× previous body, each wick <=5% (2019–2025)

[Locked protocol](DE_CUONG_ENGULFING_THAN2X_RAU5.md) · [Test source](scripts/htf_engulf_body2x_wick5.py) · [GitHub Actions execution](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41100790578). Keeps the preceding H1/H4 next-candle-only 50% limit entry, H4/D1 four-touch zones, 1-pip wick-based stop, net 1:1.5 minimum planned RR and 0.5% equity designed risk. Neither financial performance nor number of successful fills may be assumed until the workflow outputs a verified report. No live trading.

## Latest research: M15 only, 3 confirmed touches within 10 M15 candles, 2R TP (2026-10-30)

- [**Verified seven-year report (2019–2025)**](BAO_CAO_M15_3_CHAM_10_NEN_TP2R_2019_2025.md)
- [Frozen M15-only three-touch specifications](DE_CUONG_M15_3_CHAM_TOI_DA_10_NEN_2R.md)
- [Successfully completed GitHub Actions with annual source CSVs](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41104800811)
- [Implementation: no H4/D1 zones whatsoever](scripts/m15_three_touch_engulf_2r.py)

Three distinct M15 price-zone reactions: two confirmed same-side pivots and one finished strong M15 engulfing, **2–10 bars apart between consecutive touches**, within a reproducible zone tolerance. Mid-candle LIMIT only during next M15 candle, wick ±1 pip stop, **projected net R:R = 2.0 take profit**, 0.5% intended risk and at most one filled trade/week for four FX pairs. Genuine Dukascopy M15 Bid/Ask, not H1 interpolation. 2019–2025: **53 orders, 13 actual fills, 1 winner, 12 losers; aggregate −$19.33 across seven independent annual $1k simulations**. The strategy **did not demonstrate an edge** and is not connected to a live broker. Keep earlier H4/D1 scripts only for reproducible historical comparisons, not as filters in this new system.

## QuantMind FX — probability-first research with AI and historical case memory (2026-10-31)

- [**Báo cáo kiểm định dự báo xác suất 2019–2025 / NO-GO**](BAO_CAO_QUANTMIND_XAC_SUAT_2019_2025.md)
- [Pre-registered protocol with 2023 calibration/validation split](DE_CUONG_QUANTMIND_FX_XAC_SUAT.md)
- [Verified successful 4-pair ML backtest + 18,598 probability forecasts and CSVs](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41142808221)
- [Executable causal H1 model and historical-case analog veto](scripts/quantmind_probability.py)

Data: real Dukascopy 2018–2025 verified four-pair H1 quote history; 24,898 training event labels (2019–22), 3,094 calibration labels (2023H1), 3,072 validation predictions (2023H2), 12,432 chronological holdout predictions (2024–25). Main classifier plus 40 nearest historical analogs and disagreement veto, 2R net TP / 1R net SL, estimated 0.5% equity risk, no more than one entry a week. **Validation AUC 0.514, later period AUC 0.508, Brier worse than training-prior baseline, predicted maximum probability below 2R breakeven, ZERO eligible trades.** The conclusion is NO-GO. No live execution or ChatGPT API calls per candle; assistant's involvement was in strategy architecture, historical research, and audit. Older backtests in this repository are research comparisons, not previously proven profitable strategies.

## Latest — QuantMind v2 on authentic 1-minute quotes (31 Oct 2026)

- [**Full audited 15-month report — disappointing results and methodology diagnosis**](BAO_CAO_QUANTMIND_V2_M1_15_THANG.md)
- [Fixed research protocol for monthly validation and later tests](DE_CUONG_QUANTMIND_V2_15_THANG.md)
- [All 15 SHA-verified M1 month studies and successful cohort aggregation](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41143864924)
- [Genuine M1 bid/ask execution-quote false-break/reclaim implementation](scripts/quantmind_m1_reclaim.py), [regression tests](tests/test_quantmind_m1_reclaim.py), [strict 15-month aggregation](scripts/aggregate_quantmind_m1.py)

Real Dukascopy BID/ASK M1 on EURUSD GBPUSD AUDUSD USDJPY, **no synthetic M1 from H1**, false-break reclaim at previous 60-bar range, spread-normalization, 2R nominal net TP and 0.5% intended equity risk. January 2024 pilot excluded from later cohort. Four sample months in 2022, four in 2023 validation and seven in 2024–25 later test; each month resets a $1k simulated portfolio. Reversal: **20 trades, −$3.43** in 2022; **19 trades, −$4.85** in validation; **35 trades, −$15.16** in later test (PF 0.617, 8 wins). Extra-spread stress worsens later PnL to −$23.04. Main diagnostic: **67 of all 74 reversal orders occur Monday** because the one-entry-per-week rule selects the first eligible signal; results describe this specific time-biased policy, not all reclaim events. Conclusion **NO-GO** and no broker orders. Bid/Ask candles are not centralized FX order book and cannot prove institutional liquidity sweeping.

## Latest 31 Oct 2026: EconEdge hypothesis grounded in economic trend evidence

- [**Audited tradeable-size weekly trend-vs-opposite test, 2019–2025**](BAO_CAO_ECONEDGE_XU_HUONG_TUAN_2019_2025.md)
- [Frozen pre-run protocol](DE_CUONG_ECONEDGE_TREND_TUAN_2019_2025.md)
- [Successful GitHub Actions with main 6 trade/decision ledgers](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41151384843)
- [**Additional post-hoc 278-signal weekly direction diagnostic**](BAO_CAO_ECONEDGE_DAU_HIEU_HOI_QUY_TRUNG_BINH.md) · [Successful diagnostic workflow](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41151534226)

The week-ahead momentum strategy uses 480 PREVIOUSLY CLOSED real H1 bars and a fixed Monday 08 to Friday 20 UTC holding period, no mandatory 2R take profit, 0.5% equity risk, 5× notional cap, minimum 0.01 lot. Signals are compared with opposite-direction trades on the same FX pair and calendar week. Main validation 2022–23 had ONLY ONE eligible trade (−$3.90); later 2024–25 trend earned +$20.57 on only 10 trades, but the weekly-block bootstrap lower bound was negative and the validation gate failed. **NO-GO**.

The subsequent clearly post-hoc diagnostic measures ONLY weekly pip movement (not executable $1000-account profits): 278 eligible signals across 2019–25, trend average **−13.35 pips**, inverse average **+11.47 pips**, but the 8-week-block bootstrap 95% lower bound of the inverse average is **−1.32 pips**, not sufficient evidence of a positive edge. The inverse policy with actual 0.01 lot / 0.5% risk sizing was NOT robustly profitable. No actual FX carry/swap is modeled; macro-rate/carry analysis requires authentic historical interest rate and broker swap data. No live trading or brokerage keys.

## Extended 15-year EconEdge FX reversal study (2011–2025; 2010 warm-up)

- [**15-year audited Vietnamese report**](BAO_CAO_ECONEDGE_15_NAM_2011_2025.md) · [pre-registered fixed protocol](DE_CUONG_ECONEDGE_15_NAM_2011_2025.md)
- [**All 9 GitHub Actions jobs successful, including authentic 2010–2017 history acquisition**](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41152773799)
- [Backtest and 8-week bootstrap implementation](scripts/econedge_long_2011_2025.py)
- Artifact: `econedge-15year-complete-2011-2025` (99,712 genuinely matching H1 observations; 606 weekly signal rows; trade/decision CSVs and JSON). Eight annual quote artifacts retain 2010–17 files and monthly SHA-256 manifests.

The originally observed 2019–25 weekly mean-reversion effect does **not generalize reliably**: 2011–17 inverse mean **−2.11 pip/week** across 286 eligible signals, versus +11.63 over the previously reused 2018–25 period. Full 2011–25 mean +5.14 pips for 606 signals, but eight-week block bootstrap 95% lower bound is **−3.33 pips**. On the actual $1k / 0.5%-risk / 0.01 minimum lot / 5× leverage simulator, the inverse arm lost **$63.71 across the 15-year full-account run with just 34 fills**, and spread x2 worsens it to −$65.43. The trend arm showed +$33.71 on 43 fills but also failed statistical robustness. **NO-GO real trading**. Brokerage carry/swap and tick-level execution are unavailable; this is not an Exness profit simulation. Source integrity: 13 inverted Dukascopy AUDUSD H1 quotes in the 2010 warm-up were explicitly excluded and recorded, no artificial data or signals were generated.

## Latest 31 Oct 2026 — real 2026 EURUSD + GBPUSD H1 reversal forward-period check

- [**Full audited Vietnamese 2026 research report: actual downloaded quote data, not a fabricated result**](BAO_CAO_ECONEDGE_EURGBP_H1_2026.md)
- [**GitHub Actions success and 13 passing tests, all trade decision CSVs**](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41155530651)
- [Research script](scripts/econedge_2026_eurgbp.py) · [2026 tests](tests/test_econedge_2026_eurgbp.py)
- Artifact `econedge-eurgbp-2026-verified-results`, 26 authentic SHA-256 monthly source manifests, 6,754 common H1 bars, 38 complete weeks Jan–Sep 2026, 21 qualifying frozen four-week momentum events.
- Inverse trend-to-mean direction produced **+9.36 average modeled pips per qualifying week**, but eight-week-block bootstrap lower 95% **−3.80 pip**. Trading with real Standard **0.01 minimum lot: 2 fills, −$4.54**; hypothetical **0.001 standard-lot: 13 fills (8 winners), +$17.80**, stress extra spread still +$17.38, but weekly PnL bootstrap lower **negative**. Matched trend at hypothetical .001 lot lost $25.82.
- [Official Exness Standard Cent specifications](https://get.exness.help/hc/en-us/articles/17537782786588-Standard-Cent-account) confirm **1 cent lot = 0.01 standard lot**; **0.1 cent lot = 0.001 standard lot in contract exposure** (availability, increment and broker spreads/swap must still be checked before any trading). No broker real-money orders were placed.
- Final verdict: **NO-GO** for live trading given short sample, unsupported historical Exness swap/tick execution and bootstrap uncertainty. Future tests must use new data without retuning the fixed frozen rule.

## Completed 31 October 2026: exact EURUSD+GBPUSD 2026 strategy retested over 15 years

- [**Audited complete 2011–2025 Vietnamese annual PnL report**](BAO_CAO_ECONEDGE_EURGBP_CHINH_XAC_2011_2025.md) · [Preregistered same-policy rules](DE_CUONG_ECONEDGE_EURGBP_15_NAM_MINLOT_0001.md)
- [**Successful GitHub Actions run: 20 tests pass and 384 SHA256 source months audited**](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41158636720)
- [Exactly EURGBP-only backtest with real 2010–25 Dukascopy H1 and 0.001/0.01 lot simulations](scripts/econedge_eurgbp_15years_exact2026.py)
- Artifact `econedge-eurgbp-2011-2025-exact2026-strategy`: 99,785 common genuine H1 bars; 439 qualifying directional signals; 105 reversal trades at hypothetical 0.001 standard lot; year-by-year **continuous** $1000 equity ledger; matched trend and 0.01-lot controls; per-month SHA256 provenance; original trade and decision CSVs.

**Result:** hypothetical min **0.001 standard lot** reversal: 2011–17 +$12.40 (33 trades, bootstrap lower negative), 2018–25 **−$67.31** (72 trades), entire 2011–25 continuous-account **−$55.57 = −5.56% (105 trades, PF 0.812, max closed-trade DD −9.05%)**. Extra spread stress −$59.28. The special 2026 Jan–Sep 13-trade +$17.80 result does not generalize historically. Standard min .01 lot over the continuous 15 years gave only 14 reversal trades and −$53.22. **NO-GO for real-money deployment**, missing broker swap and tick execution. This retrospectively selected EURGBP subset is not independent out-of-sample validation.

## 31 October 2026 — WinnerFX v1: trading like a winner requires positive asymmetry, not a high win rate

- [**Complete Vietnamese 15-year audited report**](BAO_CAO_WINNERFX_TU_DUY_NGUOI_THANG_2011_2025.md) · [Frozen pre-run method](DE_CUONG_WINNERFX_V1_TREND_CONVEXITY.md)
- [**GitHub Actions fully successful AFTER adverse stop-slippage correction**](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41159566809)
- [Executable research implementation](scripts/winnerfx_v1.py) · [Regression tests](tests/test_winnerfx_v1.py).
- Final artifact `winnerfx-v1-2011-2025-audited`: 99,712 genuine SHA-verifiable H1 quotes jointly observed across four FX pairs; 4,153 valid UTC daily bars from 2010–25; 15-year annual realized PnL, all source evidence via original verified data, 12 trade CSVs, 12 decision ledgers.
- Strategy: **55-trading-day D1 close breakout + EMA20 >/< EMA100**, enter next D1 first authentic Bid/Ask OPEN, risk stop 0.5% equity, **3×ATR20 trailing stop never widened**, no fixed take profit; at most one FX position across four pairs, hold at most 90 trading days. Compare trend with inverse same-signal policy, and hypothetical min .001 with standard min .01 lots.
- Historical full 2011–25 $1000-account with hypothetical .001 lot: **117 trend trades, 32.5% wins, mean win +$5.50 vs mean loss −$2.45, +$14.93 total/15 years, PF1.077, −6.75% max closed DD**, spread stress +$13.39. **Earlier 2011–17 +$71.35, newer 2018–25 −$52.23**, both negative 95% lower bootstrap weekly returns; no observed 0.01-lot entries allowed under the frozen 0.5% risk/$1000. No historical swap or tick execution, and reused historical dates are not pristine OOS. **NO-GO live trading.**

## 31 October 2026 — EconEdge Macro v1: TESTING genuine currency interest and futures fund positions

- [**One combined source-verified Vietnamese report: CFTC flows, OECD interest rates, FX price-only risk premium limits**](BAO_CAO_ECONEDGE_MACRO_V1_COT_LAISUAT_RUIRO_2011_2025.md)
- [**Pre-registered economic design and strict NO-GO gates**](DE_CUONG_ECONEDGE_MACRO_COT_CARRY_V1.md)
- [Official CFTC futures-only TFF GitHub Actions success](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41160441156) · [CFTC position/price script](scripts/econedge_macro_cftc_v1.py). Official source SHA 3f4c0cc8759b062f67407c64474764b1f9c276df7ef54af3169168c4f5c22a17, 3,340 CFTC 2010–2025 actual EUR/GBP/AUD/JPY futures weekly position rows from official Socrata. Positions known only **≥13 days after Tuesday** are used on Monday. 2011–2025 continuous-account follow 4-week change of Asset-Manager net futures positions **−$166.64/261 trades**, reverse **+$56.52/261 trades**, PF1.081, bootstrap 95% lower negative. Reverse was **+$95.54 in 2011–17** but **−$32.68 in 2018–25** independent-account windows; NOT a stable tradable edge. No historical broker swap/carry was credited.
- [OECD/FRED 5-currency 3-month interest signal Github Actions success](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41160588432) · [FRED rate/spot-price script](scripts/econedge_macro_rate_proxy_v1.py). Actual 178 monthly aligned events (2011–25), 2-month signal availability lag, choose highest absolute foreign-USD 3-month rate spread, follow high rate currency; **-30.67 bps/month PRICE ONLY in 2011–17** and **+32.80 bps/month spot in 2018–25**, full 15yr +2.85 bps/month with negative block-bootstrap lower bound; **NOT broker trading or actual 3-month carry returns**. FRED original source SHA 66ea842c8833af62b1cfa6b92e6b0e90104303711f939e2441d3b2ead901c1e9.
- Official data and full trade/decision ledgers are stored in downloadable GitHub Artifacts `econedge-macro-cftc-real-data-2011-2025` and `econedge-3month-rate-spotsignal-2011-2025`. CFTC TFF reports are **futures-only positions**, not global spot FX capital flows, and rate series are **interbank proxies, NOT actual executable forward swap or broker carry**. All 2011–25 FX data was previously viewed in many experiments; no pristine OOS claim. **NO-GO real money.**
