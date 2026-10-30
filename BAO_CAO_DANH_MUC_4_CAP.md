# BÁO CÁO ĐỊNH LƯỢNG 4 CẶP FOREX — 30/10/2026

## Kết luận

**Chưa phát hiện lợi thế giao dịch bền vững, không đạt mục tiêu 5–8% mỗi tháng, không được đưa vào giao dịch thật.**

[Đề cương nghiên cứu được đóng băng trước kết quả](DE_CUONG_DANH_MUC_4_CAP.md) · [Lượt GitHub Actions hoàn tất thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41088543737) · Artifact: `fx4-quant-portfolio-results` (RESULTS_PORTFOLIO.json và 18 sổ tái cân bằng).

## Tính xác thực dữ liệu

- **Nguồn giá:** Dukascopy EUR/USD, GBP/USD, AUD/USD, USD/JPY H1 Bid/Ask, tải qua `dukascopy-node`. Không phải dữ liệu môi giới Exness.
- Đã tải, kiểm tra SHA-256, lưu tiến độ **246/246 tháng** cho ba cặp mới; thêm EUR/USD lịch sử đã lưu sẵn.
- **42.589 nến H1 đồng thời** của cả bốn cặp; **341 phiên tái cân bằng tuần** trước khi chia hai giai đoạn.
- Thời kỳ xác nhận: 2021–2022, 103 tuần; thời kỳ kiểm định cuối: 2023–29/10/2026, 197 tuần.
- Dựa trên giá nến đã hoàn tất trước 08:00 UTC thứ Hai; mở vị thế tại giá mở lúc 08:00, đánh dấu lãi lỗ theo giá mở tuần kế tiếp. Không dùng dữ liệu tương lai.
- Bắt đầu riêng từng kỳ với **1.000 USD**, dùng một sổ vốn danh mục duy nhất. Không phải 4 tài khoản mỗi tài khoản 1.000 USD.

## Ba cấu hình so sánh đã chốt trước kiểm định

1. **TSMOM:** xu hướng cùng dấu ở 480 và 1.440 nến, phân bổ nghịch biến động, giới hạn 55% vị thế/cặp, gross exposure tối đa 150%.
2. **Cross-sectional:** mua ngoại tệ có sức mạnh giá lớn nhất và bán ngoại tệ yếu nhất trong 60 ngày. Với JPY, đảo dấu USDJPY để đo sự mạnh lên của đồng yên.
3. **Equal-weight benchmark:** 25% mỗi cặp theo chiều mua định sẵn; chỉ để đối chứng, không tự động trung hòa rủi ro USD.

Phí nghiên cứu giả định kiểu Exness Standard (EURUSD 0,8 pip; GBPUSD 1,2 pip; AUDUSD 1,5 pip; USDJPY 1,1 pip, **không phải dữ liệu Exness lịch sử được xác nhận**), cộng trượt giá 0,1 pip trên mỗi chiều tái cân bằng. Có đối chiếu spread Bid/Ask quan sát Dukascopy và trường hợp nhân đôi spread.

**Chưa tính swap/rollover/carry**, chưa có chuỗi lãi suất lịch sử được kiểm toán, do đó đây **không phải backtest chiến lược carry**.

## Kết quả chính: mức spread kiểu Exness giả định

| Phương án | Validation 2021–22 | Holdout 2023–26 | Drawdown tuần ở holdout | Phí holdout | Tháng 8% trong holdout |
|---|---:|---:|---:|---:|---:|
| TSMOM theo xu hướng và phân bổ biến động | +10,87% | **−4,54%** | −8,94% | 9,45 USD | 0 |
| Xếp hạng sức mạnh tiền tệ | −0,86% | **−4,00%** | −10,75% | 5,77 USD | 0 |
| Đối chứng 25% mỗi cặp | −3,62% | **+9,48%** | −5,77% | 0,07 USD | 0 |

TSMOM được **chọn chỉ từ validation 2021–2022**, vì có lợi nhuận dương và drawdown >=−15%. Nhưng TSMOM **không vượt qua holdout 2023–2026**; trong kỳ này lãi gộp trước phí là −36,00 USD, chi phí 9,45 USD và lỗ ròng −45,44 USD. **Không được chọn đối chứng sau khi nhìn thấy +9,48% ở giai đoạn cuối** — nó đã lỗ ở giai đoạn xác nhận.

### Độ nhạy phí trên holdout 2023–2026

| Phương án | Spread Dukascopy quan sát | Spread tham chiếu kiểu Exness | Spread Exness giả định x2 |
|---|---:|---:|---:|
| TSMOM | −4,21% | −4,54% | −5,32% |
| Cross-sectional | −3,84% | −4,00% | −4,49% |
| Equal-weight | +9,45% | +9,48% | +9,47% |

Tổng hợp kết quả từ `RESULTS_PORTFOLIO.json` trong artifact GitHub. Đối chiếu sổ tái cân bằng: **gross − cost = net**, số dư liên kết xuyên các tuần, sai số số học nhỏ hơn 10^−10 USD. Không tự tạo lệnh hoặc nến để đạt mục tiêu.

## Các hạn chế còn lại

- Carry chưa được kiểm định: thiếu chênh lệch lãi suất/giá forward/swap lịch sử đúng với từng loại tài khoản Exness.
- Không tính phí tài trợ vị thế, margin call hoặc độ trễ môi giới. Những khoản này có thể làm hiệu quả **xấu hơn**.
- Drawdown được đo từ giá đánh dấu **mỗi tuần**, chưa phải drawdown trong ngày hoặc trong tuần.
- Các cặp tiền đều có USD, nên đa dạng hóa theo số mã không đồng nghĩa độc lập rủi ro; cần kiểm tra tương quan.
- Với những chiến lược được nhìn thấy trên 2023–2026, mọi phép chỉnh tham số mới cần có dữ liệu kỳ sau hoặc tập riêng trước khi được xem là ngoài mẫu.

## Quyết định và hướng nghiên cứu

**NO-GO** đối với việc cấp vốn thật: không chiến lược nào đạt chuẩn kiểm định cuối, không có căn cứ kỳ vọng 5–8% đều mỗi tháng.

Bước nghiên cứu khoa học tiếp theo, nếu còn muốn kiểm chứng là **carry + momentum có tài trợ** từ chuỗi lãi suất/FX forward lịch sử đáng tin cậy, đa dạng hóa rủi ro theo các đồng tiền và forward/paper trading. Không tái tối ưu trực tiếp theo tập 2023–2026 đã công bố.

Mã chạy và kết quả đều trên [repository GitHub](https://github.com/thietk-stack/eurusd-auto-backtest). Không có lệnh thật, không có API key Exness, không tự động chuyển tiền.
