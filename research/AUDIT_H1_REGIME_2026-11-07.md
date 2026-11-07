# EconEdge — kiểm toán độc lập ngày 07/11/2026: tính hợp lệ của bộ phát hiện cụm biến động H1

**Phạm vi:** mã `research/h1_volatility_clustering.py` tại blob SHA `d11fb4010bd471205a47afc05ba655aef39cd1ea`, đối chiếu báo cáo EURUSD/GBPUSD 2026 ngày 31/10 và lịch sử Actions. Đây là **code/data audit**, không phải backtest hoặc xác nhận lợi thế.

## Tình trạng dữ liệu và Actions thực tế

- Truy vấn GitHub Actions ngày 07/11: lần chạy mới nhất là `41190249815`, tạo 31/10/2026 09:49:30 UTC, **success**. Không có run mới sau 31/10 trong 30 run gần nhất.
- Commit gần nhất `e6d679b5` (31/10 13:59:52 UTC) thêm bộ kiểm định cụm biến động H1; không có workflow chứng minh đã chạy bộ này trên dữ liệu thật.
- Kết quả EURUSD/GBPUSD H1 gần nhất vẫn đến 30/10: nhánh đảo chiều 0.001 lot giả định 15 lệnh, +8.6785 USD sau Bid/Ask/slippage giả định, bootstrap lower −0.5514 USD/tuần; **không có swap, commission hay stop tick thật**. Dữ liệu 2026 từng được nghiên cứu, không được gọi là pristine holdout.
- Không có manifest nguồn crypto BTC/ETH đã xác minh hash trong báo cáo hoặc artifacts đã xem; không được công bố phát hiện crypto.

## Phát hiện kiểm toán mới (đáng sửa trước khi dùng kết quả)

1. **Bộ đọc H1 hiện tại không chạy được với FX giao dịch thông thường:** `assert np.all(np.diff(stamps)==3600)` yêu cầu mọi giờ liên tục, trong khi EURUSD/GBPUSD có khoảng nghỉ cuối tuần. Không được tự thêm nến giả để thỏa mãn. Phải xử lý lịch phiên hợp lệ và chỉ tạo feature/label khi cửa sổ H1 hoàn chỉnh trong phiên; hoặc chạy H1 trên dữ liệu crypto 24/7 trước.
2. **Thiếu bộ kiểm thử tự động cho bộ phân tích mới:** mã mới chỉ được commit, chưa có CI xác nhận tính nhân quả/embargo/đầu vào. Trước khi chạy phải có test cố tình sửa tương lai và xác minh feature quá khứ không đổi; kiểm thử thiếu nến, duplicate, timezone, hash sai, và boundary embargo.
3. **Đầu vào CSV không chứng minh provenance:** `--expected-sha256` chỉ đối chiếu một hash do người chạy truyền vào; nếu hash được tính từ chính file chưa xác minh thì kiểm tra không chứng minh nguồn độc lập. Với crypto, cần URL nguồn chính thức, checksum gốc nếu có, hash bytes gốc ZIP, hash CSV chuyển đổi, script phiên bản, thời điểm tải, first/last timestamp.
4. **Chưa có suy luận thống kê:** mã chỉ xuất mean future realized volatility theo quintile và tỷ số Q5/Q1, chưa có khoảng tin cậy block bootstrap hoặc Holm correction như giao thức đã đăng ký. Một tỷ số >1 không phải bằng chứng thống kê; và dự báo volatility không đồng nghĩa edge sau phí.
5. **Sai phạm tiềm tàng về lựa chọn mẫu:** `assert train.sum()>1000` đếm nến theo giờ có nhãn chồng lấn, trong khi đánh giá chỉ lấy nến 00:00 UTC mỗi 24h. Điều kiện số mẫu phải áp dụng cho **observations độc lập thực sự** sau khi chọn mốc 24h.
6. **Tập test chưa được chứng minh chưa từng nhìn:** trong nghiên cứu FX trước, nhiều giai đoạn 2025–2026 đã được sử dụng; do đó không thể mặc định 2025–09/2026 là holdout sạch cho các giả thuyết mới mà không có log freeze/trial registry.

## Quyết định và công việc kế tiếp

- **NO-GO:** không dùng kết quả H1 regime để giao dịch cho đến khi có dữ liệu có nguồn và kiểm thử CI; không đặt lệnh hay cấp vốn.
- Ưu tiên: sửa bộ kiểm định để nhận FX H1 có weekend gaps mà không điền giả; tách quy trình crypto 24/7; thêm test; chạy H1 BTC/ETH với checksum nguồn, xuất CI bootstrap theo block ngày/tuần và correction; công bố cả kết quả âm.
- Với EURUSD/GBPUSD, chỉ tiếp tục chiến lược đã khóa và bổ sung các tuần 02–06/11 khi nguồn Dukascopy đủ H1 và hash. Không thay ngưỡng để săn lợi nhuận. Rủi ro thiết kế <=0.5%; chi phí broker chưa xác minh nên chưa đủ điều kiện execution validation.

## Liên kết kiểm toán

- [GitHub Actions run gần nhất](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41190249815)
- [Báo cáo H1 EURUSD/GBPUSD 30/10](https://github.com/thietk-stack/eurusd-auto-backtest/blob/main/BAO_CAO_ECONEDGE_EURGBP_H1_2026_CAP_NHAT_30_10.md)
- [Mã phát hiện cụm biến động](https://github.com/thietk-stack/eurusd-auto-backtest/blob/main/research/h1_volatility_clustering.py)
