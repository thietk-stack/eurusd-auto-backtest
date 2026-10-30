# EUR/USD — so sánh chiến lược GitHub với giao dịch định lượng (30/10/2026)

**Kết luận: CHƯA XÁC NHẬN ĐƯỢC LỢI THẾ LỢI NHUẬN.** Trên bộ dữ liệu thật H1, cả bản chuyển thể chiến lược công khai và phương án định lượng đều lỗ sau chi phí giả định Exness.

## Tài liệu và nguồn kiểm toán

- [GitHub Actions — lượt chạy thành công #1](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41087216252); artifact `eurusd-github-quant-comparison` có toàn bộ sổ lệnh CSV + `RESULTS_GITHUB_VS_QUANT.json`.
- [Mã nguồn nghiên cứu](scripts/github_quant_compare.py).
- [Eurodollars gốc (jgardezi)](https://github.com/jgardezi/Eurodollars), license MIT. Tác giả **tự công bố** lợi nhuận khoảng +938% khi backtest 2008–2018; đây **không phải thành tích đã được độc lập xác minh**.
- Thư viện GitHub được quan tâm rộng rãi: `freqtrade/freqtrade-strategies` ~5.608 sao (cho crypto, không chứng minh có lợi nhuận trên EUR/USD). `QuantConnect/Lean` là engine backtest, không phải một chiến lược.

## Cấu hình cố định trước backtest

Dữ liệu: **104.967 nến H1 EUR/USD thực từ Dukascopy**, cache có kiểm tra checksum. Không phải nguồn dữ liệu giá khớp lệnh Exness.

Vốn mô phỏng riêng mỗi giai đoạn: 1.000 USD, lệnh đơn, max rủi ro thiết kế 0,5%/lệnh, đòn bẩy hiệu dụng <=5x, lot bước 0,01. Spread kịch bản Exness Standard 0,8 pip cố định và trượt giá 0,1 pip mỗi chiều, commission 0, **chưa tính swap**. Không có tài khoản/tiền thật.

- **Bản chuyển thể Eurodollars:** SMA H1 50/200 (ít nhất 17 nến cùng chiều), SMA daily 7/21 (ít nhất 4 ngày); Stochastic 9/9/5 vượt lên khỏi quá bán hoặc xuống khỏi quá mua; không quá 3 lệnh theo cùng xu hướng H1; TP 7 pip, SL 17 pip.
- **TSMOM định lượng:** động lượng 120 và 480 nến cùng chiều, mức độ tín hiệu chuẩn hóa >1,0, giới hạn biến động bằng tỉ số realized vol 480/1440; chỉ mở lúc 08:00 UTC, stop 2 ATR và target 3 ATR, thời gian giữ tối đa 96 giờ.

**Caveat:** Bản Eurodollars được chuyển thể để dùng chung bộ khớp lệnh và quy tắc quản lý vốn, không phải mô phỏng 1:1 hệ thống LEAN gốc. Tác giả dùng 5.000 units mỗi lệnh, còn phép thử này giới hạn rủi ro 0,5% và tối đa 5x. Có ngưỡng cắt an toàn 500 nến. Do đó kết quả **không bác bỏ** kết quả gốc, mà đo hiệu quả chính quy tắc được tái lập.

## Kết quả

| Phương án | 2010–2018 (nền) | 2019–2022 (sau khi tác giả công bố) | 2023–2026 (gần đây) | Lệnh sau 2018 |
|---|---:|---:|---:|---:|
| Eurodollars chuyển thể | -8,16% (220) | **-3,36% (116)** | **-1,32% (125)** | 241 |
| TSMOM định lượng | -2,68% (431) | **-2,29% (239)** | **-3,12% (200)** | 439 |

Phần trăm là **cả giai đoạn**, trong ngoặc là giao dịch khép kín, không phải lợi nhuận tháng. Mọi giai đoạn dùng cùng các tham số cố định. Kiểm tra riêng 2023–2026:

| Chỉ tiêu | Eurodollars chuyển thể | TSMOM |
|---|---:|---:|
| Lệnh | 125 | 200 |
| Thắng | 72,80% | 39,50% |
| Profit factor | 0,892 | 0,929 |
| Drawdown tối đa sau đóng lệnh | -3,36% | -7,25% |
| Số tháng đạt >=5% | 0 | 0 |
| Số tháng đạt >=8% | 0 | 0 |
| Spread 1,2 pip | -2,32% | -4,22% |
| Spread 2,0 pip | -4,32% | -7,24% |

**Đối chiếu sổ lệnh:** số lệnh và thứ tự thời gian được xác nhận; cho từng giao dịch, `gross - spread - slippage = net` với độ sai lệch máy tính bằng 0. Tổng giao dịch 2010–2026: 461 + 870 = 1.331 lệnh giữa hai chiến lược. **Không đủ 2.000 lệnh riêng cho một chiến lược**, không bù thêm bằng dữ liệu hoặc lệnh giả.

## Quyết định

Chưa đưa tiền thật vào giao dịch; không có chiến lược nào đạt mục tiêu sinh lợi đều 5–8%/tháng. Nghiên cứu thêm các nguồn dữ liệu Exness tick và kiểm tra độ tin cậy fill/overnight trước khi làm thêm các phép thử phức tạp. Không tăng tham số bằng cách nhìn trước kết quả giai đoạn 2023–2026.

Không nên dựa vào số sao GitHub, tỷ lệ thắng cao hoặc kết quả quảng cáo lịch sử để kết luận lợi nhuận sau phí. Backtest dùng nến H1 có hạn chế thứ tự tick intrabar (ưu tiên SL nếu cùng nến chạm TP và SL), chưa tính swap, spread động, độ trễ giao dịch hay drawdown trong khi giữ lệnh.
