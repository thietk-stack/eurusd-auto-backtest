# QuantMind FX v1 — AI xác suất + trí nhớ tình huống — kiểm định thật và kết luận

**Ngày nghiên cứu:** 31/10/2026.  
**Trạng thái:** **Đã hoàn thành backtest** trên GitHub Actions; **NO-GO** giao dịch tiền thật.

- [Đề cương cố định trước kết quả](DE_CUONG_QUANTMIND_FX_XAC_SUAT.md)
- [GitHub Actions lần cuối: thành công, có toàn bộ dự báo lịch sử](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41142808221)
- Artifact `quantmind-probability-study`, gồm `QUANTMIND_RESULTS.json`, `BAO_CAO_QUANTMIND.md`, **18.598 dòng dự báo lịch sử ở ba kỳ hiệu chỉnh/validation/holdout**, và CSV các lệnh được vào (rỗng vì bị từ chối).
- [Mã nguồn mô hình](scripts/quantmind_probability.py) và [kiểm thử](tests/test_quantmind_probability.py).

## Hệ thống này thực sự làm gì?

1. Từ **49.877 nến H1 đồng thời trên bốn cặp EURUSD, GBPUSD, AUDUSD, USDJPY** thuộc 2018–2025, tính **25 đặc trưng** từ dữ liệu quá khứ đã đóng (xu hướng nhiều cửa sổ, đường đi/hiệu quả, các bóng nến, breakout, biến động, độ đồng pha USD, spread, giờ giao dịch, mã cặp). H1 được chọn cho phép thử đầu tiên để tạo nhiều sự kiện nhất quán; không ngụy tạo nến M15.
2. **AI thống kê**: học máy histogram gradient boosting về xác suất **TP +2R trước SL −1R**, tối đa 24 nến H1. Nếu cùng một nến chứa hai barrier, tính SL trước. Spread Dukascopy mở giờ và giả định slippage 0,1 pip mỗi chiều được tính vào khoảng TP/SL.
3. **Trí nhớ tình huống**: truy hồi **40 trường hợp giống nhất từ tập huấn luyện 2019–2022**, làm trơn tỷ lệ thắng về prior để giảm ảo tưởng 100%.
4. **AI tự phản biện**: trừ điểm khi xác suất bộ dự báo và xác suất từ 40 tương tự không đồng thuận. Bắt buộc p_mô_hình ≥40%, p_tương_tự ≥40%, p_kết_hợp ≥48%. Không ép số lệnh; đòn bẩy ≤5x, mỗi lệnh rủi ro thiết kế 0,5% vốn; tối đa một giao dịch mỗi tuần trên cả 4 cặp.
5. **Không gọi mô hình ChatGPT qua API cho từng nến**. ChatGPT tham gia trực tiếp trong vai trò **thiết kế, viết mã, kiểm toán và ra quyết định GO/NO-GO nghiên cứu**, còn các xác suất là của mô hình định lượng đã chạy trên dữ liệu thật. Không có auto-trading ở tài khoản người dùng.

## Chia kỳ ngăn rò rỉ dữ liệu

| Kỳ | Mục đích | Số cặp-sự kiện dự báo |
|---|---|---:|
| 2019–2022 | Huấn luyện mô hình và kho trí nhớ tương tự | **24.898** |
| 01–06/2023 | Hiệu chỉnh sigmoid trên tập tách biệt | **3.094** |
| 07–12/2023 | Kiểm định validation, cổng GO/NO-GO | **3.072** |
| 2024–2025 | Kiểm tra theo thời gian về sau, không chọn lại tham số | **12.432** |

**Quan trọng:** Một sự kiện là một hướng/cặp tại một thời điểm (cả BUY và SELL là ứng viên), nhiều sự kiện có nhãn tương quan; **không** được coi là 12.432 giao dịch độc lập. Các năm 2024–25 đã được xem trong nghiên cứu *khác* trước đây, nên không phải holdout còn nguyên vẹn ở cấp dự án.

## Kết quả kiểm định xác suất

