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
