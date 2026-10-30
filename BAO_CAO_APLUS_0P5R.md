# Kết quả kiểm định A+ — rủi ro 0,5R, R:R ≥1:1,5 (30/10/2026)

## Trạng thái

**Backtest hoàn thành trên dữ liệu EUR/USD, GBP/USD, AUD/USD, USD/JPY thực từ Dukascopy; KHÔNG phát hiện lợi thế đủ mạnh để giao dịch tiền thật.**

- [Đề cương A+ đã chốt](DE_CUONG_TIN_HIEU_APLUS_0P5R.md)
- [GitHub Actions run thành công — kết quả cuối](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41091173869)
- Artifact lưu `RESULTS_APLUS.json` và 4 sổ lệnh CSV: `aplus-fourpair-signal-study`.
- [Mã nguồn](scripts/aplus_signals.py)

## Quy tắc chốt trước đánh giá

- Theo quy ước 1R=1% equity, **0,5R = tối đa 0,5% vốn rủi ro theo dừng lỗ thiết kế mỗi lệnh**, làm tròn lot xuống, đòn bẩy hiệu dụng tối đa 5x.
- R:R **dự kiến sau chi phí** tại thời điểm mở lệnh **≥1,5**: lệnh có tỷ số thấp hơn bị loại, không thể đổi bằng điểm.
- Tối đa **một lệnh mỗi tuần trên toàn bộ 4 cặp**, chỉ một vị thế mở cùng lúc; không bắt buộc tuần nào cũng có lệnh.
- Các xác nhận: hai nhóm EMA theo chân trời H1, pin/engulfing, RSI động lượng, cấu trúc breakout hoặc EMA reclaim, ATR theo trạng thái biến động, spread và khung giờ. Phân kỳ RSI đã xác nhận là 1 điểm thưởng.
- Không giả tạo volume tập trung hoặc lịch tin tức: bộ dữ liệu hiện chưa có dữ liệu phù hợp.
- Thoát SL/TP, tối đa 72 giờ; cùng nến chạm cả hai thì coi SL trước. Dữ liệu nến H1 **không** cho thứ tự tick chính xác.

## Kết quả chính

Vốn nghiên cứu 1.000 USD, độc lập giữa mỗi thời kỳ. Spread thực quan sát Dukascopy ở giá mở dùng để ước tính chi phí; slippage 0,1 pip mỗi chiều. Không có swap/rollover lịch sử, không phải báo giá khớp lệnh thật của Exness.

| Chỉ tiêu | Validation 2021–2022 | Holdout 2023–2026 |
|---|---:|---:|
| 1 tuần tối đa 1 tín hiệu (thực hiện) | 100 | 179 |
| Lợi nhuận sau chi phí | **−6,41%** | **+1,41%** |
| Vốn cuối kỳ | 935,94 USD | 1.014,06 USD |
| Tỷ lệ thắng | 31,0% | 39,1% |
| Profit factor | 0,7403 | 1,0337 |
| Drawdown theo lệnh đã đóng | −7,92% | −4,64% |
| Tháng đạt +5% | 0 | 0 |
| Tháng đạt +8% | 0 | 0 |
| Chi phí giao dịch thực nghiệm | 13,42 USD | 27,85 USD |
| Kịch bản spread x2 | **−5,24%** | **−6,33%** |

Có 10/100 giao dịch validation và 15/179 giao dịch holdout được cộng điểm vì phân kỳ RSI. Phần lớn lệnh A+ đạt 8 điểm, số nhỏ đạt 9.

- R:R dự kiến thấp nhất trong giao dịch holdout **1,501**.
- Mức rủi ro thiết kế lớn nhất khi vào lệnh holdout: **5,12 USD** tương đương khoảng 0,5% vốn tại thời điểm vào.
- Khoảng **12/179 lệnh holdout** có lỗ hiện thực hóa lớn hơn rủi ro dự kiến ở thời điểm vào lệnh do giả định khớp giá/gap/chi phí. **Rủi ro 0,5R không được bảo đảm trong thực tế.**

## Đánh giá

1. Tần suất đã gần một lệnh/tuần nhưng tỷ lệ thắng validation chỉ 31%, hiệu suất âm sau phí; tín hiệu A+ là **định nghĩa confluence**, chưa phải tín hiệu đã chứng minh xác suất cao.
2. Giai đoạn holdout dương nhẹ nhưng PF chỉ 1,034; spread x2 biến thành lỗ. Không đủ để ra quyết định dùng vốn.
3. Có thể thử mô hình cảnh báo A+ (không thực thi), nhưng chưa đủ điều kiện triển khai bot giao dịch tiền thật.
4. Bất kỳ lần thay đổi trọng số/điểm hay ngưỡng EMA–RSI sau khi nhìn kết quả đều là điều chỉnh theo dữ liệu đã xem; muốn xác nhận phải có thời kỳ hoàn toàn mới, forward demo, hoặc một tập dữ liệu chưa nhìn thấy.

**Kết luận: NO-GO cho tiền thật; A+ có thể được giữ làm giả thuyết để nghiên cứu, chưa chứng minh 5–8%/tháng.**
