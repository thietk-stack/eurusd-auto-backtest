# EconEdge FX v1 — kiểm định xu hướng 4 tuần, giao dịch một tuần, đối chứng ngược hướng

**Hoàn tất và kiểm toán ngày 31/10/2026. KẾT LUẬN: NO-GO với tài khoản tiền thật.**

- [Đề cương CHỐT TRƯỚC khi xem kết quả](DE_CUONG_ECONEDGE_TREND_TUAN_2019_2025.md)
- [GitHub Actions thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41151384843)
- [Mã chạy thật](scripts/econedge_weekly_trend.py), [bài kiểm thử](tests/test_econedge_weekly_trend.py)
- Artifact `econedge-weekly-trend-2019-2025`: `RESULTS_ECONEDGE_TREND.json`, `BAO_CAO_ECONEDGE_TREND.md`, sáu CSV giao dịch và sáu CSV quyết định đặt/bỏ lệnh. Dữ liệu nguồn EURUSD, GBPUSD, AUDUSD, USDJPY là **49.877 nến H1 cùng thời điểm, 2018–2025 Dukascopy Bid/Ask có SHA-256 theo tháng**.

## Tại sao thử phương án này?

Thay vì gắn luật nến Engulfing và chạm vùng, nghiên cứu từ một giả thuyết kinh tế đã có bằng chứng trong các thị trường **futures/forwards**: lợi nhuận có thể có động lượng theo thời gian (Moskowitz, Ooi & Pedersen, 2012, *Time Series Momentum*; AQR *A Century of Evidence on Trend-Following Investing*). Nhưng bằng chứng từ thị trường hợp đồng tương lai lớn **không thể tự động chuyển thành một lợi thế cho FX spot với vốn 1.000 USD và lot tối thiểu 0,01**.

### Điều kiện đã được đăng ký trước

- Vào **thứ Hai 08:00 UTC**, chỉ dùng **480 nến H1 đã đóng** (~4 tuần giao dịch) để đánh giá điểm động lượng đã chuẩn hóa biến động `z`.
- Chọn **duy nhất một cặp** có `|z|` cao nhất trong bốn cặp; chỉ vào khi `|z| ≥ 0,80`. Nhánh chính theo dấu `z`, nhánh đối chứng đánh hướng ngược tại **chính cặp và tuần đó**.
- Khớp **OPEN H1 Bid/Ask thật**, cộng giả định 0,1 pip trượt mỗi chiều; dừng lỗ bằng **6× median biên độ 72 H1 đã đóng**, stop tối thiểu 8 pip, bỏ nếu >70 pip. Stop MỘT PHẦN xấp xỉ bằng giá giữa Low/High H1 ± nửa spread open, không có tick Bid/Ask high/low.
- Không ép TP 2R: **giữ lệnh đến thứ Sáu 20:00 UTC** nếu chưa chạm SL. Khi thiếu báo giá tại giờ đóng, sử dụng giá giữa CLOSE của nến cuối trước hạn ± một nửa spread OPEN của nến đó làm giá thoát xấp xỉ; không bịa Bid/Ask CLOSE.
- **0,5% equity/lệnh** là rủi ro dự kiến theo stop và slippage; bước/min lot 0,01, ≤5× đòn bẩy, chỉ 1 giao dịch/tuần trên 4 cặp. **Bỏ lệnh** khi stop quá rộng hoặc tài khoản không đủ đặt lot 0,01 mà vẫn giữ rủi ro thiết kế.
- Stress spread x2 **không thay đổi lệnh/lot/stop/tín hiệu**, chỉ trừ thêm khoản tương đương ½ spread entry + ½ spread exit. Không tính swap/triple swap hoặc lãi suất vay FX. **Không thể coi lãi/lỗ giá spot là kết quả carry giao dịch thật.**

## Số liệu sau phí báo giá và trượt giá giả định

| Giai đoạn (mỗi kỳ vốn reset $1.000) | Phương án | Tuần xem xét | Lệnh KHỚP | Bỏ do min lot | Lãi/lỗ USD | Return kỳ | Profit Factor | Drawdown sau đóng | Spread x2 (USD) | Cận dưới bootstrap trung bình USD/tuần |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019–2021 khám phá | Theo xu hướng | 154 | 23 | 38 | **+10,29** | +1,03% | 1,214 | −1,78% | +9,10 | **−0,169** |
| 2019–2021 khám phá | Ngược hướng | 154 | 19 | 42 | −27,32 | −2,73% | 0,510 | −4,80% | −28,27 | −0,408 |
| 2022–2023 validation | **Theo xu hướng** | 103 | **1** | 16 | **−3,90** | −0,39% | 0,000 | −0,39% | −3,93 | **−0,114** |
| 2022–2023 validation | Ngược hướng | 103 | 1 | 16 | +13,76 | +1,38% | — | 0,00% | +13,73 | 0,000 |
| 2024–2025 kỳ sau | **Theo xu hướng** | 102 | **10** | 13 | **+20,57** | +2,06% | 1,897 | −1,37% | +20,04 | **−0,209** |
| 2024–2025 kỳ sau | Ngược hướng | 102 | 9 | 14 | −31,65 | −3,16% | 0,066 | −3,38% | −32,18 | −0,501 |

