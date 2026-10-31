# Đề cương đã khóa: ECONEDGE FX v1 — xu hướng nhiều tuần, kiểm tra tuần kế tiếp

**Ngày chốt:** 31/10/2026; các thông số này cố định TRƯỚC khi xem kết quả mô phỏng mới.

## Tại sao nghiên cứu

Tài liệu thực nghiệm Moskowitz, Ooi & Pedersen (2012) (*Time Series Momentum*, Journal of Financial Economics, 104:228–250) nêu tính kéo dài theo thời gian ở futures/forwards và nhiều thị trường. Kết quả đó không có nghĩa hệ thống giao dịch Forex spot 1.000 USD của ta tự động có lãi. Ta cần kiểm định riêng thị trường, chi phí và khối lượng nhỏ.

**Chỉ có một giả thuyết chính**: hướng biến động đã hình thành trong **480 nến H1 có dữ liệu thực cùng cặp** (~4 tuần giao dịch) có thể tiếp diễn trong tuần kế tiếp. **Đối chứng hướng ngược lại tại cùng thời điểm và cùng cặp được chọn theo |z|**, không chọn lại cặp theo hậu nghiệm.

## Dữ liệu và điểm vào

- Các cặp EURUSD, GBPUSD, AUDUSD, USDJPY; nguồn dữ liệu lịch sử **Dukascopy H1 BID/ASK** có SHA-256 theo tháng. Đọc 2018–2025 đã lưu; 2018 khởi động. Không có dữ liệu lãi suất, lãi qua đêm hoặc lịch sử swap Exness, **không phép tính carry trade giả**.
- Chỉ ra quyết định **thứ Hai 08:00 UTC** từ **toàn bộ H1 đã đóng trước 08:00**. Tính log-return trong 480 nến H1 trước, lấy tổng lợi nhuận trên khoảng 480 nến chia cho volatility lịch sử cùng cửa sổ nhân căn bậc hai số nến, được **z-score momentum**.
- Chọn cặp có |z| cao nhất trong bốn cặp. Chỉ giao dịch nếu |z| **≥0,80** (ngưỡng cố định).
- Chiến lược chính BUY nếu z>0, SELL nếu z<0. Đối chứng ngược hướng vào **cùng cặp** khi đúng cùng sự kiện xuất hiện. Không ép tuần nào có lệnh.
- Entry tại **OPEN H1 thực thứ Hai** (BUY lấy Ask, SELL lấy Bid), cộng giả định trượt 0,1pip/chiều.
- Không áp đặt TP cố định 2R. SL = **6× median biên độ High–Low của 72 nến H1 đã đóng trước entry**, tối thiểu **8 pip**, tối đa **70 pip**. Nếu >70 pip thì bỏ lệnh chứ không co stop cho đẹp.
- Stop kiểm tra bằng low/high H1 midpoint cộng/trừ **½ spread tại open nến thoát** làm xấp xỉ bid-low/ask-high; nếu bar open qua stop thì cắt ở giá open tệ hơn. Không giả định biết thứ tự tick nội H1. **Vị thế đóng vào thứ Sáu lúc 20:00 UTC** hoặc stop trước. Không giữ qua cuối tuần; nếu phiên thiếu dữ liệu thì đóng theo báo giá quan sát cuối trước hạn.
- Không dời stop hoặc chốt lợi nhuận theo dấu hiệu hậu nghiệm. Lãi/lỗ thực theo giá Bid/Ask open/close; spread đã nằm trong giá, chỉ trừ thêm giả định slippage 0,1pip mỗi chiều, không trừ spread hai lần.
- **Rủi ro thiết kế stop và slippage ≤0,5% vốn/lệnh**. Lot chuẩn min/bước 0,01, danh nghĩa ≤5× equity, chỉ một vị thế/tuần cho cả 4 cặp; 1R = 1% vốn. Nếu không đủ lot tối thiểu/rủi ro thì bỏ lệnh.
- Kiểm định độ nhạy spread ×2 bằng cách giữ nguyên lệnh/SL/TP/lot và **trừ thêm chênh lệch spread gốc tại entry** (xấp xỉ chi phí bổ sung roundtrip) ra khỏi PnL. Chi phí qua đêm **chưa có nên kết quả có khả năng lạc quan** so với spot FX broker, dù không giữ qua cuối tuần.

## Tách giai đoạn, không tối ưu thông số theo holdout

- 2018 warm-up.
- 2019–2021: khám phá (dùng để hiểu lỗi, KHÔNG sửa tham số đã chốt nếu kiểm tra hiệu quả).
- 2022–2023: validation.
- 2024–2025: kỳ kiểm tra theo thời gian về sau.
- **Cả 2019–2025 đã xuất hiện trong các chiến lược trước** nên không có kỳ holdout “nguyên vẹn” ở cấp nghiên cứu. Không được khẳng định giá trị dự báo mới đã xác nhận hoàn toàn chỉ vì lần test này dương.
- Mỗi giai đoạn bắt đầu với 1.000 USD mô phỏng **riêng**; không cộng phần trăm qua các giai đoạn thành lợi nhuận kép.
- Chính sách đánh giá: ít nhất **35 lệnh validation**, PnL sau phí dương, stress spread ×2 dương, PF>1,10 và outperform placebo ngược hướng trên cùng các mốc; kỳ sau ≥45 lệnh, PnL dương, stress dương, PF>1,10 và outperform placebo. Yêu cầu **cluster block bootstrap theo 8 tuần** đối với lợi nhuận USD mỗi tuần; cận dưới một phía 95% của tổng trung bình tuần >0 để xem là tín hiệu thống kê sơ bộ. Nếu không đạt => NO-GO. Có thắng cũng chỉ chuyển qua kiểm định forward demo + phí swap, không dùng tiền thật.

## Carry và tin tức sẽ được nghiên cứu thế nào

Không suy diễn carry/swap từ spot H1. Để nghiên cứu carry cần thu thập chênh lệch lãi suất qua từng ngày + lịch sử swap/commission broker Exness (lịch sử điều chỉnh, triple swap); đối chiếu tháng/dữ liệu lịch thay đổi. Để nghiên cứu tin tức cần **timestamp phát hành** và giá tick sau sự kiện, tránh dùng dữ liệu đã sửa sau tin. Không đưa PnL carry/tin tức nếu chưa có các nguồn hợp lệ.

Tham khảo: https://doi.org/10.1016/j.jfineco.2011.11.003 ; https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing ; https://www.banque-france.fr/en/publications-and-statistics/publications/carry-trades-and-volatility-risk .