| Giai đoạn | Tỷ lệ thực tế TP chạm trước SL | Xác suất mô hình trung bình | AUC | Brier mô hình | Brier dự báo nền cố định | Số lệnh được chấp nhận |
|---|---:|---:|---:|---:|---:|---:|
| 2023 nửa đầu — hiệu chỉnh | 28,25% | 27,12% | 0,5129 | 0,20313 | **0,20296** | **0** |
| 2023 nửa cuối — validation | 30,63% | 27,17% | 0,5139 | 0,21394 | **0,21254** | **0** |
| 2024–2025 — kiểm tra về sau | 29,42% | 27,14% | 0,5080 | 0,20840 | **0,20765** | **0** |

Brier **thấp hơn** là tốt hơn; mô hình **cao hơn (tệ hơn)** dự báo nền ở cả ba kỳ. AUC khoảng 0,50 tương đương khả năng phân hạng gần ngẫu nhiên. Phân bố điểm dự báo được xuất dưới dạng CSV đầy đủ để đối chiếu chứ không chọn vài ví dụ thuận lợi.

### Vì sao hệ thống không vào lệnh?

- **Xác suất cao nhất mà mô hình xác suất đưa ra trong 2024–2025 chỉ 31,18%.**
- Xác suất từ **trí nhớ tình huống** có lúc lên tới 54,98%, nhưng mô hình chính **không xác nhận**; bộ lọc bất đồng đã từ chối.
- Xác suất tổng hợp cao nhất trong 2024–2025 vẫn **31,18%**, dưới cả **mức hòa vốn 33,33%** cho payoff +2R/−1R (với giả định 2R đã là ròng sau phí).
- Cổng vận hành đã chốt cao hơn (48%), nên **0 ứng viên đủ điều kiện** cả calibration, validation và holdout; **0 giao dịch** được thực hiện. **Lợi nhuận tài khoản 0% chỉ có nghĩa không giao dịch**, hoàn toàn không có nghĩa mô hình sinh lời hay ít rủi ro trên thị trường thực.

### Rủi ro còn chưa mô phỏng đầy đủ

H1 là dữ liệu giá trung bình OHLC với spread Bid/Ask ở OPEN, **không có tick Exness thực tế hoặc Bid/Ask High/Low**; nếu một giờ chạm hai barrier, giả định SL trước. Chưa có swap, rollover, chi phí tài trợ, market impact, lịch tin, thanh khoản và độ trễ. Drawdown tính sau các lệnh đóng; nếu có lệnh, gap có thể khiến mức thua thực vượt ngân sách 0,5%.

## Quyết định nghiên cứu

**NO-GO.** Mô hình không vượt dự báo nền và không tìm được xác suất kỳ vọng đủ cao để mở vị thế. Việc hạ ngưỡng 48% sau khi xem kết quả **sẽ là tối ưu hóa hậu nghiệm**; trong phép thử này thậm chí mức xác suất dự báo lớn nhất còn dưới hòa vốn +2R/−1R.

Hướng nghiên cứu tiếp theo hợp lệ cần **nguồn dữ liệu mới tạo khác biệt về thông tin**, ví dụ Bid/Ask **tick** cùng các thống kê spread thay đổi theo giây, thứ tự quét thanh khoản, dữ liệu order flow/futures hoặc tin kinh tế theo thời điểm phát hành, sau đó chốt giả thuyết mới và dùng giai đoạn chưa nhìn thấy/forward demo. Không có cơ sở nói hệ thống “chưa từng ai nghĩ ra” hoặc chắc chắn đem lại 5–8%/tháng. Các kỹ thuật nền tảng đã có trong giới học thuật.

## Tài liệu nền

- Marcos López de Prado, *Advances in Financial Machine Learning*, chương triple-barrier.
- Bailey & López de Prado (2014), *The Deflated Sharpe Ratio* (rủi ro kiểm định quá nhiều).
- Scikit-learn Probability Calibration documentation (xác suất cần kiểm định bằng dữ liệu tách biệt).
