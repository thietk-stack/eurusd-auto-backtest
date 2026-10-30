# Kết quả đã kiểm tra lại: thân Engulfing >=2x thân trước, từng râu <=5%

**Kiểm tra ngày 30/10/2026.** GitHub Actions [run 41100790578](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41100790578) có nhật ký cho thấy **14 unit tests đạt**, nghiên cứu in đủ 8 mô hình, artifact **[12997219281](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41100790578/artifacts/12997219281)** đã xuất. Lưu ý: API GitHub vẫn trả trạng thái `queued` (không đồng bộ), nên chứng cứ hoàn tất là **log thực thi + artifact**, không phải trạng thái API.

## Định nghĩa lọc và nguồn
- Engulfing vẫn phủ thân nến trước cùng khung H1/H4, và đổi màu.
- `abs(Close-Open) >= 2*abs(Close_previous-Open_previous)` cùng timeframe.
- Râu **trên** và **dưới**, **mỗi râu** <=5% chiều dài `High-Low` nến hiện tại.
- Chỉ có một cây H1/H4 sau engulfing để khớp limit tại 50% cả nến; SL ngoài râu 1 pip; TP gộp 2R, bị chặn bởi vùng cứng đối diện; RR dự kiến sau phí >=1.5, 0.5% vốn rủi ro thiết kế.
- Bốn cặp EURUSD, GBPUSD, AUDUSD, USDJPY; bốn vùng cứng H4_same/H4_flip/D1_same/D1_flip; H1/H4 engulfing riêng.
- Dữ liệu: **49.877 nến H1 đồng thời**, lịch sử Dukascopy Bid/Ask trong năm 2018–2025; kết quả giao dịch theo **7 năm 2019–2025**, tài khoản mô phỏng $1.000 reset đầu mỗi năm.

## Nến đạt lọc *trước* khi xét vùng cứng

| Cặp | H1 | H4 |
|---|---:|---:|
| EURUSD | 138 | 37 |
| GBPUSD | 148 | 24 |
| AUDUSD | 146 | 34 |
| USDJPY | 108 | 40 |
| **Tổng** | **540** | **135** |

So với bộ lọc không có râu, mức 5% tạo thêm tín hiệu, nhưng vẫn rất ít sau khi kết hợp vùng cứng.

## Kết quả sau lọc vùng cứng + limit đúng nến tiếp theo

| Engulfing | Vùng cứng | Limit đặt 2019–25 | Lệnh thực khớp 2019–25 | Hết hạn | Năm có lãi |
|---|---|---:|---:|---:|---:|
| H1 | H4 same | 18 | **7** | 11 | 2/7 |
| H1 | H4 flip | 22 | **8** | 14 | 2/7 |
| H1 | D1 same | 15 | **5** | 10 | 1/7 |
| H1 | D1 flip | 12 | **5** | 7 | 3/7 |
| H4 | H4 same | 4 | **2** | 2 | 0/7 |
| H4 | H4 flip | 8 | **2** | 6 | 1/7 |
| H4 | D1 same | 4 | **1** | 3 | 0/7 |
| H4 | D1 flip | 3 | **0** | 3 | 0/7 |
| **Tổng các phép thử độc lập** | | **86** | **30** | **56** | — |

**Không được coi 30 lượt khớp của 8 phiên bản là 30 giao dịch độc lập trong cùng một tài khoản.** Một số tín hiệu/lệnh có thể trùng giữa các kiểu vùng.

### Lãi/lỗ ròng của H1: theo năm (% vốn khởi đầu từng năm)

| Năm | H4 same | H4 flip | D1 same | D1 flip |
|---|---:|---:|---:|---:|
| 2019 | 0% (0) | −0,29% (1) | +0,49% (1) | +0,49% (1) |
| 2020 | −0,45% (1) | 0% (0) | 0% (0) | 0% (0) |
| 2021 | +0,27% (2) | +0,70% (1) | 0% (0) | +0,68% (1) |
| 2022 | +0,36% (2) | −0,43% (1) | 0% (0) | 0% (0) |
| 2023 | −0,87% (2) | **−1,59% (4)** | −0,31% (4) | +0,06% (3) |
| 2024 | 0% (0) | 0% (0) | 0% (0) | 0% (0) |
| 2025 | 0% (0) | +0,89% (1) | 0% (0) | 0% (0) |

### Lãi/lỗ ròng của H4: theo năm

- H4/H4 same: 2020 −0,39% (1 lệnh), 2025 −0,44% (1 lệnh), còn lại không có giao dịch.
- H4/H4 flip: 2020 +0,66% (1), 2025 −0,44% (1), còn lại không có giao dịch.
- H4/D1 same: 2020 −0,48% (1), còn lại không có giao dịch.
- H4/D1 flip: không có lệnh khớp cả bảy năm.

## Kết luận

**Chưa có lợi thế thống kê đáng tin cậy**; các phép thử có 0–8 lệnh trong bảy năm, không thể xem những năm 0% vì không có lệnh là kết quả hòa vốn tốt. Không có cơ sở kỳ vọng đều 5–8% mỗi tháng. **NO-GO giao dịch tiền thật.**

Bộ dữ liệu đã được dùng trong những thử nghiệm trước; kết quả hiện tại chỉ có tính **khám phá**, không phải kiểm chứng out-of-sample còn nguyên vẹn. Dữ liệu là H1 OHLC, không cho thứ tự tick giữa limit/SL/TP; spread thực Exness và swap chưa có. Không cam kết mức lỗ thực tế bị giới hạn tuyệt đối ở 0,5R khi gap.
