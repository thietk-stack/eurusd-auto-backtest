# Đề cương tín hiệu A+ trên 4 cặp Forex — cố định tiêu chí

**Thiết lập rủi ro theo yêu cầu ngày 30/10/2026**: R:R tối thiểu **1:1,5**, sau chi phí dự kiến. **0,5R/lệnh** được tạm hiểu là **0,5% vốn chủ sở hữu**, với quy ước 1R = 1% vốn. Không vượt quy mô nếu làm tròn lot 0,01. Lệnh gap, spread biến động hoặc trượt giá có thể khiến mức thua thực tế vượt 0,5%.

## Điểm A+ (chỉ tín hiệu xác nhận từ nến H1 đã đóng)

Đánh giá cả Buy và Sell theo hướng ngược nhau. Các nhóm bắt buộc:
- **2 điểm:** xu hướng đồng hướng EMA24/96 và EMA120/480 trên các chân trời H1.
- **1 điểm:** một mô hình nến pin bar có bóng dài hoặc engulfing đã đóng.
- **1 điểm:** RSI14 trong vùng thuận động lượng và thay đổi cùng chiều so với 3 nến trước.
- **1 điểm:** vượt cấu trúc đỉnh/đáy 12 nến hoặc chạm và lấy lại EMA24.
- **1 điểm:** biến động ATR14 tương đối ổn định so với median 240 nến (0,7–1,9 lần).
- **1 điểm:** spread Bid/Ask quan sát nằm trong giới hạn.
- **1 điểm:** tín hiệu tại phiên 07:00–17:00 UTC ngày thường.
- **Thêm 1 điểm:** phân kỳ RSI xác nhận bằng pivot giá 3 nến trước + 3 nến sau, không dùng pivot chưa hoàn tất.

Tối thiểu 7 điểm, nhưng do các nhóm nền tảng bắt buộc cộng thành 8, điểm thực tế đạt thường là 8 hoặc 9. Phân kỳ RSI là yếu tố tăng độ ưu tiên chứ **không bắt buộc**. Mã nghiên cứu hiện chưa có **khối lượng giao dịch tập trung** hay lịch tin tức lịch sử; không giả tạo hai yếu tố này.

## Quy tắc chọn lệnh

- Bốn cặp EURUSD, GBPUSD, AUDUSD, USDJPY, chung một tài khoản 1.000 USD mô phỏng.
- Tối đa **1 tín hiệu A+ mỗi tuần ISO trên toàn bộ 4 cặp**, và không mở lệnh mới khi còn vị thế.
- Chọn cơ hội *đầu tiên theo thời gian* thỏa điều kiện; khi nhiều cặp cùng giờ thì điểm cao hơn, RR cao hơn, rồi tên cặp. Tuyệt đối **không lựa chọn lệnh tốt nhất vào cuối tuần** (nhìn trước tương lai).
- Vào tại giá mở nến kế tiếp; stop = 1,6 ATR14 hoặc tối thiểu 5 pip; target 2,8 ATR14 hoặc tối thiểu 1,75 lần khoảng SL. **Chỉ chấp nhận nếu RR net dự kiến >=1,5** sau spread đầu vào quan sát và chi phí dự kiến.
- Kích thước lệnh tính theo risk budget 0,5% vốn; hạn chế đòn bẩy hiệu dụng 5 lần; làm tròn xuống 0,01 lot; lệnh dưới 0,01 lot bị loại.
- Đóng tại SL, TP hoặc tối đa 72 nến H1, trường hợp chạm cả SL và TP trong một nến thì coi SL xảy ra trước (thận trọng). Không giao dịch thật.

## Kiểm định

- Giá thực H1 Bid/Ask Dukascopy, có kiểm tra checksum; **không phải dữ liệu Exness**.
- Xác nhận 2021–2022, holdout 2023–2026; không sửa ngưỡng kỹ thuật theo lợi nhuận holdout.
- Kiểm tra lãi/lỗ, profit factor, drawdown vốn sau lệnh đóng, số tuần thực có tín hiệu, số tháng đạt +5% và +8%, kịch bản spread x2.
- Chỉ xem là tín hiệu đáng nghiên cứu tiếp khi cả hai giai đoạn có ít nhất 40 lệnh, lãi sau phí dương, PF > 1,10, DD không quá -15% và holdout có lãi cả khi spread nhân 2.
- Chưa có swap, lãi qua đêm, spread tick tại thời điểm SL/TP, lịch tin tức kinh tế, khối lượng thật; **chưa đủ để cấp vốn thật hoặc kỳ vọng đều 5–8%/tháng**.

Mã: [scripts/aplus_signals.py](scripts/aplus_signals.py), workflow: [A-plus confluence FX 4-pair risk-controlled research](.github/workflows/aplus.yml).
