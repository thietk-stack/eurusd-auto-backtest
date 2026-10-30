# QUANTMIND FX v2 — nghiên cứu M1 phá vỡ giả + quay lại vùng giá, 15 tháng mẫu

**Hoàn thành ngày 31/10/2026. KẾT LUẬN: NO-GO giao dịch tiền thật.**

Bộ dữ liệu: **Dukascopy M1 BID và ASK thực** của EURUSD, GBPUSD, AUDUSD, USDJPY; báo giá kiểm tra theo SHA-256 tháng/cặp, **không nội suy từ H1 hoặc M15**. 15 tháng mẫu rải theo quý, dùng dữ liệu quá khứ M1 đã đóng. Mô phỏng lệnh tại nến M1 tiếp theo, SL-first khi nội nến không xác định thứ tự khớp, TP ròng dự kiến 2R, lệnh rủi ro tối đa thiết kế 0,5% số dư, không quá một lệnh khớp mỗi tuần ISO trên cả bốn cặp.

- [Bản chốt quy tắc M1, không chỉnh sau thí điểm](DE_CUONG_QUANTMIND_V2_M1_RECLAIM.md)
- [Bản chốt nhóm 15 tháng và loại dữ liệu pilot đã xem](DE_CUONG_QUANTMIND_V2_15_THANG.md)
- [GitHub Actions toàn bộ 15 job + job tổng hợp đều thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41143864924)
- Artifact **`quantmind-m1-fifteen-month-consolidated`** chứa `AGGREGATED_M1_RECLAIM.json`, `BAO_CAO_15_THANG_M1.md`, `ALL_MONTHLY_RESULTS.csv` và sổ lệnh từ 15 tháng. 15 artifact riêng chứa 4 nguồn giá kiểm tra SHA-256, số ứng viên, số lệnh, chi phí và giao dịch.
- [Mã logic cố định](scripts/quantmind_m1_reclaim.py), [kiểm thử](tests/test_quantmind_m1_reclaim.py), [mã kiểm toán và gộp](scripts/aggregate_quantmind_m1.py).

## Quy tắc giá

M1 có High vượt **đỉnh 60 nến M1 liền trước ≥0,8 pip**, nhưng Close đóng lại **dưới đỉnh trước ≥0,1 pip**, hoặc tương tự cho đáy. Chỉ dùng nến đóng, không suy diễn rằng thật sự có tổ chức quét stop loss. Spread cuối tín hiệu <=1,25 lần median spread của 120 phút quan sát trước và <=2,5 pip. Giao dịch 07:00–17:00 UTC. Hai cấu hình được so sánh cùng một giả thuyết:
1. **Reversal:** giao dịch ngược hướng của false-break (bán tại false-break đỉnh, mua tại false-break đáy).
2. **Continuation đối chứng:** giao dịch theo hướng phá vỡ tại các sự kiện tương tự, nhưng lệnh được lọc bởi khoảng SL/điều kiện riêng nên tập sự kiện cuối cùng **không trùng hoàn toàn từng lệnh**; không diễn giải đây là kiểm định matched-pairs hoàn chỉnh.

Giá entry BUY lấy **Ask OPEN +0,1 pip** giả định trượt, SELL lấy **Bid OPEN −0,1 pip**; stop ngoài cực trị nến sự kiện 1 pip, target ròng dự kiến 2R, kiểm tra lệnh thoát theo **Bid/Ask phía đối ứng**. Không trừ spread trùng lần thứ hai. Max 120 M1 nến quan sát. Bất kỳ nến M1 nào vừa chạm SL vừa TP tính **SL trước**.

Phép nhạy cảm spread x2 **giữ nguyên những giao dịch gốc, SL/TP và lot**, trừ thêm một lần **spread đã quan sát ở điểm vào** khỏi PnL mỗi lệnh. Đây là stress chi phí cố định đường đi, không phải mô phỏng tick broker hoặc tái lựa chọn lệnh. Thử nghiệm thí điểm 2024-01 đã từng có lỗi định nghĩa stress TP xa hơn; phát hiện và sửa, ghi lại minh bạch *trước khi chạy 15 tháng mới*, có unit test kiểm tra chi phí không làm PnL tăng.

## Chia kỳ 15 tháng cố định

- Khám phá **2022**: tháng 1, 4, 7, 10 (4 tháng).
- Validation **2023**: tháng 1, 4, 7, 10 (4 tháng).
- Kiểm tra về sau **2024–2025**: 2024 tháng 4, 7, 10; 2025 tháng 1, 4, 7, 10 (7 tháng).
- **Tháng 1/2024**, đã chạy thí điểm và từng thấy lãi nhẹ, được **loại hoàn toàn** khỏi tập kiểm định tiếp theo để giảm thiên lệch lựa chọn sau khi nhìn kết quả.

**Đặc biệt:** mỗi tháng được mô phỏng từ **1.000 USD riêng**, không phải tài khoản chạy liên tục. Tổng PnL USD trong bảng là **phép cộng tiền lãi/lỗ của các phép thử độc lập**; không được gọi là lợi nhuận kép hay kết quả cả năm.

## Kết quả sau chi phí quan sát (không có phí swap)

