# QuantMind v2 — tập kiểm tra mở rộng M1, cố định trước khi đọc kết quả

**Ngày chốt:** 31/10/2026. Chỉ nghiên cứu, không giao dịch tiền thật.

Giữ nguyên **tất cả** thông số của [đề cương M1](DE_CUONG_QUANTMIND_V2_M1_RECLAIM.md): phá vỡ giả đỉnh/đáy 60 nến M1 tối thiểu 0,8pip, đóng quay vào vùng tối thiểu 0,1pip, spread <=1,25x median 120 nến trước và <=2,5pip, thời gian 07:00–17:00 UTC, vào ở M1 kế tiếp theo giá Bid/Ask; SL qua cực trị tín hiệu 1pip, TP 2R ròng dự kiến, rủi ro thiết kế 0,5% vốn, tối đa một vị thế/tuần của bốn cặp. Đối chứng continuation có đầy đủ kết quả riêng.

**Sửa lỗi kiểm toán, không điều chỉnh chỉ báo:** phép stress spread x2 phải **giữ nguyên toàn bộ lệnh gốc, lot, SL và TP**, trừ thêm một khoản tương đương **spread ghi nhận tại điểm vào** khỏi PnL của từng lệnh. Không dời TP xa hơn rồi nhận lợi nhuận tăng khi chi phí tăng. Kiểm toán này đã phát hiện sau lượt thí điểm tháng 01/2024, trước tập thử mở rộng và được lưu kèm bài kiểm thử tự động. Lượt thí điểm tháng 01/2024 **được loại khỏi tập đánh giá sau**.

## Tập nghiên cứu 15 tháng được định trước, không chọn tháng theo kết quả

- **Khám phá lịch sử:** tháng 01, 04, 07, 10 năm **2022**.
- **Validation:** tháng 01, 04, 07, 10 năm **2023**.
- **Kiểm tra về sau:** tháng **04, 07, 10 năm 2024** và tháng **01, 04, 07, 10 năm 2025**.
- Tháng 01/2024 đã được xem trong thí điểm và **không dùng** để tuyên bố kiểm tra ngoài mẫu cho chiến lược mới.

Đây là **mẫu tháng rải đều trong năm**, KHÔNG phải toàn bộ dữ liệu của năm, nên **không được gán lãi/lỗ 4 tháng thành lợi nhuận cả năm hoặc lãi kép cả năm**. Mỗi tháng mô phỏng tài khoản khởi đầu 1.000 USD độc lập; tổng PnL USD của các tháng là phép cộng khảo sát, không phải tỷ suất lãi kép của một tài khoản chạy liên tục.

## Cổng đánh giá
- Cả hai hướng đảo chiều và đi tiếp được công bố riêng, không chọn hướng chỉ vì test có lãi.
- Kỳ validation 2023 phải có ít nhất **15 lệnh**, PF>1,1 và PnL >0 cùng stress spread x2 >0; nếu không, quyết định không đủ điều kiện GO.
- Kỳ kiểm tra về sau 2024–25 phải có ít nhất **30 lệnh**, PnL >0 và stress >0, PF>1,1, cận dưới Wilson một phía 95% p(win) >1/3. Cổng này chỉ cho phép **nghiên cứu tiếp trên tick/forward demo**, không sử dụng tiền thật.
- Trước khi công bố, kiểm tra **SHA256** tất cả tháng Bid/Ask; không điền lấp nến thiếu bằng nội suy. H1/M15 cũ tuyệt đối không dùng để dựng M1.
- Không có sổ lệnh tập trung/volume thị trường FX, tick nội nến, swap Exness, độ trễ và lịch tin; mọi kết luận chỉ là về proxy phá vỡ giả từ báo giá Dukascopy.
- Lịch sử 2022–25 đã từng được nghiên cứu trong chiến lược khác, nên validation/holdout ở đây chỉ **tách theo thời gian trong thử nghiệm v2**, không phải holdout nguyên vẹn của toàn dự án.
