# QuantMind FX v1 — đăng ký kiểm định xác suất trước kết quả

**Ngày đăng ký:** 31/10/2026. Đây là giả thuyết phối hợp mô hình học máy, trí nhớ tình huống và cơ chế từ chối giao dịch; **không tuyên bố độc nhất thế giới**, không bảo đảm lợi nhuận, **không đặt lệnh thật**.

## Vấn đề thay đổi
Không dùng mô hình nến Engulfing, không áp đặt 3/4 lần chạm, không tìm RSI “thần thánh”. Học xác suất sự kiện **giá đến TP +2R trước SL −1R trong 24 nến H1 quan sát tiếp theo**, từ thông tin đã đóng trước khi vào lệnh, với stop-first trên nến chạm cả hai mức. Nếu chưa chạm sau 24 nến, đóng theo giá quan sát cuối cùng. Lệnh chỉ mô phỏng.

**Bốn cặp** EURUSD, GBPUSD, AUDUSD, USDJPY, dùng giá lịch sử **Dukascopy H1 Bid/Ask thật** 2018–2025, hash SHA-256. Năm 2018 cho feature warm-up. Chỉ xem giao dịch ở mốc 08:00, 12:00, 16:00 UTC ngày thường; cả BUY và SELL đều là ứng viên, thuật toán chọn hoặc không chọn.

## Hai “bộ não” không biết trước tương lai

1. **Bộ dự báo xác suất:** HistGradientBoostingClassifier với số vòng/độ phức tạp cố định, học trên 2019–2022; xác suất hiệu chỉnh bằng sigmoid trên **nửa đầu 2023** riêng, không dùng holdout. Nhiều đặc trưng giá điển hình được tính chỉ từ nến đã đóng: động lượng 3/12/24/72 giờ, vị trí giá so với 24/72 nến, độ hiệu quả tuyến đường, độ biến động tương đối, bất đối xứng bóng nến, độ sâu breakout, autocorrelation xấp xỉ, tương quan chuyển động chung các cặp, spread đầu vào, giờ/phiên.
2. **Trí nhớ tình huống:** KNN trên feature đã chuẩn hóa từ **2019–2022**, lấy 40 tình huống gần nhất về mặt hình học (không phải 40 nến gần nhất theo thời gian). Xác suất thắng KNN được co về xác suất gốc bằng prior Beta, giảm quá tự tin khi bằng chứng ít.

**“Phản biện AI” là luật định lượng:** nếu hai nguồn xác suất mâu thuẫn nhiều thì giảm điểm; không lấy đầu ra một LLM làm nhãn lịch sử hoặc cho phép mô hình nhìn tương lai. Xác suất cuối = 0,65×p_model + 0,35×p_analog − 0,35×|p_model−p_analog|. Chỉ xem xét lệnh khi p_model≥0,40, p_analog≥0,40, p_final≥0,48. Các ngưỡng đều cố định **trước khi xem lợi nhuận**.

## Lệnh, TP, SL và vốn

- Vào tại OPEN H1 kế tiếp sau tín hiệu, tính phí bằng spread Bid/Ask Dukascopy đầu nến và giả định 0,1 pip trượt mỗi chiều. Do dữ liệu H1 không có đầy đủ giá Bid/Ask High/Low tick, giá khớp nội nến là **mô hình gần đúng theo mid OHLC**, không phải backtest tick Exness.
- Stop theo biên độ gần đây: max(6 pip, 1,25 × median High−Low 48 nến H1 đã đóng). TP được đặt sao cho **lợi nhuận ròng dự kiến 2R** sau mô hình chi phí, i.e. target distance = 2×stop distance + 3×estimated roundtrip cost.
- 1R vốn theo quy ước = 1% equity, đặt vị thế sao cho stop + phí rủi ro tối đa thiết kế **0,5% vốn/lệnh**, không quá 5× đòn bẩy; lot làm tròn xuống 0,01. **Tối đa 1 lệnh được vào/tuần ISO trên cả bốn cặp**, không ép tuần nào cũng có lệnh. Chọn lệnh đầu tiên theo thời gian đủ điều kiện, khi đồng thời chọn xác suất hiệu chỉnh cao nhất.
- Dữ liệu nhãn hàng rào **không được cắt qua ranh giới train/validation/holdout**. Không rò rỉ “lợi nhuận tương lai” sang feature.

## Chia kỳ và tiêu chí NO-GO

- 2018 warm-up, **2019–2022** train, **01–06/2023** hiệu chỉnh xác suất, **07–12/2023** validation kiểm tra đủ lệnh/lợi nhuận/Brier, **2024–2025** holdout (chronologically later, dù các năm này đã xuất hiện trong những nghiên cứu chiến lược trước, nên không phải “holdout nguyên vẹn” ở cấp dự án).
- Cố định chỉ **một cấu hình chính** không điều chỉnh theo kết quả; so sánh với bộ dự báo xác suất gốc vô điều kiện và xác suất không hiệu chỉnh, đo Brier/AUC và calibration.
- Cổng validation: ít nhất 8 lệnh, lợi nhuận dương sau phí, PF>1,05, Brier < baseline prior. Nếu thất bại, chính thức **NO-GO**; holdout vẫn xuất để kiểm tra giả thuyết nhưng không dùng để chọn lại ngưỡng hay mô hình.
- Cổng holdout: kết quả sau phí >0, PF>1,1, spread x2 vẫn dương, DD lệnh đóng >−15%, và ≥30 giao dịch để có cơ sở sơ bộ. Chỉ vượt cổng cũng **chưa có quyền dùng tiền thật** cho đến khi forward demo và swap thực tế.

Không có swap, lịch tin, độ trễ, spread Exness, tài trợ tiền qua đêm, kiểm toán tick. Chống tối ưu quá mức bằng cách lưu mọi trial và **không thử thông số khác để làm đẹp kỳ 2024–25**. Các khái niệm triple-barrier, hiệu chỉnh xác suất, backtest overfitting đã có trong tài liệu học thuật; “QuantMind” chỉ là cách kết hợp cho dự án.

Tham khảo:
- López de Prado, *Advances in Financial Machine Learning*, chapter 3 (triple-barrier/meta-labeling).
- Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*.
