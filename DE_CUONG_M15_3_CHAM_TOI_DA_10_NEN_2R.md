# Price Action chỉ M15 — ba lần chạm cùng vùng, cách nhau tối đa 10 nến

**Đăng ký quy tắc ngày 30/10/2026, trước khi đọc kết quả.** Loại bỏ hoàn toàn vùng H4 và D1 (không còn yêu cầu 4 chạm H4/D1).

## Quy tắc tạo vùng giá và nến tín hiệu

- Xác định 3 lần giá tới **cùng một vùng** trên M15. Với BUY là ba phản ứng **hỗ trợ** (đáy M15), với SELL là ba phản ứng **kháng cự** (đỉnh M15).
- Hai lần đầu là pivot M15 được xác nhận: đáy thấp hơn hai nến trước và nến ngay sau có giá thấp nhất cao hơn đáy pivot, đồng thời giá đóng nến sau bật lên ít nhất 0,4 lần median biên độ 40 nến M15. Đỉnh dùng điều kiện đối xứng. **Không giao dịch dựa trên pivot chưa được xác nhận**.
- Lần thứ ba là chính **nến M15 Engulfing mạnh vừa đóng**, trong đó râu thấp (BUY) hoặc râu cao (SELL) quay về cùng vùng và giá đóng đảo chiều có lợi. Nến thứ ba có hiệu lực ngay sau khi đóng; không đòi các nến tương lai để xác nhận.
- **Khoảng cách giữa lần 1–2 và 2–3 đều phải ≤10 cây M15**, tối thiểu 2 nến để tránh đếm trùng một lần chạm. Như vậy ba điểm chạm chỉ trải dài tối đa 20 nến M15 (5 giờ) từ lần đầu tới lần thứ ba.
- Ba mức giá cách nhau không quá **bán kính max(2 pip, 0,35 × trung vị High−Low của 40 nến M15 trước)**, dùng dữ liệu chỉ tính đến nến tín hiệu. Đây là cách xác định một vùng giá thống nhất, không phải chỉ ba mức giá rời rạc.
- **Engulfing mạnh giữ nguyên:** nến đổi màu và thân phủ kín thân nến liền trước, thân hiện tại ≥2 lần thân nến trước, mỗi râu trên/dưới ≤5% toàn nến.

## Lệnh

- BUY LIMIT / SELL LIMIT tại **50% High–Low của nến Engulfing M15**.
- Lệnh chờ chỉ tồn tại trong **nến M15 ngay kế tiếp (15 phút)**; không chạm mức Limit thì hủy, không đuổi giá.
- SL BUY dưới đáy nến M15 Engulfing 1 pip; SL SELL trên đỉnh 1 pip.
- **TP đặt tại mục tiêu R:R ròng dự kiến 2,0** tính từ giá khớp thực theo Bid/Ask M15 và trượt giá mô phỏng 0,1 pip mỗi chiều. Đạt TP thì chốt, không giảm mục tiêu còn 1,5R. Không sử dụng bất kỳ vùng H4/D1 nào để hủy hoặc chặn mục tiêu.
- **Mỗi lệnh rủi ro thiết kế 0,5% vốn**, không quá 5x đòn bẩy, lot tối thiểu/bước 0,01; tối đa một lệnh khớp mỗi tuần trên tổng EURUSD, GBPUSD, AUDUSD, USDJPY; không bắt buộc tuần nào cũng có lệnh.
- Dữ liệu Bid/Ask M15 thật từ Dukascopy, tuyệt đối **không chia nhỏ H1 để dựng M15**. 2019–2025 báo cáo từng năm, 1.000 USD vốn mô phỏng reset mỗi năm.

## Tiêu chí kiểm tra

Số nến Engulfing mạnh, số lần có đủ ba chạm, số Limit chờ, số Limit khớp trong nến M15 kế tiếp, tổng lãi/lỗ sau spread và trượt giá, win rate, profit factor, DD sau giao dịch đóng, và số năm có lãi. Đối chiếu từng giao dịch để chắc chắn không sử dụng nến tương lai hoặc đặt thêm lệnh trong cùng tuần.

**Hạn chế:** Không có dữ liệu tick nội nến để chắc chắn trình tự SL/TP, không có swap/rollover Exness lịch sử, rủi ro thực tế có thể vượt mức 0,5% vốn nếu gap. Đây là backtest khám phá trên dữ liệu từng được nghiên cứu, chưa phải xác nhận ngoài mẫu mới; không kích hoạt giao dịch thật.

[Mã nguồn chiến lược](scripts/m15_three_touch_engulf_2r.py) · [GitHub Actions](.github/workflows/m15_three_touch_2r.yml).
