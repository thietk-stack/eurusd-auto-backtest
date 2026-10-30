# QuantMind FX v2 — False-Break Reclaim + Quote Spread, dữ liệu M1

Ngày chốt: **31/10/2026**, chốt **trước lần xem hiệu quả giao dịch**. Đây là thử nghiệm mới; không tuyên bố phát hiện hiện tượng chưa ai biết, không có live trading.

## Giả thuyết về giá (không suy diễn order flow)
- Dữ liệu đầu vào **M1 Bid và Ask THẬT** từ Dukascopy, mã nguồn gốc và SHA-256 cho từng tháng/cặp; không tổng hợp M1 từ H1/M15.
- Với mỗi nến M1 vừa đóng, tính **đỉnh cao nhất và đáy thấp nhất của 60 nến M1 đã đóng trước nến tín hiệu**. Yêu cầu 60 nến đó trải dài không quá 90 phút lịch, để tránh vô tình nối phiên đứt quãng.
- **False-break lên:** High nến tín hiệu vượt đỉnh 60 nến trước ít nhất **0,8 pip** nhưng Close đóng trở lại **thấp hơn đỉnh cũ 0,1 pip**, vẫn ở trong vùng cũ. Phương án reversal **SELL**, đối chứng continuation **BUY**.
- **False-break xuống:** Low vượt đáy cũ ít nhất 0,8 pip, Close đóng lại **cao hơn đáy cũ 0,1 pip**. Phương án reversal **BUY**, đối chứng continuation **SELL**.
- M1 sau nến tín hiệu phải liền kề thời gian đúng 60 giây; chỉ xét thứ Hai–thứ Sáu, 07:00–17:00 UTC.
- **Spread filter** quan sát tại lúc tín hiệu M1 đã đóng: Close Ask−Close Bid ≤ 2,5 pip và ≤ 1,25 lần **median spread close của 120 M1 trước**. Spread tại OPEN phút vào lệnh ≤ 2,5 pip.
- Đây là phép đo **phá vỡ giả/tái chiếm bằng giá**, *KHÔNG chứng minh lệnh dừng của người khác đã bị “quét” hay có order book/volume toàn thị trường*. Cũng không dùng thuật toán LLM nhìn tương lai.

## Thử nghiệm thực thi hai hướng độc lập
- **Reversal (giả thuyết chính):** SELL sau false-break lên, BUY sau false-break xuống.
- **Continuation (đối chứng):** giao dịch theo hướng phá vỡ ở đúng sự kiện tương ứng; nếu reversal không tốt hơn continuation rõ ràng thì không có cơ sở nói mô hình “reclaim” tạo lợi thế.
- Entry tại **OPEN nến M1 ngay sau tín hiệu**, dùng **Ask+0,1 pip** BUY và **Bid−0,1 pip** SELL (giá thực thi ước lượng). Không vào các nến khác và không vào khi thiếu giá.
- SL: ngoài High/Low nến false-break **1 pip**; mỗi hướng lấy mức đối diện hợp lý theo định nghĩa. Khoảng SL ở giá thực thi nằm từ 2–45 pip, chỉ đặt lệnh khi cấu trúc rủi ro hợp lý.
- TP theo **2R ròng dự kiến**, đã tính giá Bid/Ask và giả định slippage 0,1 pip mỗi chiều. Trong một nến M1 vừa chạm SL vừa chạm TP thì **SL trước**, trong nến vào chỉ tính SL nếu chạm; không nhận TP cùng nến khi chưa có tick.
- Vốn giả định ban đầu $1000, rủi ro thiết kế theo SL+slippage ≤ **0,5% số dư mỗi lệnh**, làm tròn lot xuống 0,01 và giới hạn danh nghĩa 5x; **tối đa một entry mỗi tuần ISO** trên cả EURUSD, GBPUSD, AUDUSD, USDJPY; không ép lệnh. Giữ tối đa 120 M1 quan sát.
- Kịch bản stress x2 spread dựa trên phí bổ sung từ spread đầu vào, với điều kiện số lệnh có thể thay đổi. **Không tính swap, độ trễ, market impact, giá thực thi Exness và thứ tự tick M1**.

## Kiểm định và cổng chất lượng
- **Lượt đầu tháng 01/2024 chỉ là kiểm tra hệ thống tải dữ liệu, đơn vị pip, giá khớp hai phía, và thuật toán. Không dùng số liệu một tháng để chọn hướng/điều chỉnh tham số.**
- Sau khi pipeline đạt, mở rộng sang các mốc thời gian tách biệt; mọi ngày/năm kiểm định phải công bố rõ, không gọi kết quả của tháng đơn lẻ là kết quả cả năm.
- Không kết luận hệ thống có lợi thế nếu **dưới 30 giao dịch**; cần tổng lãi sau phí >0, stress spread x2 >0, profit factor >1,1 và **cận dưới Wilson 95% một phía** cho tỷ lệ thắng >1/3 (chỉ là kiểm định sơ bộ, chưa sửa cho phụ thuộc thời gian/nhiều thử nghiệm). Nếu không qua => **NO-GO**.
- Với nhiều nghiên cứu trước 2019–2025, các giai đoạn này **không còn holdout hoàn toàn chưa nhìn thấy ở cấp dự án**. Không tăng đòn bẩy/giao dịch thật dù vượt một cổng duy nhất; bắt buộc forward demo rồi xác nhận tick broker.

[Mã tải M1 thật](scripts/download_m1_four_pairs.mjs) · [Mã nghiên cứu](scripts/quantmind_m1_reclaim.py) · [Kiểm thử](tests/test_quantmind_m1_reclaim.py).
