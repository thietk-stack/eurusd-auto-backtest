# EconEdge EURUSD/GBPUSD — Kiểm toán bổ sung H1 2026 đến 30/10 và lỗi dữ liệu cache tháng chưa đủ

**Ngày kiểm toán:** 31/10/2026. **Quyết định:** **NO-GO tiền thật; không có lợi thế thống kê được xác nhận.** Đây là phép nối tiếp thời gian với chính sách đã khóa, không tối ưu tham số.

## 1. Phát hiện và sửa lỗi dữ liệu có ý nghĩa thực tế

Trong lượt chạy ban đầu [41190117145](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41190117145), hệ thống từ chối báo cáo vì **không có H1 thứ Sáu 30/10/2026 lúc 20:00 UTC trên cả EURUSD và GBPUSD**. Kiểm tra mã nguồn cho thấy một lỗi kiểm toán:

- Bộ tải `scripts/download.mjs` và `scripts/download_portfolio.mjs` **đã xác minh SHA256 của tệp tháng có sẵn nhưng không xác minh thời điểm kết thúc của khoảng thời gian dữ liệu**. Cache tháng 10 có `to = 2026-10-30T00:00:00Z` được chấp nhận nhầm là đủ cho yêu cầu đến `2026-10-31T00:00:00Z`.
- Đã sửa **cả hai bộ tải** để chỉ dùng lại tháng có nguồn bao phủ trọn vẹn `[requestedFrom, requestedTo)`. Nếu cache đúng hash nhưng thời gian cũ chưa đủ, phải tải lại **dữ liệu thật**, không nội suy/giả nến.
- Bổ sung `scripts/coverage_guard.mjs`, `tests/test_download_coverage.mjs`. **16 kiểm thử** đã chạy đạt trong lần cuối, gồm kiểm tra tính đầy đủ cache.
- [GitHub Actions cuối cùng, thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41190249815). Log ghi `REFRESH_PARTIAL_CACHED_MONTH` cho **EURUSD, GBPUSD, AUDUSD, USDJPY** tháng 10 và nạp lại từ Dukascopy; mỗi cặp có **525 H1 tháng 10**. Chỉ EURUSD và GBPUSD được dùng trong chiến lược này.

