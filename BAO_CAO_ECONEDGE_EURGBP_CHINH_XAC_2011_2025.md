# EconEdge EUR/USD + GBP/USD — Backtest CHÍNH XÁC cấu hình 2026 trên 15 năm 2011–2025

**Ngày kiểm định:** 31/10/2026. **Kết quả hoàn thành: NO-GO giao dịch tiền thật.**

## Tại sao phải chạy lại?

Nghiên cứu 15 năm trước là chọn mạnh nhất từ **bốn cặp** EUR/GBP/AUD/JPY và dùng **lot tối thiểu 0,01**. Kết quả tháng 01–09/2026 (+17,80 USD) lại thuộc cấu hình **chỉ EUR/USD + GBP/USD, giả định tối thiểu 0,001 standard lot**. Đó là **hai chính sách khác nhau**. Không được dùng kết quả 15 năm cũ để tuyên bố chính sách mới đã được kiểm tra dài hạn. Lần này đã chạy lại **đúng hai cặp, đúng 0,001 lot** trên toàn bộ 2011–2025.

## Hồ sơ kỹ thuật có thể tái lập

- [Đề cương chốt trước khi chạy](DE_CUONG_ECONEDGE_EURGBP_15_NAM_MINLOT_0001.md)
- [GitHub Actions — đã hoàn thành thành công, **20 bài kiểm thử đạt**](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41158636720)
- [Mã chính](scripts/econedge_eurgbp_15years_exact2026.py) · [Kiểm thử](tests/test_econedge_eurgbp_15years_exact2026.py) · [Workflow](.github/workflows/econedge_eurgbp_15years_exact2026.yml)
- Artifact **`econedge-eurgbp-2011-2025-exact2026-strategy`** gồm `SUMMARY_15Y_EURGBP_001_vs_0001.json`, `SOURCE_192_MONTHS_2_PAIRS_SHA256.csv`, `ALL_MONDAY_DECISIONS_2011_2025.csv`, `ALL_QUALIFYING_DIRECTIONAL_SIGNALS.csv`, `EACH_YEAR_CONTINUOUS_ACCOUNT.csv`, 12 CSV lệnh khớp và 12 CSV quyết định đầy đủ, báo cáo Markdown nguồn.
- **384 tệp dữ liệu thật**, gồm **192 tháng cho mỗi cặp** từ 01/2010 đến 12/2025, đã đối chiếu SHA-256 với metadata Dukascopy từng tệp; **99.785 nến H1 giao nhau**. Năm 2010 làm ấm bộ chỉ tiêu; giao dịch từ 2011–2025. Nến thiếu không nội suy.
- Ba nhóm tài khoản kiểm định độc lập: 2011–17 (khởi tạo 1.000 USD), 2018–25 (khởi tạo 1.000 USD), **toàn kỳ 2011–25** (tài khoản khởi tạo 1.000 USD, chạy **liên tục qua từng năm**). Dòng toàn kỳ KHÔNG phải phép cộng chính xác của hai dòng từng giai đoạn vì equity và lot làm tròn khi vào lệnh thay đổi theo đường vốn.

### Quy tắc tín hiệu và rủi ro không đổi

