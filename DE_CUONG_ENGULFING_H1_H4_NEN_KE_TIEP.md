# Quy tắc đúng theo yêu cầu: Engulfing H1 và H4 độc lập — chỉ đúng NẾN KẾ TIẾP

Cập nhật 30/10/2026, chốt quy tắc trước khi xem kết quả mới. **Không phải** một nến Engulfing H1 chờ khớp trong 4 giờ.

## Hai phương án khác nhau

**Phương án A — H1:** Khi H1 hình thành nến engulfing hoàn tất tại vùng cứng, ngay khi **nến H1 kế tiếp** mở, đặt Buy Limit/Sell Limit tại 50% High–Low của nến H1 vừa đóng. Nếu **chính nến H1 kế tiếp** không chạm giá limit trong khoảng thời gian một giờ của nó, **hủy lệnh**, không khớp ở những nến sau.

**Phương án B — H4:** Khi H4 hình thành nến engulfing hoàn tất tại vùng cứng, ngay khi **nến H4 kế tiếp** bắt đầu, đặt Buy Limit/Sell Limit tại 50% High–Low của **nến H4** vừa đóng. Lệnh được chờ xuyên suốt **đúng một cây H4 tiếp theo** (4 giờ đồng hồ). Nếu cây H4 đó đóng mà không khớp, **hủy lệnh**. Dùng bốn nến H1 thực bên trong cây H4 kế tiếp để kiểm tra thời điểm có thể chạm limit; không lựa chọn thời điểm đẹp nhất sau khi đã biết kết quả.

Bốn nguồn vùng cứng giữ nguyên: H4_same, H4_flip, D1_same, D1_flip; yêu cầu >=4 pivot HTF xác nhận trong quá khứ. Do đó 4 × 2 = **8 nhóm thử nghiệm**, cùng dữ liệu giá thực của bốn cặp.

## Lệnh và vốn

- Chỉ vào lệnh ở vùng **hỗ trợ** theo BUY với engulfing tăng, hoặc **kháng cự** theo SELL với engulfing giảm. Limit tại (High+Low)/2 toàn cây engulfing, **không phải Low hay High**. Với BUY, SL = Low cây engulfing − **1 pip**; với SELL, SL = High + 1 pip.
- TP cơ sở 2R gộp tính từ limit; hạ về trước vùng cứng đối diện đã xác nhận nếu nằm trước TP. Lọc R:R sau spread+slippage **>=1:1,5** cả khi tạo limit và khi thực sự khớp.
- 0,5R/lệnh theo quy ước 1R=1% vốn → tối đa **0,5% equity** rủi ro thiết kế; 0,01 lot, đòn bẩy tối đa 5×; tối đa **một lệnh đã khớp mỗi tuần** trong một sổ vốn chung bốn cặp. Không ép tuần nào có lệnh.
- TP và SL chạm cùng một giờ: SL trước; nếu cùng giờ vừa chạm limit và SL thì ghi SL (bảo thủ). Không ghi TP ngay trong giờ khớp thiếu dữ liệu tick.
- Nếu thị trường mở vượt qua stop do gap, không giả tạo lệnh khớp limit và cắt ngay như chắc chắn có thể; ghi hủy không khớp hợp lệ. Stop còn có thể vượt 0,5% dự kiến do gap **sau khi đã khớp**.
- Cả hai loại limit chỉ có hiệu lực trong một **nến kế tiếp đúng cùng khung tín hiệu**; nếu thị trường đóng cửa/gap không có nến liền kề đầy đủ thì không tự ý chuyển limit sang ngày sau.

## Dữ liệu và báo cáo

Giá Bid/Ask lịch sử Dukascopy 2018–2025, có checksum; **2018 khởi tạo vùng, 2019–2025 phân tích riêng từng năm** với vốn nghiên cứu khởi đầu 1.000 USD độc lập mỗi năm (không tính nhầm lợi nhuận kép). 4 cặp EURUSD, GBPUSD, AUDUSD, USDJPY; 8 cấu hình, báo cáo số lệnh chờ, khớp, hết hạn, lợi nhuận ròng, PF, win rate, drawdown, chi phí và spread x2.

Khung H4 được ghép từ **đúng 4 nến H1 quan sát**; không coi nến H4 thiếu giá là nến hoàn tất. Dữ liệu H1 OHLC không biết thứ tự tick khi một nến chạm nhiều giá, nên kết quả chỉ là xấp xỉ bảo thủ. Không có điều kiện khớp Exness thực tế, swap/rollover, độ trễ, tin tức, khối lượng tập trung. Kết quả giai đoạn 2019–2025 không còn là holdout hoàn toàn độc lập do đã nghiên cứu các giai đoạn này trước đó. Đây là phép thử khám phá; không tự động giao dịch tiền thật và không hứa 5–8%/tháng.
