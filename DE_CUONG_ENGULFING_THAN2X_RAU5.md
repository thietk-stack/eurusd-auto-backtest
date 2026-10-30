# Đề cương: Engulfing thân >=2 lần thân trước, mỗi râu <=5% toàn nến

**Phép thử đăng ký trước khi xem kết quả 2019–2025.**

H1/H4: nến hiện tại phải engulfing thật (thân phủ thân nến trước và đổi màu). Sau đó lọc **abs(Close−Open) >= 2 × abs(Close_trước−Open_trước)** của cùng khung; thân nến trước bằng 0 sẽ bị loại. Độ dài **từng râu trên và dưới** không vượt quá **5% của High−Low toàn nến hiện tại**. Sai số lưu trữ giá chỉ cho phép 1e−8 đơn vị giá. Không dùng ngưỡng 5% tính gộp cả hai râu.

Giữ nguyên: H4/D1 4 điểm xoay chiều hỗ trợ/kháng cự được xác nhận, mỗi nến Engulfing H1/H4 là tín hiệu độc lập. Limit ở 50% toàn nến tín hiệu, chỉ hiệu lực đúng **nến H1 ngay sau** hoặc **nến H4 ngay sau** tương ứng; không khớp hủy. SL BUY dưới Low nến 1 pip, SELL trên High 1 pip; TP gộp 2R giới hạn trước vùng đối diện; sau phí RR >=1:1,5, rủi ro thiết kế 0,5% vốn, tối đa một lệnh khớp mỗi tuần trên 4 cặp.

Nguồn: lịch sử Dukascopy H1 Bid/Ask của EURUSD, GBPUSD, AUDUSD, USDJPY 2018–2025; lấy 2018 làm warmup và báo từng năm 2019–2025. So sánh 8 tổ hợp khung tín hiệu/vùng cứng; kiểm tra stress spread x2. Không phải Exness tick, không có swap; không gửi lệnh tiền thật. Các giai đoạn đã xem trước trong nghiên cứu, nên đây là backtest khám phá và không phải xác nhận ngoài mẫu mới. Nếu quá ít lệnh, không suy diễn hiệu quả.

[Mã thử nghiệm](scripts/htf_engulf_body2x_wick5.py) · [GitHub Actions](.github/workflows/htf_engulf_body2x_wick5.yml).
