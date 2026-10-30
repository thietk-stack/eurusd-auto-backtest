# Kiểm định price action vùng hỗ trợ/kháng cự cứng >=4 lần chạm

**Ngày:** 30/10/2026. **Kết luận: CHƯA tìm thấy lợi thế sinh lời đủ ổn định. Không dùng tiền thật.**

- [Đề cương đã chốt trước khi có kết quả](DE_CUONG_PRICE_ACTION_VUNG_CUNG.md)
- [GitHub Actions run #1 thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41092879699)
- Artifact `hard-4-touch-price-action`: `RESULTS_PRICE_ACTION.json`, báo cáo và 8 CSV sổ lệnh/kịch bản chi phí.
- [Mã nguồn chiến lược](scripts/price_action_hard_zones.py)

## Quy tắc

1. **Vùng cứng đồng vai:** ít nhất 4 phản ứng support (pivot đáy) HOẶC 4 phản ứng resistance (pivot đỉnh) nằm gần nhau.
2. **Vùng cứng đổi vai:** ít nhất 4 phản ứng xoay chiều tại cùng vùng; trong đó có cả hỗ trợ và kháng cự, đã xuất hiện đổi vai theo trình tự thời gian.

Chỉ dùng hành động giá: xác nhận pivot bằng 3 nến mỗi phía, biên độ phản ứng tối thiểu dựa trên biên độ nến lịch sử, mỗi phản ứng cách nhau tối thiểu 24 nến H1. Không dùng RSI, EMA, ATR, volume, machine learning.

**Chi tiết độ rộng:** vùng có bán kính `max(6 pip, 0.75 × median biên độ 240 nến H1 trước)`. Khoảng lịch sử xét điểm chạm là 4.320 **nến H1 quan sát được**, không phải 180 ngày lịch liên tục; vùng mới được dùng trong 2.160 nến H1 quan sát sau xác nhận. Một pivot chỉ được dùng sau 3 nến xác nhận, nên không dựa vào đỉnh/đáy chưa biết ở thời điểm giao dịch.

Vào tại giá mở nến H1 tiếp theo khi cây nến vừa đóng từ chối vùng giá (hình nến đảo chiều hoặc đảo chiều phá biên nến trước). Stop đặt ngoài mép vùng với đệm tối thiểu 1,5 pip; target cách điểm vào khoảng 2 lần stop. Bỏ qua nếu vùng cứng đối diện đã tồn tại nằm giữa entry–target. Bắt buộc **R:R dự kiến sau chi phí >=1,5**, thiết kế **0,5R = 0,5% vốn hiện tại** và giới hạn đòn bẩy 5x; chung 1 tài khoản 1.000 USD trên bốn cặp EURUSD, GBPUSD, AUDUSD, USDJPY, tối đa **1 lệnh mỗi tuần**; không ép tuần nào cũng có giao dịch.

## Kết quả độc lập

**Dữ liệu:** 42.589 nến H1 được đối chiếu đồng thời giữa 4 cặp, giá Bid/Ask lịch sử thật nguồn Dukascopy. Không phải dữ liệu Exness. Chênh lệch Bid/Ask lịch sử dùng để tính phí, cộng giả định trượt 0,1 pip mỗi chiều, **không tính swap**.

| Phương pháp | Giai đoạn | Lệnh | Lãi/lỗ ròng | Win rate | PF | Drawdown đóng lệnh | Spread ×2 | Tháng đạt >=5% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 4 lần cùng vai | 2021–2022 | 61 | **−1,06%** | 34,43% | 0,929 | −2,53% | −1,23% | 0 |
| 4 lần cùng vai | 2023–2026 | 101 | **−2,77%** | 33,66% | 0,891 | −5,45% | −4,54% | 0 |
| 4 lần đổi vai | 2021–2022 | 71 | **+2,58%** | 38,03% | 1,152 | −3,24% | +3,34% | 0 |
| 4 lần đổi vai | 2023–2026 | 113 | **−4,71%** | 30,97% | 0,838 | −8,37% | −6,16% | 0 |

Những phần trăm này là **cho cả giai đoạn nhiều năm**, không phải theo tháng. Vốn thử nghiệm 1.000 USD được thiết lập độc lập ở mỗi giai đoạn và phương pháp.

### Kiểm toán điều kiện cứng từ CSV

- Số điểm chạm trong lệnh thực tế: **ít nhất 4** với cả hai kiểu vùng.
- R:R dự kiến sau chi phí nhỏ nhất: **1,786 / 1,785** (validation cùng/đổi vai); **1,762 / 1,777** (holdout cùng/đổi vai). Không có lệnh nào dưới 1,5.
- Tối đa **1 entry trong cùng một tuần ISO** trên toàn danh mục; không bù lệnh.
- Rủi ro dự kiến lúc vào **không vượt 0,5% số dư** theo sổ lệnh; có lệnh thực tế bị thua nhiều hơn số tiền rủi ro dự kiến do gap/giả định khớp nến/chi phí.
- Kiểm toán sổ lệnh: `gross − transaction cost = net` với sai số < 2×10^-15 USD; số dư sau lệnh nối đúng từ vốn đầu 1.000 USD.
- Phương án **4 lần đổi vai** đạt bộ lọc chọn trên 2021–2022 (71 lệnh, +2,58%, PF 1,152, DD −3,24%), nhưng **thất bại** khi mở rộng sang 2023–2026 (−4,71%, PF 0,838). Không được điều chỉnh tham số sau khi nhìn kết quả mới này rồi gọi lại là ngoài mẫu.

### Cách diễn giải

Số lần chạm nhiều tạo ấn tượng có vùng hỗ trợ/kháng cự mạnh, nhưng **chưa đủ chứng minh lệnh đảo chiều có kỳ vọng dương**. Vùng đã thử trên H1, ưu tiên dừng lỗ nếu trong cùng nến chạm cả SL/TP (thận trọng), nhưng không có tick để khẳng định trình tự giá. Mức sụt giảm chỉ đo sau khi đóng lệnh, chưa tính biến động trong khi giữ lệnh. Phí thực thi Exness, swap, tin tức, thanh khoản và chênh lệch spread thực tế tại thời điểm chạm stop/TP chưa được xác minh.

**Quyết định: NO-GO giao dịch tiền thật.** Nếu muốn nghiên cứu tiếp, chỉ nên đưa ra một giả thuyết trước khi thu thập dữ liệu mới/chạy forward demo, ví dụ so sánh chất lượng phản ứng vùng ở H4 và D1; không tái chỉnh bộ tham số theo lợi nhuận 2023–2026 đã xem.