- Chỉ **thứ Hai 08:00 UTC**, dùng 480 nến H1 **đã đóng** trước lúc vào. Chọn cặp có |z| lớn nhất giữa **duy nhất EUR/USD và GBP/USD**, chỉ giao dịch khi |z|≥0,80.
- Nhánh chính **đảo chiều**, nhánh đối chứng **theo xu hướng**, cùng tuần/cặp. Không TP 2R cố định: chốt thứ Sáu 20:00 UTC hoặc chạm stop trước.
- SL = 6× median biên độ H1 của 72 nến trước, tối thiểu 8pip; nếu stop >70pip, **bỏ**. 0,5% vốn là **giới hạn rủi ro thiết kế cho lệnh**, danh nghĩa ≤5×, khớp giả định theo OPEN Bid/Ask với trượt giá 0,1 pip/chiều; 1 lệnh/tuần tối đa.
- Hai điều kiện lot: **0,01 standard lot** và **0,001 standard lot giả định** (khối lượng tương đương 0,1 cent lot nếu tài khoản Cent hỗ trợ quy tắc đó). Không tự tăng mức mạo hiểm để ép lệnh.
- Stress spread×2 giữ nguyên lệnh, số lot, stop và giá thoát, **trừ thêm ½ spread entry + ½ spread exit** trên cùng các lệnh. **Chưa tính swap/financing, slippage thực của Exness, tick nội H1**. Stop được mô phỏng từ giá giữa High/Low và ½ spread OPEN cùng giờ; không biết thứ tự tick.

## A. Backtest ĐÃ ÁP DỤNG lot và stop, lãi/lỗ USD thực của mô phỏng

| Giai đoạn (các tài khoản độc lập) | Quy mô lot tối thiểu | Hướng | Lệnh khớp | Thắng | PnL USD | Tỷ suất toàn kỳ | Profit Factor | DD sau đóng | Stress spread×2 USD | Bootstrap lower 95% USD/tuần |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **2011–17** | 0,001 giả định | **Đảo chiều** | 33 | 14 (42,4%) | **+12,40** | +1,24% | 1,144 | −5,16% | +11,11 | **−0,167** |
| 2011–17 | 0,001 giả định | Thuận | 33 | 12 (36,4%) | +3,79 | +0,38% | 1,043 | −3,54% | +2,57 | −0,184 |
| **2018–25** | 0,001 giả định | **Đảo chiều** | 72 | 25 (34,7%) | **−67,31** | −6,73% | 0,674 | −7,67% | −69,69 | **−0,346** |
| 2018–25 | 0,001 giả định | Thuận | 72 | 27 (37,5%) | −40,47 | −4,05% | 0,790 | −7,19% | −43,09 | −0,261 |
| **Toàn 2011–25** | **0,001 giả định** | **Đảo chiều** | **105** | **39 (37,1%)** | **−55,57** | **−5,56%** | **0,812** | **−9,05%** | **−59,28** | **−0,215** |
| Toàn 2011–25 | 0,001 giả định | Thuận | 105 | 39 (37,1%) | −37,15 | −3,72% | 0,869 | −7,29% | −41,03 | −0,185 |
| Toàn 2011–25 | **0,01** | Đảo chiều | 14 | 1 (7,1%) | −53,22 | −5,32% | 0,067 | −5,32% | −53,59 | −0,106 |
| Toàn 2011–25 | 0,01 | Thuận | 16 | 8 (50%) | +13,33 | +1,33% | 1,400 | −1,09% | +12,88 | −0,025 |

**Đặc biệt:** cận dưới bootstrap (khối 8 tuần, 2.500 lần) của đảo chiều **âm trên cả 2011–17, 2018–25 và toàn 15 năm**. Chính sách **không vượt cổng định trước**, dù giai đoạn 2011–17 dương.

## B. Sổ vốn 1.000 USD CHẠY LIÊN TỤC qua 15 năm, hướng đảo chiều min 0,001 lot

| Năm | Giao dịch | Thắng | Lãi/lỗ USD | Tỷ suất theo equity đầu năm |
|---|---:|---:|---:|---:|
| 2011 | 0 | 0 | 0,00 | 0,00% |
| 2012 | 1 | 1 | +4,07 | +0,41% |
| 2013 | 3 | 2 | +19,84 | +1,98% |
| 2014 | 19 | 5 | **−43,89** | **−4,29%** |
| 2015 | 1 | 0 | −4,59 | −0,47% |
| 2016 | 2 | 2 | +23,11 | +2,37% |
| 2017 | 7 | 4 | +13,85 | +1,39% |
| 2018 | 2 | 0 | −9,64 | −0,95% |
| 2019 | 13 | 4 | −20,82 | −2,08% |
| 2020 | 5 | 2 | +16,01 | +1,63% |
| 2021 | 15 | 5 | **−26,06** | **−2,61%** |
| 2022 | 2 | 2 | +22,22 | +2,29% |
| 2023 | 14 | 4 | **−26,41** | **−2,66%** |
| 2024 | 19 | 6 | **−28,83** | **−2,98%** |
| 2025 | 2 | 2 | +5,57 | +0,59% |

