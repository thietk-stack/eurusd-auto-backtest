# WinnerFX v1 — Tư duy kiếm tiền của người thắng: cắt lỗ có kỷ luật, giữ các xu hướng lớn

**Báo cáo đã hoàn thành và kiểm tra số liệu ngày 31/10/2026. Quyết định: NO-GO giao dịch tiền thật.**

## Căn cứ và đề cương trước khi chạy

- [Đề cương đã đăng ký TRƯỚC khi xem kết quả WinnerFX](DE_CUONG_WINNERFX_V1_TREND_CONVEXITY.md).
- [Workflow GitHub Actions hoàn thành thành công sau sửa phí trượt Stop Loss](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41159566809).
- [Mã có thể tái lập](scripts/winnerfx_v1.py) · [Tests](tests/test_winnerfx_v1.py) · [Workflow](.github/workflows/winnerfx_v1.yml).
- Artifact `winnerfx-v1-2011-2025-audited`, 27 tệp gồm `WINNERFX_V1_RESULTS.json`, `BAO_CAO_WINNERFX_V1.md`, `ANNUAL_REALIZED_PNL_2011_2025.csv`, 12 sổ lệnh và 12 sổ quyết định.
- Dữ liệu **Dukascopy thực** của EURUSD, GBPUSD, AUDUSD và USDJPY; **192 tháng 2010–2025 mỗi cặp, SHA256 nguồn từng tệp** được kiểm tra bởi bộ đọc `verified_16_year_data`. Có **99.712 nến H1 cùng thời điểm và 4.153 D1 có ít nhất 16 H1 quan sát thực**. Năm 2010 chỉ khởi tạo.
- Sau khi chạy lần đầu, kiểm toán phát hiện rằng Stop Loss trong nến đã dùng giá stop nhưng **chưa cộng 0,1 pip trượt giá phía thoát**. Đã sửa tính phí trượt cho mọi Stop Loss và thêm bài kiểm thử cả BUY/SELL, **không thay đổi bất kỳ tín hiệu, ngưỡng, Stop Loss hoặc TP**. Các kết quả báo cáo dưới đây là **lượt chạy sau sửa**.

## Phép thử: kiếm tiền từ những xu hướng kéo dài, KHÔNG dự báo từng nến

1. Nến D1 UTC được dựng từ H1 thực, không nội suy giờ thiếu; vào lệnh **ngày giao dịch kế tiếp** sau tín hiệu D1 đã đóng.
2. BUY khi CLOSE phá **đỉnh 55 ngày giao dịch trước** và EMA20 > EMA100; SELL khi CLOSE phá đáy 55 ngày và EMA20 < EMA100. Cùng ngày nhiều cặp đủ, chỉ chọn một cặp có mức vượt ngưỡng lớn nhất tính theo ATR20; tối đa **một vị thế mở** trên cả bốn cặp.
3. Mua Ask-open hoặc bán Bid-open H1 thật, cộng trượt giá 0,1pip mỗi chiều. SL lúc vào **3×ATR20**, tối thiểu 15 pip, nếu stop cần >400 pip thì bỏ. Khi có lãi, mỗi D1 đóng cập nhật stop tốt hơn theo **Close ±3×ATR20**, **không nới stop**, không có chốt lời cố định.
4. Đóng khi chạm stop hoặc sau **90 ngày giao dịch**. Kích thước lot theo rủi ro thiết kế 0,5% equity/lệnh, <=5× danh nghĩa, bước/tối thiểu 0,001 hoặc 0,01 standard lot. Stress spread×2 **trừ thêm ½ spread entry + ½ spread exit** trên cùng những lệnh thực hiện.
5. Đối chứng: giao dịch **ngược hướng** tại các tín hiệu phá vỡ D1, có tài khoản và quản trị rủi ro riêng. Vì thời gian giữ khác nhau, các giao dịch được chọn không ghép cặp 1–1, đây là so sánh **hai chính sách**, không phải thử nghiệm nhân quả từng lệnh.

## Kết quả — lot tối thiểu GIẢ ĐỊNH 0,001 standard lot

| Nhóm tài khoản mô phỏng $1.000 | Phương pháp | Lệnh | Thắng | PnL USD | PF | DD sau đóng | Spread×2 PnL USD | Cận dưới bootstrap 95% trung bình USD/tuần |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2011–2017 | Theo xu hướng | 50 | 40,0% | **+71,35** | 1,971 | −2,08% | +70,72 | **−0,0377** |
| 2011–2017 | Ngược xu hướng | 59 | 40,7% | +6,77 | 1,079 | −2,74% | +6,03 | −0,1103 |
| 2018–2025 | Theo xu hướng | 68 | 27,9% | **−52,23** | 0,544 | −5,68% | −53,08 | **−0,2349** |
| 2018–2025 | Ngược xu hướng | 72 | 34,7% | −53,08 | 0,552 | −6,43% | −53,89 | −0,2345 |
| **2011–2025 tài khoản liên tục** | **Theo xu hướng** | **117** | **32,5%** | **+14,93** | **1,077** | **−6,75%** | **+13,39** | **−0,1063** |
| 2011–2025 tài khoản liên tục | Ngược xu hướng | 130 | 37,7% | −46,45 | 0,773 | −7,91% | −47,99 | −0,1424 |

