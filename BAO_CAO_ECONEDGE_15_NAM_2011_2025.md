# ECONEDGE — 15 năm nghiên cứu hồi quy về trung bình 2011–2025 (đã kiểm toán)

**Hoàn thành ngày 31/10/2026. KẾT LUẬN: KHÔNG TÌM ĐƯỢC LỢI THẾ BỀN VỮNG, NO-GO tiền thật.**

## Bằng chứng và khả năng tái lập
- [Đề cương cố định TRƯỚC khi lấy dữ liệu lịch sử bổ sung 2010–2017](DE_CUONG_ECONEDGE_15_NAM_2011_2025.md).
- [GitHub Actions toàn bộ 8 năm dữ liệu + job 15 năm **đều hoàn thành thành công**](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41152773799).
- Artifact **`econedge-15year-complete-2011-2025`**: `ECONEDGE_15Y_RESULTS.json`, `ALL_WEEKLY_DIRECTION_SIGNALS_2011_2025.csv`, `BAO_CAO_ECONEDGE_15_NAM.md`, 28 CSV giao dịch và quyết định của 7 nhóm thời kỳ × 2 hướng (một số nhóm chồng thời gian, **không** được cộng số giao dịch giữa các nhóm).
- Có 8 artifact **`econedge-verified-quotes-2010` tới `...-2017`** bảo lưu mọi CSV nguồn của EURUSD, GBPUSD, AUDUSD, USDJPY và checksum SHA-256 cho từng tháng.
- [Mã nghiên cứu không tối ưu thông số](scripts/econedge_long_2011_2025.py) · [kiểm thử](tests/test_econedge_long_15_years.py) · [nguồn tín hiệu gốc](scripts/econedge_weekly_trend.py).

**Bộ dữ liệu:** 192 tháng (2010–2025) × 4 cặp = **768 file H1 tháng có SHA-256**; **99.712 nến H1 giao nhau thực** của bốn cặp. Năm 2010 chỉ là dữ liệu warmup, **15 năm 2011–2025** là giai đoạn đánh giá. Năm 2011–2017 là *lịch sử sớm hơn* trước đây chưa kiểm định với hệ thống này, **không phải forward holdout tương lai**; 2018–2025 đã được quan sát nhiều lần qua những nghiên cứu trước đó.

**Chất lượng nguồn (công khai):** lượt tải đầu phát hiện Ask thấp hơn Bid −0,3 pip trong một bản ghi AUDUSD cũ. Sau kiểm tra, công cụ tải lịch sử riêng chỉ loại các nến Bid/Ask bị đảo chiều, lưu `rejected_inverted_spread` trong metadata, không sửa giá, không tạo giá giả, dừng nếu lỗi >2% của tháng. Kiểm toán **384 metadata tháng thuộc 2010–2017** ghi nhận **13 nến AUDUSD bất thường, tất cả trong năm 2010** (13/199.596 bản ghi gốc thuộc tám năm); **không có nến bị loại ở 2011–2017**. Thay đổi ngưỡng kiểm tra dữ liệu từ 0,5% thành 2% đã thực hiện sau phát hiện lỗi và được khai báo; **không thay các ngưỡng tín hiệu hoặc mục tiêu giao dịch**.

## Giả thuyết gốc không thay đổi

Mỗi thứ Hai lúc 08:00 UTC, tính điểm động lượng từ **480 nến H1 đã hoàn thành** (~4 tuần giao dịch); chọn duy nhất cặp có |z| lớn nhất; chỉ có tín hiệu nếu |z|≥0,8. So sánh hai hướng trên **chính cùng tuần/cặp**:
- **Hồi quy về trung bình:** giao dịch ngược hướng di chuyển của bốn tuần trước.
- **Đi theo xu hướng (đối chứng):** giao dịch cùng hướng.

