# EconEdge: preregistered market-regime discovery protocol (2026-10-31)

Status: RESEARCH DESIGN ONLY. No crypto dataset ingested; no crypto backtest result or claimed edge.

## Universe and integrity
- Separate BTCUSDT and ETHUSDT spot 1h from EURUSD/GBPUSD H1; never pool results.
- Source: Binance public monthly kline ZIP and matching .CHECKSUM; verify SHA256 of original ZIP, preserve URL, retrieval UTC time, checksum, row count, first/last timestamp and raw manifest.
- 2025+ Binance spot kline timestamps use microseconds, not milliseconds. Verify interval continuity, duplicate timestamps, OHLC consistency and missing candles. Reject incomplete periods.
- Do not silently substitute synthetic or resampled price data. Funding/OI require separately timestamped futures series, and must not be inferred from spot OHLCV.

## Frozen first-stage hypotheses
H1: Volatility clustering. Rank lagged 24-hour realized volatility into quintiles (thresholds trained on train only); test next 24-hour absolute return and realized volatility by quintile. Predictive volatility is NOT automatically a trading edge.
H2: Short-horizon momentum versus reversal. Define past 12-hour close-to-close return standardized by trailing 30-day volatility; compare subsequent non-overlapping 12-hour returns for top/bottom quintiles, both sign continuation and reversal. No signal parameter tuning on test.
H3: Intraday seasonality. Compute absolute hourly returns by UTC hour and compare to shuffled day-block null. Do not infer profitability from hour-of-day alone.

## Split and statistics
- Training/discovery: 2021-01-01 to 2023-12-31 UTC; validation: 2024-01-01 to 2024-12-31; untouched test: 2025-01-01 to 2026-09-30. Reserve Oct 2026 onward for future forward tracking. Adjust only if verified source availability requires it, and publish revised split BEFORE evaluating.
- Strict causal features using only completed candles, next-bar execution, embargo >= 24 hours at split boundaries; no overlapping observations for nominal significance.
- Report base rate, conditional rate, sample count, effect size, block-bootstrap 95% confidence interval, and multiple-testing correction (Holm) across hypotheses, symbols and horizons. Report negative results.
- For tradeable candidates, account for observed fees, conservative bid/ask spread, slippage, funding and liquidation risks where applicable; absent execution-cost evidence means 'not execution-validated'. Never equate close-to-close return to executable PnL.
- Risk design <= 0.5% per hypothetical trade; no orders, no capital allocation, no optimization on test.

## Promotion criteria
Out-of-sample lower confidence bound of net expectancy > 0; sufficient independent trades across market regimes, stable effect in both chronological subperiods, reasonable drawdown, sensitivity to realistic worse execution costs, no single episode dominating results. If any fail: NO EDGE CONFIRMED; no forward-demo promotion.

## Next execution
Implement checksum-verified downloader, manifest and integrity tests, then run H1 (volatility clustering) before directional hypotheses. Log data provenance and publish complete null results.