| Giả thuyết | Nhóm | Tháng | Giao dịch | Thắng | Profit factor | Tổng PnL USD các tháng | Tổng PnL USD nếu thêm 1 spread | Cận dưới Wilson 95% p(win) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **Reversal** | 2022 khám phá | 4 | 20 | 6 (30,0%) | 0,862 | **−3,43** | −9,78 | 0,164 |
| **Reversal** | 2023 validation | 4 | 19 | 5 (26,3%) | 0,788 | **−4,85** | −10,89 | 0,134 |
| **Reversal** | 2024–25 về sau | 7 | 35 | 8 (22,9%) | 0,617 | **−15,16** | −23,04 | 0,134 |
| Continuation | 2022 khám phá | 4 | 20 | 7 (35,0%) | 1,088 | +1,82 | −4,96 | 0,202 |
| Continuation | 2023 validation | 4 | 19 | 4 (21,1%) | 0,509 | −10,96 | −18,23 | 0,098 |
| Continuation | 2024–25 về sau | 7 | 35 | 11 (31,4%) | 0,821 | −4,76 | −13,54 | 0,203 |

Đây là **74 giao dịch cho reversal**, và **74 giao dịch đối chứng khác**, qua 15 tháng không liên tục. Kết quả đảo chiều cộng lãi/lỗ độc lập **−23,44 USD**; đối chứng **−13,90 USD**. Cả hai đều âm theo PnL sau quote spread/trượt giá mô phỏng.

### Cổng đánh giá đã cố định trước

- Validation (2023): yêu cầu ít nhất 15 lệnh, lãi dương sau phí, PF>1,1 và stress vẫn dương. **THẤT BẠI**: −4,85 USD, PF 0,788, stress −10,89 USD.
- Kỳ 2024–2025: ít nhất 30 lệnh, lãi dương, PF>1,1, stress dương và **Wilson lower 95% cho tỷ lệ thắng >33,33%**. **THẤT BẠI**: 35 lệnh, 8 thắng, PF 0,617, Wilson 0,134, cả hai PnL âm.
- Dù cho một giai đoạn khác tích cực, **không được nâng cấp chiến lược sau khi validation đã không đạt**.

## Phát hiện phương pháp luận quan trọng: Chọn lệnh đầu tuần gây thiên lệch

Kiểm toán `reversal_ALL_15_MONTHS.csv` cho thấy:
- **67/74 lệnh reversal (90,5%) mở vào thứ Hai**, chỉ 7 lệnh vào ngày khác.
- **64/74 lệnh reversal (86,5%) vào 07:00–07:59 UTC**.
- Nguyên nhân là nghiên cứu giữ nguyên giới hạn **tối đa một giao dịch mỗi tuần** và lấy **tín hiệu hợp lệ đầu tiên**. Trong dữ liệu M1 có tới nhiều trăm ứng viên mỗi tháng, nên thuật toán tự động ưu tiên thứ Hai lúc bắt đầu phiên cho phép thay vì xem đủ điều kiện của từng phần khác trong tuần.
- Do đó đây là kiểm định chính xác của **“vào lệnh đầu tiên đáp ứng điều kiện mỗi tuần”**, **không** chứng minh mọi false-break M1 ở các phiên khác đều có cùng tỷ lệ thắng.
- Đối chứng continuation cũng có 67/74 lệnh vào thứ Hai. Các tập ứng viên khác nhau do SL của hai hướng khác nhau; không được diễn giải như so sánh ghép cặp tuyệt đối.

### Cấu trúc lãi/lỗ reversal trong 74 lệnh

| Lý do thoát | Số lệnh | Tổng PnL USD |
|---|---:|---:|
| SL thông thường | 44 | −70,93 |
| SL ngay trong phút vào | 11 | −16,24 |
| TP +2R | 18 | +61,13 |
| Hết thời gian giữ | 1 | +2,60 |

Kết quả **18 TP đạt 2R**, nhưng **55 lần chạm SL**, và một lần thoát do hết giờ, khiến tổng PnL lỗ. Số lệnh thắng 19 tính cả một lệnh hết giờ dương.

### Những điều KHÔNG thể khẳng định từ nghiên cứu

- **Không có order book trung tâm Forex** hay dòng lệnh tổ chức; v2 chỉ đo hành vi phá vỡ giả trên M1 Dukascopy. Không thể kết luận cá mập “quét thanh khoản”.
- M1 là nến Bid/Ask, **không phải tick**. Không biết thứ tự chính xác khi nến chạm cả stop và target, hay chi phí Exness thực tế.
- Không có swap/rollover, tin kinh tế theo thời điểm, market impact và latency.
- Ngưỡng rủi ro 0,5% vốn là **thiết kế**, có thể bị vượt bởi gap, slippage hoặc thiếu thanh khoản.
- Kết quả từ các tháng rời rạc không đo lường lợi nhuận cả năm; các năm này đã được dùng cho nhiều nghiên cứu khác, nên không còn “holdout hoàn toàn chưa nhìn thấy” ở cấp dự án.
- Nhiều thử nghiệm trong lịch sử nghiên cứu tăng rủi ro data snooping. Không chỉnh ngưỡng 60, spread 1,25× hay phiên dựa vào tập validation/kiểm tra vừa xem và không gọi là phát hiện mới đã được xác nhận.

## Quyết định và hướng nghiên cứu tiếp theo

**NO-GO giao dịch tiền thật.**

Bước nghiên cứu có cơ sở nhất không phải thêm chỉ báo mà **loại thiên lệch lấy lệnh đầu tuần** khỏi việc học xác suất: gắn nhãn **toàn bộ** ứng viên false-break và đo (P(TP | dữ kiện đầu vào)), sau đó dùng các **mẫu không chồng lấn về thời gian hoặc block bootstrap theo ngày/tuần**, không dùng hàng nghìn sự kiện chồng lấn làm hàng nghìn giao dịch độc lập. Nếu chọn mô hình mới, phải đăng ký trước, dùng nguồn dữ liệu mới và forward demo/tick kiểm chứng. Dù kết quả sau này tích cực vẫn cần nhiều tháng demo chưa dùng điều chỉnh và kiểm toán spread/swap thực trên broker.

**Không giao dịch tiền thật.**