Mỗi giai đoạn bắt đầu bằng một sổ vốn 1.000 USD riêng; **không cộng tỷ suất kỳ thành lãi kép nhiều năm**. Không phải năm nào cũng có nhiều lệnh. **2024–2025 chỉ có 10 lệnh theo xu hướng**, nên dù kết quả +2,06% trong hai năm vẫn không phải bằng chứng mạnh về khả năng sinh lời.

### Giải thích tại sao không giao dịch

**Vướng mắc số một: không đủ kích thước lệnh phù hợp.**
- Với **103 tuần giai đoạn validation 2022–23**, hệ thống bỏ **65 tuần do stop cần rộng hơn 70 pip**, 21 tuần do tín hiệu động lượng yếu, 16 tuần do không thể đặt lot tối thiểu 0,01 mà vẫn giữ ngân sách rủi ro 0,5%, còn lại chỉ **một giao dịch** đủ các điều kiện.
- Điều này không chứng minh tín hiệu xu hướng không có khả năng dự báo. Nó chỉ cho thấy **phiên bản chính sách giao dịch hiện tại không thể triển khai thường xuyên với 1.000 USD và stop theo biến động**.
- **Đổi sang 0,001 lot** có thể là một bài nghiên cứu độ nhạy nếu xác nhận broker hỗ trợ, nhưng không được tự xem là tài khoản spot đã có điều kiện như vậy. **Nới rủi ro hơn 0,5% hoặc tăng đòn bẩy không giải quyết bài toán lợi thế.**

**Vướng mắc số hai: bootstrap chưa xác nhận được lợi thế.**
- Dù giai đoạn 2019–21 và 2024–25 có lãi theo mô phỏng, **cận dưới một phía 95% của trung bình PnL theo khối 8 tuần vẫn âm**.
- Validation còn **không đủ 35 lệnh** theo cổng chất lượng đã đăng ký trước, nên **validation_pass=False**.
- Kỳ 2024–2025 **không đủ 45 lệnh** và cận dưới bootstrap vẫn âm, nên **later_pass=False**.
- **Quyết định: NO-GO giao dịch tiền thật**, ngay cả khi có một vài năm lãi.

### Mức độ giới hạn của kiểm định

Đây là dữ liệu lịch sử Forex spot BID/ASK H1, không phải hợp đồng tương lai AQR; H1 chỉ có Bid/Ask ở OPEN, nên khoảng stop intrabar dùng một giá xấp xỉ, không biết thứ tự tick; spread thực Exness, swap qua đêm, triple swap, lãi suất tài trợ, tin kinh tế và trượt giá khi gap không được xác nhận.

Các năm 2019–2025 đã được sử dụng qua nhiều nghiên cứu trong dự án, do đó **không có holdout hoàn toàn mới ở cấp dự án**. Một kết quả lãi trên kỳ 2024–25 không thể được gán là khám phá độc lập vì trước đó đã nhìn các năm này theo cách khác.

## Hướng tiếp theo, không chỉnh hậu nghiệm để "săn lãi"

Để trả lời xem **tín hiệu dự báo hướng giá** hay chỉ là không khớp với giới hạn rủi ro và kích thước hợp đồng, cần chạy thêm một chẩn đoán **chỉ đọc**: đo hướng biến động tuần sau cho *toàn bộ tín hiệu động lượng* mà không áp đặt lot/SL. Báo **pip**, không biến pip này thành lợi nhuận tài khoản; đây là kiểm tra bổ sung thực hiện **sau khi đã thấy kết quả** và không được gọi là validation nguyên vẹn.

Nghiên cứu carry muốn có ý nghĩa thực tế phải có **lịch sử chênh lệch lãi suất từng ngày và lịch sử phí/swap của chính broker**, thay vì suy ra carry từ OHLC. Nghiên cứu tin tức phải có lịch phát hành theo thời điểm và báo giá tick tương ứng. Trong mọi trường hợp: không gửi lệnh thật khi chưa đủ số liệu.
