# EUR/USD auto backtest — Historical data pipeline

**Status:** Source code deployed; real-data backtest only becomes valid after a successful GitHub Actions run. No real trading and no Kronos model inference.

This repository automatically retrieves historical EUR/USD H1 Bid/Ask candles from Dukascopy with the `dukascopy-node` library. The strategy is fixed Donchian 18 with ATR14 stop 1.9×, take-profit 2.8×, maximum 48 hours holding, position risk 0.5% of equity, maximum effective leverage 5× and lot step 0.01. An indicative Exness Standard **cost scenario** uses 0.8 pip fixed spread, 0.1 pip slippage per side and zero commission; swap is assumed zero, not verified. Stress runs repeat the full OOS period with spreads of 1.2 and 2.0 pips.

## Automated runs

Click [Actions](https://github.com/thietk-stack/eurusd-auto-backtest/actions/workflows/backtest.yml) → **EURUSD historical download and 2000 trade backtest** → **Run workflow** if you want an additional manual attempt. The workflow also runs on first push and on a daily schedule. It downloads a bounded number of months per run and caches previously verified months, to avoid starting over after timeouts. If data are missing or downloaded trade count is less than 2,000, it exits non-successfully and marks the output INCOMPLETE.

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
