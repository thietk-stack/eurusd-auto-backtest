# WINNERFX v1 — Chiến lược học từ người chiến thắng: theo xu hướng lớn, cắt lỗ nhỏ, giữ lời dài

**Đóng băng giả thuyết: 31/10/2026, TRƯỚC khi xem kết quả chạy phiên bản này.**

## Cơ sở và giới hạn
BIS 2025 mô tả FX chủ yếu là OTC, dealer và PTF có khả năng nội bộ hóa dòng lệnh/làm giá mà trader bán lẻ không thể sao chép. Không nhầm chênh lệch spread của dealer với lợi thế dự báo chỉ từ biểu đồ. Bài nghiên cứu của Hurst, Ooi, Pedersen (AQR 2017) nêu bằng chứng xu hướng trên **danh mục futures đa tài sản**, không chứng minh rằng spot FX bốn cặp có lợi thế. Bởi vậy chỉ nghiên cứu ý tưởng **giữ vị thế khi xu hướng kéo dài, chấp nhận nhiều lệnh thua nhỏ, không áp TP 2R**, kiểm định trên báo giá Dukascopy thật.

Bốn cặp: EURUSD, GBPUSD, AUDUSD, USDJPY. Dữ liệu Dukascopy H1 Bid/Ask-open có chứng từ SHA256 từng tháng 2010–2025, chốt giai đoạn giao dịch 2011–2025 và 2010 khởi tạo. Dữ liệu 2011–2025 **đã từng được xem nhiều lần ở dự án**, nên đây là **khảo sát hồi cứu nhiều lần kiểm tra, KHÔNG phải holdout nguyên vẹn**.

## Quy tắc giá duy nhất, không tìm ngưỡng thắng sau khi chạy

1. Tạo D1 UTC từ những nến H1 chung được quan sát thật của cả bốn cặp; ngày giao dịch chỉ hợp lệ nếu có ít nhất **16 H1**; lấy D1 Open = H1 đầu tiên; High/Low từ H1 observed-mid; Close = H1 cuối ngày. Không điền giờ/giá thiếu.
2. Sau khi ngày D1 kết thúc, so sánh **giá đóng** với **max/min của 55 ngày giao dịch trước ngày tín hiệu**, tức không chứa ngày tín hiệu. LONG nếu close > max55 và **EMA20 > EMA100**, SHORT nếu close < min55 và EMA20 < EMA100. EMA đều chỉ sử dụng nến đã đóng. Cần ≥120 ngày warm-up cho EMA và ATR.
3. Nếu nhiều cặp có tín hiệu cùng ngày, chỉ chọn cặp có `abs(close-barrier)/ATR20` lớn nhất (được chốt trước), mã cặp theo thứ tự chữ khi hòa; **mỗi thời điểm chỉ giữ tối đa một vị thế** trên cả bốn cặp, không mua cùng lúc những cặp USD tương quan.
4. Vào tại **H1 đầu tiên ngày D1 tiếp theo** dùng giá Bid/Ask-open thật, BUY Ask +0,1 pip slip; SELL Bid −0,1 pip slip. Chỉ một lệnh/ngày.
5. Đặt stop ban đầu **3×ATR20 của ngày tín hiệu**, không nhỏ hơn 15pip; nếu >400pip thì hủy. Rủi ro dừng lỗ theo thiết kế ≤**0,5% vốn equity/lệnh**, max 5× danh nghĩa, làm tròn xuống bước lot. Hai phiên bản độc lập min/bước **0,01** và **0,001 standard lot (giả định broker hỗ trợ)**.
6. **Không TP cố định.** Giữ lệnh khi xu hướng còn: mỗi lần một D1 mới hoàn thành, cập nhật stop nếu có lợi hơn theo **Close D1 mới −3×ATR20 hiện tại** với BUY, hoặc Close +3×ATR20 với SELL, **không bao giờ nới stop**. Trong các giờ H1 của ngày đang giao dịch, kiểm tra stop theo midpoint High/Low ± một nửa spread OPEN của chính giờ đó, chạm stop thì thoát; gap/OPEN xuyên stop xử lý giá tệ hơn. Giả định slippage 0,1pip trên giá thoát.
7. Nếu chưa chạm stop sau **90 ngày giao dịch**, đóng tại **Open D1 tiếp theo**. Nếu dữ liệu không đủ báo giá vào thời điểm cần thoát, đánh dấu sai khác và không nhận lợi nhuận không có quan sát.
8. Stress spread ×2: giữ nguyên toàn bộ lệnh/số lot/thời gian thoát, trừ thêm chi phí tương đương **½ spread entry + ½ spread exit**. **Không có lịch sử swap/rollover và không có tick Bid/Ask high-low thực**, nên PnL là ước lượng giá spot có thể lạc quan đáng kể khi giữ qua đêm. Phải tính chi phí broker thực và forward demo trước khi dùng tiền thật.

## Báo cáo và quy tắc không tự chọn người thắng

- Chạy tài khoản độc lập khởi đầu 1.000 USD cho: **2011–2017**, **2018–2025**, **toàn bộ 2011–2025 chạy liền**. Không cộng hai kết quả độc lập thành tỷ suất của tài khoản toàn kỳ. Báo PnL USD, PF, drawdown đóng lệnh, số lệnh, thời gian giữ, thắng/lỗ, trung bình thắng/thua, annual PnL trên tài khoản 15 năm liên tục.
- So sánh **cùng điều kiện tín hiệu nhưng giao dịch ngược hướng** làm đối chứng chính sách (có thể chọn tập lệnh không hoàn toàn giống vì thời gian giữ khác nhau); không tuyên bố matched pair từng lệnh.
- Cổng chất lượng dự kiến: **mỗi nửa 2011–2017 và 2018–2025 có ít nhất 30 lệnh**, PnL dương sau spread gốc và stress, PF>1,1; **cận dưới một phía 95% block-bootstrap trên PnL/tuần theo block 8 tuần >0**; vượt đối chứng ngược chiều. Đồng thời toàn kỳ có lãi và max closed-trade drawdown không quá 15%. Không đạt => **NO-GO**. Vượt vẫn chỉ được nghiên cứu **forward demo + swap thật**, không live trading.
- Không được thay ngưỡng 55, EMA20/100, ATR3, 90 ngày, risk0,5% từ dữ liệu vừa xem để tạo kết quả dương. 2011–25 vốn đã xem là dữ liệu thăm dò; không được quảng cáo backtest đó là hiệu quả ngoài mẫu.

Nguồn công khai: https://www.bis.org/publications/qr-202512/global-fx-markets-when-hedging-takes-centre-stage ; https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing
