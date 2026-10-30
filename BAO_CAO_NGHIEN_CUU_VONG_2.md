# EUR/USD — vòng nghiên cứu 2: kiểm định ba nhóm chiến lược

**Trạng thái: KHÔNG TÌM THẤY CHIẾN LƯỢC ĐỦ ĐIỀU KIỆN.**

[Lượt kiểm định GitHub Actions thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41085764980) · [Tải artifact đầy đủ](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41085764980) (eurusd-research-round-2).

### Dữ liệu và quy trình
- 104.967 nến EUR/USD H1 nguồn Dukascopy Bid/Ask; **không phải tick Exness**.
- Giai đoạn phát triển 2015–2018; lựa chọn theo xác nhận 2019–2022; đánh giá cuối 2023–30/10/2026.
- Vốn mô phỏng riêng từng giai đoạn: 1.000 USD. Rủi ro thiết kế 0,5%/lệnh, đòn bẩy hiệu dụng tối đa 5 lần, không lệnh thật.
- Chi phí giả định: 0,8 pip spread cố định + 0,1 pip trượt giá mỗi chiều; commission = 0, swap giả định = 0. Chưa thể kiểm toán điều kiện khớp lệnh Exness.
- 3 hướng mới đã xác định trước: trend_filter, mean_reversion, session_breakout; thêm Donchian18 baseline.
- Quy tắc chọn **chỉ dựa trên 2019–2022**: ít nhất 40 giao dịch, lãi sau phí dương, profit factor >1,05, drawdown >=−20%; xếp hạng theo lợi nhuận validation. **Không phương án nào đủ điều kiện.**

### Kết quả thực nghiệm

| Chiến lược | 2015–18 (phát triển) | 2019–22 (xác nhận) | Lệnh 2019–22 | PF 2019–22 | 2023–26 (kiểm định cuối) | Lệnh 2023–26 | PF 2023–26 | DD 2023–26 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Donchian 18 | +13,39% | −13,64% | 1.028 | 0,936 | −24,91% | 1.026 | 0,874 | −27,77% |
| Xu hướng + bộ lọc EMA/ADX | +2,36% | −2,86% | 419 | 0,972 | −11,64% | 393 | 0,868 | −14,03% |
| Hồi quy trung bình RSI/Bollinger | −9,12% | −16,19% | 322 | 0,718 | −12,74% | 311 | 0,770 | −19,79% |
| Phá vỡ phiên (07–08 UTC) | −19,84% | −11,83% | 387 | 0,862 | +5,48% | 343 | 1,070 | −7,13% |

Các tỷ lệ là **cho cả giai đoạn**, không phải theo tháng. Chiến lược phiên có lãi ở giai đoạn cuối nhưng đã **không đủ điều kiện** trên dữ liệu xác nhận; nếu chọn nó sau khi nhìn giai đoạn cuối sẽ gây thiên lệch lựa chọn. Không chiến lược nào đạt 8% trong một tháng trên giai đoạn cuối theo phép tính lãi/lỗ thực hiện; một tháng đơn lẻ có lãi lớn (nếu có) cũng không xác nhận lợi thế bền vững.

### Diễn giải thận trọng
- Đây là backtest trên nến giờ, nên đường đi trong nến chỉ được xấp xỉ. Khi cùng chạm TP và SL, mô phỏng giả định SL khớp trước.
- Drawdown được tính theo vốn sau giao dịch đã đóng, **chưa bao gồm biến động lãi/lỗ thả nổi và swap**.
- Chưa chạy Kronos AI; không thể kết luận rằng Kronos không có lợi thế.
- Không thể tuyên bố tìm thấy hệ thống kiếm 5–8% mỗi tháng. Không có cơ sở đưa tiền thật vào giao dịch.

### Khuyến nghị nghiên cứu tiếp (không hợp thức hóa kết quả đã xem)
1. Kiểm tra chất lượng Bid/Ask, spread động và lịch tin kinh tế; đánh giá chênh lệch giữa tick Exness và Dukascopy trước khi thử hệ thống tự động.
2. Chỉ bổ sung giả thuyết có lập luận định lượng trước khi nhìn kết quả; việc chỉnh tham số theo 2023–26 không còn là kiểm định ngoài mẫu.
3. Nếu thử thêm Kronos, phải đối chứng trên dữ liệu sau thời điểm chốt chiến lược hoặc dữ liệu mới hoàn toàn, nêu chi phí tính toán và điều kiện dừng.
4. Chạy demo forward trước bất kỳ giao dịch tiền thật nào.

Chi tiết giao dịch CSV và `RESULTS_RESEARCH.json` nằm trong artifact cùng lượt chạy GitHub.
