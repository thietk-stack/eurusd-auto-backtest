# ECONEDGE MACRO v1 — Dòng vị thế CFTC, lợi suất tiền tệ, rủi ro được trả công

**Ngày đăng ký: 31/10/2026. Chốt các quy tắc ở đây TRƯỚC khi xem kết quả nghiên cứu mới.** Đây là kiểm tra nghiên cứu, không cấp phép đặt lệnh thật.

## Ý tưởng kinh tế

Học theo người tạo lợi nhuận ở FX: phân biệt **lợi nhuận từ nhận rủi ro**, **vị thế đầu cơ và sức ép giao dịch**, và **lợi tức tài trợ/forward**. Không gọi chỉ báo giá là “dòng tiền tổ chức”. Không có order book spot FX tập trung, không lấy chênh lệch lãi suất chính sách làm swap có thể nhận.

### Nguồn 1 — Dòng vị thế: CFTC Traders in Financial Futures (TFF), futures only

- **Nguồn chính thức:** https://publicreporting.cftc.gov/resource/gpe5-46if.csv (TFF Futures Only, CFTC public reporting). Dữ liệu về số hợp đồng long/short của **asset managers** và **leveraged funds**; open interest. Mỗi bản ghi vị thế là **bản chụp tại thứ Ba**, thường công bố thứ Sáu 15:30 ET; không đại diện cho luồng tiền thực mua/bán spot liên ngân hàng.
- Khóa **độ trễ tối thiểu 13 ngày lịch kể từ ngày tham chiếu thứ Ba** trước khi dùng tại thứ Hai 08:00 UTC, giảm nguy cơ nhìn trước công bố ngày lễ. Nếu nghi ngờ trì hoãn dài hơn, phải kiểm tra lịch công bố trước khi tuyên bố backtest có thể giao dịch.
- Chỉ nhận 4 hợp đồng tương lai CME thuộc **Euro FX, British Pound, Australian Dollar, Japanese Yen**; cần xác minh mã thị trường và tên từng hợp đồng từ dữ liệu thực; không gom cùng tên với hợp đồng mini/micro hoặc cross không tương đương.
- Biến giải thích chính: `asset manager net / open interest`; đo **thay đổi bốn bản báo cáo CFTC gần nhất** của chỉ số này (không dùng phiên vị thế tương lai). Nếu các tuần thiếu dữ liệu, tối đa 8 tuần lịch cho bốn báo cáo.
- Mỗi thứ Hai 08:00 UTC, chọn cặp có `|delta_4week|` lớn nhất trong bốn cặp, đi **cùng hướng thay đổi asset-manager net**; với hợp đồng JPY long thì **SELL USDJPY**, còn EUR/GBP/AUD long thì BUY EURUSD/GBPUSD/AUDUSD. Đối chứng làm ngược hướng tại cùng tuần/cặp. Không đặt ngưỡng delta sau khi xem dữ liệu.
- Đầu vào giá: Dukascopy H1 Bid/Ask OPEN + OHLC MID, **2010 warm-up, thử 2011–2025**, 192 tháng/cặp SHA256 như dự án. Vào tại H1 Open thứ Hai, thoát trước hoặc tại **thứ Sáu 20:00 UTC** hoặc STOP.
- STOP trước tín hiệu: **6×median biên độ H1 đã đóng của 72 nến H1**, tối thiểu 8 pip, nếu >70 pip bỏ lệnh; max một lệnh một tuần, 0,5% vốn rủi ro thiết kế, min/bước 0,001 standard lot giả định, đòn bẩy danh nghĩa 5×. Sử dụng cùng công thức chi phí và kiểm toán cũ: 0,1pip slippage/side, BID ASK thật lúc Open, mô phỏng stop từ H1 midpoint high-low ±nửa spread Open, stress x2 spread bằng cách giữ nguyên giao dịch và trừ thêm chi phí. Chưa có lịch sử swap broker, do đó chỉ thể hiện PnL **biến động giá** chứ không phải carry.
- Phân kỳ: 2011–2017 và 2018–2025 khởi tạo $1000 riêng, sổ 2011–2025 chạy liên tục khởi tạo $1000. Ghi từng năm và từng hợp đồng; không cộng phần trăm từ nhóm độc lập.
- Gate: mỗi phân kỳ ≥35 giao dịch; PnL sau mô hình chi phí >0, PF>1.10, spread stress>0, **cận dưới 95% moving block bootstrap 8 tuần >0**, cùng phiên vượt đối chứng ngược; trên toàn 15 năm DD đóng lệnh không vượt 15%; nếu không đạt **NO-GO**. Bootstrap 2500 lần, seed 20261031.

### Nguồn 2 — Chênh lệch lãi suất: chỉ làm price-prediction, KHÔNG bịa swap

- Nghiên cứu độc lập dùng lãi suất liên ngân hàng kỳ hạn **3 tháng** cùng thang đo EUR, GBP, AUD, JPY, USD từ các chuỗi OECD/FRED như `IR3TIB01USM156N`, `IR3TIB01EZM156N`, `IR3TIB01GBM156N`, `IR3TIB01AUM156N`, `IR3TIB01JPM156N`, **chỉ khi các series có dữ liệu đủ thực và ghi nguồn/quan sát**. Trước mỗi lệnh phải trễ **ít nhất một tháng lịch sau tháng quan sát**, không được lấy giá đã điều chỉnh sau này làm dữ liệu realtime không sửa đổi.
- Dùng `foreign3m-rate - USD3m-rate` như tín hiệu dấu carry giả thuyết; **chỉ so sánh giá spot tương lai**. **Không cộng lãi suất vào PnL, không quy đổi 3m interbank thành swap Exness**. Carry thực cần forward points lịch sử, kỳ hạn roll, funding, collateral và spread broker.
- Cặp USDJPY dùng chiều giá ngược (JPY mạnh => USDJPY SELL). Không xem đoạn dữ liệu 2011–25 là OOS mới: nhiều chiến lược đã chạy trên cùng giá. Không thử vô hạn các ngưỡng rồi gọi discovery.

### Nguồn 3 — Rủi ro trả công / risk regime

- Mọi hệ thống phải phân tách lợi nhuận **spot price** và **thu nhập tài trợ**, drawdown/gap, spread, thời kỳ thua lỗ 2018–25. Có thể thử đơn giản điều kiện biến động dự kiến dựa trên H1 đã đóng, nhưng **không tối ưu ngưỡng trên cùng giá lịch sử**. Nhìn thấy lợi nhuận ngắn hạn của một giai đoạn KHÔNG đồng nghĩa thị trường “trả premium”.
- Nếu không truy xuất được CFTC hoặc chuỗi lãi suất chính thức, phải **fail closed**, lưu lỗi và không công bố kết quả giả.

## Chú ý về so sánh và các giới hạn

Dữ liệu CFTC là hợp đồng tương lai USD và chỉ vị thế nhóm báo cáo, không phải dòng vốn thanh toán quốc tế. Asset manager tăng net long có thể do định nghĩa/điều chuyển nhóm trader, thị trường tăng OI, hoặc hedging; không tự chứng minh nhân quả của giá tăng. Đối chứng theo cùng các tuần giúp đánh giá kỳ vọng, nhưng các hệ thống tính vốn khác nhau và số lot có thể khác nhau.

Nhiều dữ liệu giai đoạn 2011–2025 đã bị xem nhiều lần trong các cuộc tìm kiếm chiến lược trước, nên cả lần này vẫn chỉ là hồi cứu thăm dò. Để xác nhận phải chạy forward demo mới và kiểm tra broker swap/tick thực tế; không vào lệnh thật.