**Cấu trúc lợi nhuận đúng ý tưởng nghiên cứu nhưng chưa có edge mạnh:** trên 117 lệnh theo xu hướng, chỉ khoảng 32,5% thắng; **lệnh thắng trung bình +5,50 USD**, lệnh thua trung bình **−2,45 USD**, tỷ số thắng/thua ≈**2,24×**. Thời gian nắm trung bình 25,82 ngày giao dịch. Đây là đặc điểm của phương pháp giữ lời dài nhưng **không tự chứng minh kỳ vọng lợi nhuận đáng tin**.

Đặc biệt **2018–2025 âm ở cả hai chính sách**, trong khi cận bootstrap toàn kỳ **âm**. Cổng đã đăng ký từ trước yêu cầu từng nhóm ≥30 lệnh, PnL >0, PF >1,1, stress dương, bootstrap lower >0, và vượt đối chứng; **không đạt**. Không dùng kết quả dương của 2011–2017 để đánh đổi rủi ro trong 2018–2025.

## Kết quả lot tiêu chuẩn 0,01: KHÔNG có lệnh

Trên toàn bộ 2011–2025, với vốn 1.000 USD, rủi ro 0,5% và max đòn bẩy danh nghĩa 5×, **không có lệnh nào đủ điều kiện đặt 0,01 lot**. Trong 1.351 ngày phát sinh tín hiệu khi không có vị thế, **1.238 ngày** bị loại vì lot tối thiểu khiến rủi ro vượt ngân sách, **113 ngày** vì stop >400 pip. Việc giảm lot xuống 0,001 giúp vào đủ 117 lệnh, **nhưng không làm phát sinh lợi thế dương ổn định**. Mức 0,001 standard lot chưa được xác thực trên tài khoản broker cụ thể, cần đối chiếu kích thước hợp đồng Standard Cent.

## Những năm lợi nhuận không đồng đều (sổ liên tục lot 0,001)

| Năm | PnL USD | Số lệnh đóng |
|---|---:|---:|
| 2011 | −1,42 | 5 |
| 2012 | −1,44 | 7 |
| 2013 | **+59,57** | 7 |
| 2014 | +20,62 | 5 |
| 2015 | +0,69 | 8 |
| 2016 | −1,56 | 9 |
| 2017 | −6,36 | 8 |
| 2018 | −1,65 | 7 |
| 2019 | **−25,18** | 10 |
| 2020 | +2,06 | 8 |
| 2021 | −2,23 | 10 |
| 2022 | −5,13 | 8 |
| 2023 | −5,54 | 7 |
| 2024 | −9,47 | 7 |
| 2025 | −8,02 | 11 |

Tài khoản giả định từ 1.000 USD thành 1.014,93 USD sau 15 năm, **chưa trừ phí giữ qua đêm**. Kết quả bị phụ thuộc đáng kể vào năm 2013–2014, và nhiều năm sau đó âm. **Không đủ cơ sở để gọi là chiến lược thắng cuộc**.

## Ai thực sự thắng trên Forex, bài học và hướng đi

Các dealer có thể được trả công cho *cung cấp thanh khoản, chênh lệch Bid–Ask và quản trị lượng khách mua/bán*. Trader cá nhân dùng biểu đồ giá không thể giả định mình có khả năng internalize luồng giao dịch tương tự. Managed futures CTA có bằng chứng nghiên cứu cho xu hướng trên danh mục đa tài sản, nhưng dữ liệu bốn cặp USD không có sự đa dạng tài sản hay swap tương đương.

- [BIS — cấu trúc thị trường FX, dealer và nội bộ hóa dòng lệnh](https://www.bis.org/publications/qr-202512/global-fx-markets-when-hedging-takes-centre-stage)
- [AQR — bằng chứng dài hạn của giao dịch xu hướng đa tài sản](https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing)
- [JIMF 2024 — carry trade ngoài mẫu thường không bền, rủi ro lựa chọn sau khi nhìn dữ liệu](https://doi.org/10.1016/j.jimonfin.2024.103042)

**Quyết định: NO-GO đối với tiền thật.** Để học từ người chiến thắng tiếp, cần kiểm tra **nguồn lợi nhuận thực** (futures/forward carry, rủi ro xu hướng đa tài sản), tick/spread+swap thực tế và **tập forward chưa chọn lọc**. Không nên tìm một ngưỡng EMA/ATR khác trên chính 2011–2025 để hồi cứu có lãi. Không có lệnh broker nào được gửi.
