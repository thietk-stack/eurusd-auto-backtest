# Nghiên cứu M15 — Engulfing mạnh tại vùng cứng H4/D1, chốt 2R ròng

**Bộ quy tắc khóa trước backtest năm 2024; dự kiến mở rộng 2019–2025 sau kiểm tra dữ liệu thật.**

## Cấu hình cố định
- Bốn cặp EURUSD, GBPUSD, AUDUSD, USDJPY.
- **Vùng cứng H4/D1**: ít nhất bốn pivot đảo chiều được xác nhận; hai loại `same` và `flip` giữ nguyên thuật toán đã thử.
- **Nến tín hiệu chỉ dùng M15**: thân engulfing M15 phủ toàn bộ thân M15 liền trước và đổi màu; thân hiện tại >= **2× thân trước**; râu trên và dưới, mỗi râu <= **5%** chiều dài M15 High–Low. Nếu không đủ bốn điều kiện không được đặt Limit.
- **Limit = (High + Low) / 2 của nến M15 vừa đóng**, không phải giữa thân nến; chỉ chờ khớp **đúng một nến M15 tiếp theo**. Khi nến tiếp theo đóng không chạm giá, hủy Limit và không đuổi giá.
- BUY tại hỗ trợ: SL = đáy nến M15 Engulfing −1 pip. SELL tại kháng cự: SL = đỉnh nến M15 Engulfing +1 pip.
- **Chốt TP tại mức có R:R ròng dự kiến đúng 2,0**, sau giả định trượt giá 0,1 pip mỗi chiều; khoảng TP trên giá lớn hơn 2 lần khoảng SL một chút vì tính phí. **Không giảm TP xuống trước vùng cản để thành R:R thấp hơn 2**; nếu trước TP có vùng cứng đối diện đã biết thì bỏ lệnh.
- Vốn mô phỏng mỗi năm bắt đầu 1.000 USD, rủi ro theo stop + giả định trượt giá **0,5% vốn/lệnh**, làm tròn lot xuống 0,01, đòn bẩy danh nghĩa tối đa 5×; tối đa một **lệnh được khớp** mỗi ISO-week trên toàn bộ bốn cặp.
- Nếu cùng một nến M15 chạm Limit và SL, ưu tiên tính SL; không ghi TP ngay trong nến vừa khớp vì không có thứ tự tick. Giữ tối đa 96 giờ hoặc đóng vào cuối năm, không giấu vị thế mở.
- Dữ liệu **Dukascopy M15 BID/ASK thật** tải trực tiếp bằng `timeframe=m15`, kiểm tra tháng bằng SHA-256. Giá **H1 cũ chỉ phục vụ tìm vùng H4/D1**, không tạo M15 giả từ H1. Mô hình khớp BUY tại Ask, SELL tại Bid, stop/target phía đối ứng; spread đã bao gồm trong báo giá, không trừ spread thêm lần hai. Cộng giả định slippage 0,1 pip mỗi chiều.
- Chi phí **swap/rollover Exness lịch sử**, tick chronology nội nến, tin tức và độ trễ không có. Dữ liệu giai đoạn 2019–2025 đã được xem trong các nghiên cứu trước nên không phải holdout hoàn toàn mới; không giao dịch vốn thật.

## Cách đọc kết quả
Xuất riêng **2019–2025 từng năm** và bốn kiểu vùng cứng: số M15 lọc được, số Limit đặt, số Limit khớp đúng nến M15 kế tiếp, tỷ lệ thắng, tổng lợi nhuận sau spread/giả định slippage, PF, DD sau lệnh đóng và số tuần được giao dịch. Không sửa bộ lọc nếu số giao dịch thấp. M15 thường có stop nhỏ, vì vậy ảnh hưởng spread và khoảng trống giá phải được kiểm toán.

[Mã tải M15](scripts/download_m15_four_pairs.mjs) · [Mã backtest](scripts/m15_engulf_hard_zones_2r.py) · [Workflow](.github/workflows/m15_engulf_hard_zones_2r.yml).
