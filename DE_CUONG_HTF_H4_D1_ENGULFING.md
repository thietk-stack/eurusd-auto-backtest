# Nghiên cứu H4/D1 vùng cứng + xác nhận H1 Engulfing — khóa phương pháp

Chốt trước kết quả ngày 30/10/2026. Đây là thử nghiệm nghiên cứu, **không gửi lệnh tới sàn**.

## Định nghĩa vùng và xác nhận

- So sánh 4 cấu hình cố định: H4_same, H4_flip, D1_same, D1_flip. `same` yêu cầu >=4 pivot đảo chiều tại vùng cùng vai trò hỗ trợ HOẶC kháng cự. `flip` yêu cầu >=4 pivot phản ứng tại vùng với cả hai vai trò hỗ trợ lẫn kháng cự.
- Pivot HTF có 2 nến trái và 2 nến phải; chỉ coi vùng đã hình thành khi 2 nến phải **đã đóng** (không dùng đỉnh/đáy vẽ lại trong tương lai).
- Xác nhận phản ứng sau pivot >=0,65 lần trung vị chiều dài nến HTF gần nhất (40 nến), dựa vào giá, không dùng RSI/EMA/ATR.
- Lần chạm độc lập cách nhau >=6 nến H4 hoặc >=3 nến D1. Chỉ xét 240 nến H4 hoặc 220 nến D1 trước đó.
- Bán kính vùng: lớn hơn giữa **6 pip (H4) / 10 pip (D1)** và **0,32 lần trung vị chiều dài nến HTF 40 nến**.
- Tuổi tối đa để dùng vùng sau xác nhận: 24 ngày lịch đối với H4, 55 ngày lịch đối với D1. Tất cả thời điểm UTC.
- Nến H1 xác nhận: `bullish engulfing` cho hỗ trợ hoặc `bearish engulfing` cho kháng cự, thân nến sau phủ kín thân nến trước; nến hoàn tất phải chạm vùng và đóng vượt lên/trở xuống đường giữa vùng.
- Lệnh mở **tại giá OPEN của nến H1 kế tiếp**, trong 07:00–19:00 UTC ngày thường.

## Stop Loss và Take Profit cố định

**Buy** tại hỗ trợ: SL = thấp hơn trong **mép dưới vùng H4/D1** hoặc **đáy nến H1 engulfing** rồi trừ 1,5 pip đệm.

**Sell** tại kháng cự: SL = cao hơn trong **mép trên vùng H4/D1** hoặc **đỉnh nến H1 engulfing** rồi cộng 1,5 pip đệm.

- Khoảng SL từ giá vào phải ít nhất 5 và không quá 150 pip. Nếu không hợp lý, không đặt lệnh.
- TP bắt đầu tại 2 lần khoảng cách SL (2R *gộp*), **giảm về sát trước mép của vùng cứng đối diện gần nhất đã được xác nhận** nếu vùng đó chắn trước TP.
- R:R **dự kiến sau chi phí** = (khoảng TP − spread + slippage) / (khoảng SL + spread + slippage), áp dụng đúng công thức trong mã: `(rewardp - costp) / (riskp + costp)`. Chỉ vào lệnh khi >=1,5.
- Rủi ro thiết kế **0,5R = 0,5% số dư vốn**. Lot làm tròn xuống 0,01; giới hạn đòn bẩy 5x; 1 vị thế toàn danh mục, tối đa 1 entry/tuần ISO, không bắt buộc có lệnh.
- Giữ lệnh tối đa 96 giờ; cả SL và TP chạm trong một H1 thì **SL trước**; khi kết thúc giai đoạn backtest mà còn vị thế, phải đóng tại giá quan sát cuối cùng.

## Dữ liệu và thời kỳ

Dữ liệu lịch sử **thực** Dukascopy Bid/Ask H1, đủ tháng và SHA-256; không phải báo giá lịch sử khớp lệnh Exness. Các thanh H4, D1 được tính chỉ bằng nến H1 đã quan sát, có kiểm tra tối thiểu 3/4 nến H1 cho H4 và 16 nến H1 trong ngày cho D1.

Validation 2021–2022; holdout 2023–29/10/2026, mỗi giai đoạn vốn giả định ban đầu $1.000. Chỉ chọn biến thể nếu validation có >=25 lệnh, lãi dương, profit factor >=1,10 và drawdown sau đóng lệnh >=−15%. Chỉ coi là tín hiệu đáng nghiên cứu thêm nếu tiếp tục dương trên holdout với PF >=1,10, DD >=−15% và spread x2 vẫn dương.

Khối lượng thực/market order flow, thanh khoản ẩn, swap/rollover, spread tại giá SL/TP nội nến, tin kinh tế lịch sử và bảo đảm lỗ giới hạn 0,5% đều **không có**. Chênh lệch Bid/Ask mô hình lấy spread tại nến vào/nến thoát (có nội suy khoảng giá thoát trong nến), cộng 0,1 pip trượt mỗi chiều. Đây chỉ là mô hình gần đúng H1, không phải kết quả broker tick.

**Không tối ưu các ngưỡng dựa vào kết quả cuối.** Mức 5–8%/tháng chỉ là mục tiêu so sánh, tuyệt đối không coi là đã đạt nếu không được kiểm chứng.