Kết thúc 2025 còn **944,43 USD** từ vốn mô phỏng 1.000 USD. Gồm **7 năm dương, 7 năm âm và 1 năm không có lệnh**. Kết quả chưa tính phí swap qua đêm nên có thể còn lạc quan so với tài khoản broker thực.

## C. Chẩn đoán hướng giá, KHÔNG áp dụng Stop Loss/lot

| Giai đoạn | Số tín hiệu | Pip đảo chiều bình quân | Pip thuận xu hướng bình quân | Cận dưới bootstrap 95% đảo chiều |
|---|---:|---:|---:|---:|
| 2011–17 | 211 | +16,68 | −18,67 | **−0,87 pip** |
| 2018–25 | 228 | +2,28 | −4,00 | **−10,66 pip** |
| **2011–25** | **439** | **+9,20** | −11,05 | **−1,18 pip** |

Đây là **đo khả năng dự báo giá đến hết tuần**, không có stop/lot/rủi ro, **không phải tỷ suất tài khoản**. Cả ba cận bootstrap đều âm. Tín hiệu trên giá chưa biến thành kỳ vọng giao dịch có thể tin được.

## D. Vì sao kết quả 2026 trông tốt mà 15 năm lại không tốt?

[Kiểm định riêng 2026 Jan–Sep đã hoàn thành](BAO_CAO_ECONEDGE_EURGBP_H1_2026.md): **13 lệnh, 8 thắng, +17,80 USD** ở kịch bản lot 0,001, spread x2 còn +17,38, nhưng bootstrap lower USD/tuần âm (−0,143). **13 lệnh không đủ kiểm chứng**, trong khi **105 lệnh quá khứ** cho PnL âm và PF dưới 1.

Điều này không nhất thiết phủ nhận cơ chế hồi quy ở một số thời kỳ, nhưng **không có bằng chứng nó là chiến lược bền vững**, nhất là khi EUR/GBP đã được chọn sau khi phân tích những năm lịch sử vừa sử dụng.

Ngoài ra, trong 768 tuần quan sát 2011–25, **334 tuần bị loại vì stop >70pip**, và chỉ **105 giao dịch** thực hiện được với min 0,001 lot; danh mục còn có các giai đoạn ít lệnh nên kết quả tháng/năm biến động cao. Không được coi 2011–25 là tập ngoài mẫu mới khi lựa chọn EUR/GBP là hậu nghiệm.

## Kết luận

**Quyết định: NO-GO giao dịch thật**. Chúng ta đã backtest lại chính xác cấu hình 2026 trên **15 năm lịch sử**, không chỉ nêu giả thuyết. Kết quả sau mô hình chi phí âm, cận tin cậy cũng không vượt 0; không được điều chỉnh stop, chỉ chọn năm có lãi, hoặc tiếp tục lọc điều kiện trên cùng 2011–25 để tuyên bố đã phát hiện lợi thế.

Hướng nghiên cứu tiếp nên dùng nguồn thông tin **khác** (dữ liệu lãi suất và swap thực tế; chi phí broker và tick) và **forward demo theo lịch tương lai**, thay vì tối ưu dữ liệu 2011–25 đã dùng. Nếu muốn đánh giá lợi thế khác, cần chốt giả thuyết và dùng thời kỳ test mới. Không giao dịch tiền thật.