**Đối chiếu dữ liệu gốc:** 26 tệp tháng/cặp 09/2025–09/2026 đã tái kiểm tra SHA256 và có cùng dấu vân tay danh mục nguồn `303b518abd5600ed91a6cb68f28b8a865cc919043c15abf4e19b7876e7496829` như [artifact Jan–Sep 2026 #13025105010](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41155530651). Không có thay đổi lịch sử gốc. Hai tệp mới:

| Cặp | Tháng | Nến H1 thật | SHA256 CSV nguồn | Bao phủ dữ liệu |
|---|---|---:|---|---|
| EURUSD | 10/2026 | 525 | `078de9a6c26534aec8ac29ad2a36af6b9a27142ae862527d024176f5cb26180b` | 01/10 đến trước 31/10 00 UTC |
| GBPUSD | 10/2026 | 525 | `e19ec976f555494da01adb7a03ddbb37442390ebf2dc7c062ba5c501490fd75c` | 01/10 đến trước 31/10 00 UTC |

Có **7.279 H1 giao nhau** toàn bộ 09/2025–10/2026, đủ để dùng 480 nến đã đóng và hoàn tất thứ Sáu 20 UTC của tuần 26/10.

## 2. Kiểm tra tái lập trước khi thêm tuần mới

Mã `scripts/econedge_2026_october_audit.py` **không sửa bất cứ quy tắc giao dịch nào**, mà gọi nguyên các hàm `freeze_events` và `run_book` của `scripts/econedge_2026_eurgbp.py`. Đã xác nhận chính xác **38 tuần Jan–Sep 2026**, bốn biến thể lệnh/PNL trước khi tính phần mới:

| Min lot | Nhánh | Jan–Sep lệnh | PnL Jan–Sep USD |
|---|---|---:|---:|
| 0,001 standard lot giả định | Đảo chiều | 13 | +17,7985 |
| 0,001 giả định | Theo xu hướng | 13 | −25,8180 |
| 0,01 standard lot | Đảo chiều | 2 | −4,5350 |
| 0,01 | Theo xu hướng | 2 | −7,6400 |

**Không sửa thông số:** thứ Hai 08 UTC, 480 nến H1 đóng, |z|≥0,8, stop 6×median biên độ 72 H1 (min 8pip, max 70pip), thoát thứ Sáu 20 UTC hoặc stop, 0,1pip slippage mỗi chiều, spread thực tại H1 OPEN, thiết kế rủi ro ≤0,5% equity, đòn bẩy danh nghĩa ≤5×, tối đa một lệnh/tuần. Lot 0,001 chỉ giả định, không được coi là broker đã hỗ trợ.

## 3. Kết quả mới: năm tuần vừa hoàn chỉnh (28/09–30/10/2026)

| Tuần bắt đầu (thứ Hai 08 UTC) | Cặp được chọn | |z| | Stop | Quyết định với lot 0,001 đảo chiều | PnL USD |
|---|---|---:|---:|---|---:|
| 28/09 | GBPUSD | 1,559 | 73,65 pip | **Bỏ**, stop >70 | — |
| 05/10 | EURUSD | 2,404 | 76,95 pip | **Bỏ**, stop >70 | — |
| 12/10 | EURUSD | 1,819 | 57,90 pip | BUY 0,008 lot; stop ngày 14/10 | **−4,64** |
| 19/10 | EURUSD | 1,406 | 79,65 pip | **Bỏ**, stop >70 | — |
| 26/10 | EURUSD | 0,853 | 63,90 pip | BUY 0,007 lot; stop ngày 27/10 | **−4,48** |

Hai giao dịch mới đều dừng lỗ; **PnL tăng thêm của tài khoản giả lập nối tiếp Jan–Oct = −9,12 USD**, sau mô hình Bid/Ask và slippage, **chưa tính swap thực tế**.

## 4. Sổ tài khoản 2026 cập nhật đến 30/10

| Min lot | Chính sách | Lệnh Jan–Oct | PnL USD tài khoản khởi đầu $1.000 | PF | Stress spread×2 USD | Bootstrap lower 95% USD/tuần |
|---|---|---:|---:|---:|---:|---:|
| 0,001 giả định | **Đảo chiều** | **15** | **+8,6785** | **1,292** | **+8,2265** | **−0,5514** |
| 0,001 giả định | Theo xu hướng | 15 | −27,8680 | 0,421 | −28,2965 | −1,2975 |
| 0,01 | Đảo chiều | 2 | −4,5350 | 0,000 | −4,6050 | −0,2980 |
| 0,01 | Theo xu hướng | 2 | −7,6400 | 0,000 | −7,7050 | −0,4459 |

**Không công bố ROI thực hoặc lợi thế:** nhánh đảo chiều lot 0,001 còn PnL giá mô phỏng dương nhưng đã giảm từ +17,80 xuống +8,68 USD, cận dưới bootstrap 95% **âm**, chỉ có 15 lệnh trong 43 tuần; cả giai đoạn 2011–2025 với chính sách tương đương **105 lệnh, −55,57 USD** (không phải holdout mới). Cần giữ NO-GO. Cũng không thể dùng 5 tuần mới làm kết luận thống kê.

## 5. Giới hạn và hành động kế tiếp

- **Độ chính xác nguồn:** SHA256 được tính trên CSV đã tạo từ dữ liệu `dukascopy-node` và gắn metadata; hash xác nhận tính nguyên vẹn trong quy trình, không phải chữ ký độc lập của sàn. Đã so sánh với manifest Jan–Sep cố định và tải lại tháng 10 khi thiếu khoảng thời gian.
- **Không có swap broker, triple swap, commission thực tế, slippage khi stop, spread của Exness hay tick-level stop.** Nến H1 dùng mid high/low ± nửa spread OPEN để ước lượng chạm stop, không phải backtest tick thực tế.
- **Không thể gọi 2026 là holdout hoàn toàn nguyên vẹn:** các dữ liệu 2026 từng được xem trong nghiên cứu khác; 5 tuần mới là phần **nối tiếp theo thời gian** sau lần chạy Jan–Sep, không phải OOS sạch cho mọi giả thuyết.
- Giữ cố định chính sách, tiếp tục quan sát tuần mới với nguồn tháng có bao phủ đúng thời gian; khi đủ mẫu forward mới và dữ liệu broker thực mới xét đề xuất **demo forward**, không vào lệnh thật, không cấp vốn.

**Hồ sơ đầy đủ:** [Run 41190249815](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41190249815) · artifact `econedge-eurgbp-2026-october-frozen-5-new-weeks` (25 tệp, 12 sổ lệnh, 8 sổ quyết định, bảng 28 SHA tháng/cặp, JSON kết quả, tín hiệu và báo cáo).