Bước thứ nhất là **chẩn đoán chuyển động giá**: tại Open thứ Hai, thoát thứ Sáu 20:00 UTC, đo pip sau spread/slippage, **không Stop Loss hoặc lot**, vì vậy **không thể quy đổi trực tiếp sang PnL của tài khoản $1.000**.

Bước thứ hai là **backtest khả thi giao dịch**: cùng điểm vào nhưng thêm SL = 6×median biên độ 72H đã đóng (ít nhất 8pip, bỏ nếu >70pip), thoát ở stop hoặc cuối tuần, vốn mô phỏng $1.000, rủi ro thiết kế 0,5% equity/lệnh, lot tối thiểu/bước 0,01, max 5× đòn bẩy, tối đa một lệnh/tuần, mô hình spread và 0,1pip slippage mỗi chiều. Spread ×2 giữ nguyên lệnh và chỉ trừ thêm phí từ spread ghi nhận, **không dịch mục tiêu**. Không có phí swap, tài trợ lãi suất, Exness tick hay trượt giá gap thực.

## A. Đo khả năng dự báo hướng giá: tính bằng pip, CHƯA phải giao dịch khả thi

| Giai đoạn | Tuần có tín hiệu | Đi ngược xu hướng pip TB/tuần | Thuận xu hướng pip TB/tuần | Tỷ lệ tuần ngược xu hướng có lãi | Cận dưới bootstrap 95% của hướng ngược |
|---|---:|---:|---:|---:|---:|
| **2011–2014** | 165 | **−10,96** | +8,69 | 47,3% | −27,80 |
| **2015–2017** | 121 | **+9,95** | −11,80 | 61,2% | −8,48 |
| **2018–2021** | 159 | **+12,86** | −14,66 | 52,8% | −3,48 |
| **2022–2025** | 161 | **+10,41** | −12,32 | 54,7% | −5,20 |
| **2011–2017, mới bổ sung** | **286** | **−2,11** | +0,02 | 53,1% | **−15,50** |
| **2018–2025, từng sử dụng** | **320** | **+11,63** | −13,48 | 53,8% | **−0,09** |
| **Toàn 2011–2025** | **606** | **+5,14** | −7,11 | 53,5% | **−3,33** |

Bootstrap là circular moving-block **8 tuần, 2.500 lần lấy mẫu**, lấy phân vị thứ 5 làm cận dưới một phía. **Cận dưới 95% âm trong cả hai nhóm chính và toàn bộ 15 năm.**

**Đáng lưu ý:** trái với phát hiện quan sát trên 2019–2025, trong 2011–2017 đảo chiều không có pip trung bình dương; giai đoạn 2011–2014 còn ngược hẳn (−10,96 pip). Do đó **không thể gọi đảo chiều sau bốn tuần là một quy luật ổn định**. Giai đoạn 2018–2025 +11,63 pip vẫn có cận dưới −0,09 (không vượt được ngưỡng dương).

### Phân tách cặp 15 năm (khám phá, không chọn cặp mới hậu nghiệm)

| Cặp | Tuần được chọn bởi hệ thống | Hồi quy về trung bình, pip TB khi được chọn |
|---|---:|---:|
| EURUSD | 129 | +19,99 |
| GBPUSD | 152 | +24,41 |
| AUDUSD | 141 | −1,66 |
| USDJPY | 184 | −15,97 |

EUR và GBP tương đối tích cực ở tập này; AUD và JPY làm yếu trung bình. **Đây là phân tích SAU khi thấy kết quả**, nên việc bỏ AUDUSD/USDJPY rồi chỉ chạy EURUSD/GBPUSD **sẽ là lựa chọn hậu nghiệm, không phải chứng minh lợi thế**. Phải có tập thời gian mới chưa dùng hoặc forward demo để kiểm tra một danh sách cặp được khóa từ trước.

## B. Giao dịch với điều kiện vốn và lot thực tế: PnL USD mô phỏng

