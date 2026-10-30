# Đề cương cố định trước backtest: Price action vùng cứng 4 lần chạm

Ngày chốt: 30/10/2026. Đây là thử nghiệm nghiên cứu, không gửi lệnh đến Exness.

**Hai định nghĩa thử độc lập** (không nhìn kết quả 2023–2026 để đổi):
1. **4 lần cùng vai trò**: tối thiểu 4 pivot low riêng biệt phản ứng tăng tạo hỗ trợ, hoặc 4 pivot high riêng biệt phản ứng giảm tạo kháng cự.
2. **4 lần có đổi vai**: tối thiểu 4 pivot low/high tại một vùng giá, đã phản ứng ở cả vai trò hỗ trợ lẫn kháng cự; vai trò giao dịch lấy từ pivot mới nhất (được xác nhận), không dự đoán trước điểm đảo chiều.

Quy tắc bảo đảm không nhìn tương lai:
- Pivot có 3 nến trước và 3 nến sau; chỉ ghi nhận vào cuối nến thứ 3 **sau** pivot.
- Phản ứng giá tối thiểu 1,2 lần median range 240 nến gần nhất.
- Hai lần chạm phải cách nhau ít nhất 24 nến H1. Đếm tối đa 180 ngày lịch sử và một vùng hợp lệ tối đa 90 ngày.
- Độ rộng vùng nửa biên: lớn hơn giữa 6 pip và 0,75 × median biên độ nến của 240 nến lịch sử gần nhất. Đây là cách định nghĩa vùng *từ giá*, không sử dụng EMA/RSI/ATR.
- Vào khi nến H1 đóng cho thấy một lần từ chối vùng (pin/reversal body hoặc engulf phá đỉnh/đáy trước), tại giá mở nến H1 **kế tiếp**. Chỉ giao dịch 07:00–19:00 UTC ngày thường.
- Stop sau mép vùng và lớp đệm ≥1,5 pip. TP cố định ở 2,0 lần khoảng cách stop ban đầu; **lọc bắt buộc R:R dự kiến sau spread và slippage ≥1,5**.
- Không vào nếu có vùng cứng đối diện đã xác nhận nằm giữa điểm vào và mục tiêu. Bảo đảm tín hiệu không nhìn trước vùng tương lai.
- Dùng cùng 1 tài khoản 1.000 USD cho EURUSD, GBPUSD, AUDUSD, USDJPY. **0,5R = 0,5% số dư đang có** theo quy ước trước; không mở thêm nếu vị thế cũ chưa đóng, tối đa một lệnh trong mỗi tuần ISO. Không bắt buộc tuần nào cũng có giao dịch.
- Giới hạn vị thế 5× danh nghĩa, lot nhỏ nhất 0,01 (làm tròn xuống), tối đa giữ lệnh 72 giờ.

Dữ liệu: Dukascopy H1 Bid/Ask thật đã lưu checksum; không phải tick Exness. Phí mô phỏng: spread Bid/Ask tại giá mở/đóng xấp xỉ và 0,1 pip trượt giá mỗi chiều; kịch bản x2 spread. Không có swap, không có lịch tin, spread đúng lúc hit TP/SL hay khớp tick thật.

Phân tách: validation 01/01/2021–31/12/2022; holdout 01/01/2023–29/10/2026. Chỉ chọn từ validation phương án có ≥25 lệnh, lợi nhuận ròng >0, PF≥1,1, DD sau đóng lệnh ≥−15%. Thử qua holdout nếu ≥25 lệnh, lợi nhuận ròng >0, PF≥1,1, DD ≥−15% và lãi khi spread x2.

**Không thay thông số chỉ vì kết quả holdout không đẹp**. Điều kiện R:R và 0,5R áp dụng khi đặt lệnh; biến động gap có thể vượt giới hạn dự kiến. Thống kê số tuần giao dịch, tần suất thực và các tháng lợi nhuận ≥5%, ≥8%, không cam kết mục tiêu.
