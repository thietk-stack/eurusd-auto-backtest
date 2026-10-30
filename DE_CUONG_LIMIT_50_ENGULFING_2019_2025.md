# Kiểm định 2019–2025 — vùng cứng H4/D1 + Limit tại 50% nến Engulfing H1

Ngày thiết lập: 30/10/2026. Quy tắc khóa trước khi xem báo cáo GitHub Actions.

## Đầu vào và giai đoạn
- Sử dụng giá EURUSD, GBPUSD, AUDUSD, USDJPY H1 BID/ASK từ Dukascopy có chứng từ checksum; **không phải giá khớp lệnh Exness**.
- Tải **2018-01-01 tới hết 2025-12-31**, dùng toàn bộ năm 2018 làm khoảng khởi tạo vùng. Chỉ thống kê các năm **2019, 2020, 2021, 2022, 2023, 2024, 2025**, mỗi năm riêng biệt với **vốn khởi đầu 1.000 USD**, không cộng phần trăm giữa các năm thành lãi kép. Đóng mọi vị thế tại cuối năm để không giấu floating loss.
- Bốn nhóm vùng giữ đúng định nghĩa đã dùng ở vòng trước: **H4 cùng vai trò**, **H4 đổi vai**, **D1 cùng vai**, **D1 đổi vai**; mỗi vùng >=4 pivot HTF đã xác nhận. Pivot có 2 cây HTF sau khi xác nhận, vùng được kích hoạt khi nến thứ 2 đóng. Không dùng chỉ báo RSI/EMA/ATR.
- Engulfing H1 thân nến phủ thân trước, phải chạm vùng và đóng quay về phía có lợi. Chỉ xét 07:00–19:00 UTC từ thứ Hai đến thứ Sáu.

## Lệnh chờ, điểm vào
- Midpoint ở đây được hiểu **50% toàn bộ chiều dài nến**: `Limit = (High + Low) / 2` của **nến H1 engulfing vừa đóng**, không phải 50% thân nến.
- BUY LIMIT phải dưới giá đóng nến engulfing; SELL LIMIT phải trên giá đóng nến engulfing. Vào lệnh chỉ khi **giá quay lại và chạm limit**, không coi nến tín hiệu là đã khớp.
- Lệnh chờ bắt đầu từ nến H1 sau khi engulfing đóng, **hủy nếu quá 12 nến H1 có dữ liệu chung không khớp**. Limit có thể được khớp ở giá mở nến tốt hơn nếu thị trường mở vượt qua mức limit. Không bù lệnh khi không có tín hiệu và không ép lệnh mỗi tuần.
- Tối đa **1 lệnh khớp mỗi tuần ISO** trên **tổng cộng 4 cặp** và chỉ 1 vị thế mở. Khi hai tín hiệu đồng thời, chọn vùng có nhiều pivot chạm nhất, sau đó vùng hẹp hơn, RR cao hơn, và tên cặp để phân định.

## SL, TP và ngân sách vốn
- **BUY:** `SL = Low nến engulfing - 1 pip`.
- **SELL:** `SL = High nến engulfing + 1 pip`.
- TP cơ sở đặt tại **2R (gộp)** tính từ giá Limit chờ; nếu có vùng cứng đối diện được xác nhận nằm phía trước, TP sẽ được đưa về trước vùng cản đó với đệm 1 pip.
- Lọc hai lần: lúc đặt limit và khi lệnh thực sự khớp, **RR dự kiến sau spread + slippage phải >=1:1,5**. Kích thước lệnh cũng tính lại khi khớp nhằm bảo vệ **0,5R = 0,5% vốn/lệnh** (1R = 1% vốn theo quy ước); lot tối thiểu 0,01, đòn bẩy danh nghĩa không quá 5x. Giữ lệnh tối đa 96 nến H1.
- Nếu một nến vừa có thể khớp LIMIT vừa chạm SL, tính thua theo SL trước (bảo thủ, không giả sử chắc chắn biết thứ tự tick). **Không ghi nhận TP cùng nến vừa khớp** vì thiếu thứ tự giá.
- Giá chênh lệch BID/ASK ước lượng từ nến H1 tại thời điểm vào/thoát; chi phí trượt giá giả định 0,1 pip mỗi chiều; kiểm định spread x2.

## Tiêu chí báo cáo

- Với từng cấu hình và từng năm: số lệnh limit đặt, số limit khớp, số hết hạn không khớp; tỷ lệ thắng, số dư, lãi/lỗ ròng, profit factor, drawdown sau lệnh đóng, lợi nhuận khi spread x2 và từng cặp có lệnh.
- Đánh giá **2019–2022** như nhóm lịch sử sớm và **2023–2025** như nhóm gần đây, nhưng không tuyên bố đây là holdout hoàn toàn chưa từng quan sát (vì giai đoạn này đã được nghiên cứu trước trong các thí nghiệm khác).
- Thông báo trung thực nếu chiến lược không đủ lệnh, thiếu dữ liệu, không đạt lãi ròng sau phí hoặc phụ thuộc vào điều kiện giá khớp.

**Hạn chế:** H1 OHLC không đủ tái hiện thứ tự bid/ask tick và khớp lệnh LIMIT chính xác; không có Exness swap/rollover, chi phí thực tế từng tài khoản, độ trễ thực thi, lịch tin tức; SL không thể bảo đảm lỗ tối đa đúng 0,5% khi gap hoặc trượt giá xấu. Không có lệnh tiền thật.