| Giai đoạn | Hướng | Lệnh thực sự đủ điều kiện | PnL sau mô hình chi phí USD | Profit Factor | Spread ×2 PnL USD | Bootstrap lower trung bình USD/tuần |
|---|---|---:|---:|---:|---:|---:|
| 2011–2017 | **Đảo chiều** | 6 | **−21,25** | 0,055 | −21,56 | −0,113 |
| 2011–2017 | Thuận xu hướng | 6 | +7,89 | 1,570 | +7,57 | −0,061 |
| 2018–2025 | **Đảo chiều** | 30 | **−50,15** | 0,469 | −51,69 | −0,239 |
| 2018–2025 | Thuận xu hướng | 37 | +25,82 | 1,304 | +23,95 | −0,101 |
| **Toàn 2011–2025** | **Đảo chiều** | **34** | **−63,71** | **0,417** | **−65,43** | **−0,149** |
| **Toàn 2011–2025** | Thuận xu hướng | 43 | +33,71 | 1,341 | +31,51 | −0,052 |

**Quan trọng:** Ba nhóm **không được cộng lệnh và PnL với nhau**: chúng là các tài khoản giả định khác nhau, mỗi nhóm reset vốn đầu 1.000 USD và giới hạn kích thước vị thế thay đổi theo equity. Trong toàn kỳ, nhánh đảo chiều chỉ khớp **34 lệnh trên 770 tuần được xem xét**, bởi 431 tuần bị loại vì stop cần >70 pip, 141 tuần bỏ vì min 0,01 lot không thể khớp với 0,5% vốn và 164 tuần không qua ngưỡng tín hiệu. Nhánh thuận có 43 lệnh, PnL dương trên 15 năm nhưng **bootstrap cận dưới vẫn âm**, nên không thể xác nhận lợi thế thống kê hay lợi nhuận thực broker.

### Vì sao quy tắc gốc không phù hợp vốn $1.000

Phần lớn tuần có xu hướng đủ lớn lại đòi Stop Loss rộng theo biến động, vượt mức đã cho phép. Không được tự động giảm khoảng stop đến mức phi lý để tạo số lệnh, cũng không được tăng rủi ro/lợi thế vay để đạt kết quả đẹp. Mức rủi ro 0,5% vốn là thiết kế *khi đặt*, không bảo đảm khi có khoảng trống giá. Không có **swap/rollover thực Exness**, nên PnL giá spot qua nhiều đêm chỉ là mô phỏng từng thành phần chi phí.

## Phán quyết theo cổng khóa trước

- **Cổng hướng giá:** cần mẫu mới 2011–2017 và tập 2018–2025 cùng có pip trung bình dương và **bootstrap lower >0**. **KHÔNG ĐẠT.**
- **Cổng chiến lược khả thi:** thêm đủ lệnh, kết quả USD dương, spread x2 dương và bootstrap lower PnL/tuần dương. **KHÔNG ĐẠT.**
- **Kết luận NO-GO giao dịch tiền thật.** Việc nghiên cứu 15 năm không phát hiện một lợi thế có thể kiểm chứng đủ vững cho cấu hình tuần này.

**Hướng nghiên cứu tiếp có giá trị hơn việc chỉnh lại z-score:** quan sát dấu hiệu EUR/GBP nhưng chỉ dùng để **đăng ký giả thuyết mới** rồi xác nhận trên dữ liệu mới; hoặc chuyển sang dữ liệu lãi suất/forward để đánh giá carry/momentum có thu nhập chi phí thực, có đủ swap broker và sizing 0,001 lot nếu broker hỗ trợ. Không kiểm chứng trên chính các năm vừa xem rồi gọi là ngoài mẫu.

### Tài liệu phản biện

Raza, Marshall & Visaltanachoti (2014), *Is there momentum or reversal in weekly currency returns?*, Journal of International Money and Finance, 45, 38–60: nghiên cứu trên nhiều đồng tiền tìm bằng chứng momentum ngắn hạn cross-sectional, không phải quy luật đảo chiều trên từng cặp USD. https://doi.org/10.1016/j.jimonfin.2014.02.009
