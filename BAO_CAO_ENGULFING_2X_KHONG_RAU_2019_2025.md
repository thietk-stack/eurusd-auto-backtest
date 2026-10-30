# Backtest 2019–2025: Engulfing >=2x nến trước, KHÔNG RÂU

**Kết luận:** Chỉ 5 nến đạt lọc, 1 lệnh LIMIT được đặt, **0 lệnh thực sự khớp**; mẫu quá ít để chứng minh chiến lược có lợi nhuận.

**Nguồn chạy thực:** [GitHub Actions kết quả](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41099890038), artifact strict-engulf-2x-no-wicks-2019-2025 (RESULTS_2X_NO_WICK.json, các sổ CSV và báo cáo chương trình). [Mã bộ lọc](scripts/htf_engulf_2x_no_wick.py) · [Kiểm thử](tests/test_htf_engulf_2x_no_wick.py).

## Định nghĩa bộ lọc

Dùng dữ liệu H1 Dukascopy đã tải kiểm tra checksum, H4 dựng từ bốn H1 có giá thực. Chỉ tính Engulfing khi có đủ:
- Biên độ **toàn bộ nến** (High − Low) >= **2x biên độ toàn bộ nến trước** trên cùng khung H1 hoặc H4.
- Bullish: Open = Low, Close = High. Bearish: Open = High, Close = Low. Cho phép sai số số học <= 1e−8 đơn vị giá; không tự đổi thành "râu ngắn".
- Nến phải là body-engulfing thật và ở vùng hỗ trợ/kháng cự H4/D1 đã xác nhận ít nhất 4 phản ứng giá.
- LIMIT = giữa High–Low nến tín hiệu, **chỉ tồn tại đúng cây nến cùng khung kế tiếp**. BUY SL = Low nến −1 pip; SELL SL = High nến +1 pip. TP ban đầu 2R, chặn trước vùng đối diện đã biết; R:R sau phí >=1,5, ngân sách stop + phí 0,5% equity, tối đa một giao dịch khớp mỗi tuần trên cả 4 cặp.

Tất cả quy tắc khác giữ nguyên so với [lượt nghiên cứu trước](BAO_CAO_H1_H4_ENGULFING_LIMIT_1_NEN.md).

## Trước khi yêu cầu ở vùng giá cứng

| Cặp tiền | Engulfing H1 cũ | H1 đạt lọc | Engulfing H4 cũ | H4 đạt lọc |
|---|---:|---:|---:|---:|
| EURUSD | 6.414 | **2** | 1.543 | **0** |
| GBPUSD | 6.603 | **1** | 1.618 | **0** |
| AUDUSD | 6.780 | **0** | 1.633 | **0** |
| USDJPY | 6.782 | **0** | 1.631 | **2** |
| **Tổng** | **26.579** | **3** | **6.425** | **2** |

Tổng 49.877 nến H1 có dữ liệu đồng thời trên bốn cặp trong 2018–2025, gồm năm 2018 dùng làm dữ liệu hình thành vùng giá.

## Thống kê từng năm về các nến đạt bộ lọc

| Năm | EURUSD H1 | GBPUSD H1 | USDJPY H4 | Tổng |
|---|---:|---:|---:|---:|
| 2019 | 1 | 0 | 1 | 2 |
| 2020 | 0 | 1 | 0 | 1 |
| 2021 | 0 | 0 | 0 | 0 |
| 2022 | 0 | 0 | 0 | 0 |
| 2023 | 0 | 0 | 0 | 0 |
| 2024 | 1 | 0 | 1 | 2 |
| 2025 | 0 | 0 | 0 | 0 |

## Kết quả khớp LIMIT

Đã chạy 8 cấu hình (Engulfing H1/H4 × vùng H4/D1 cùng vai hoặc đổi vai) cho 7 năm 2019–2025. Chỉ có **1 LIMIT được đặt** ở cấu hình **Engulfing H4 + vùng D1 đổi vai năm 2024**; lệnh này không khớp trong H4 kế tiếp, nên bị hủy. Tất cả cấu hình đều **0 lệnh đã khớp**.

Do không có giao dịch, **không thể tính win rate, profit factor hay kỳ vọng lợi nhuận**. Số liệu 0% ở file tính toán chỉ có nghĩa **không phát sinh giao dịch**, không có nghĩa chiến lược đã được chứng minh hòa vốn hoặc an toàn.

## Nhận định

Điều kiện đồng thời 2x toàn nến và tuyệt đối không râu là **quá khắt khe** trên giá Forex H1/H4. Dữ liệu không chứng minh được mục tiêu lợi nhuận 5–8% mỗi tháng. Rủi ro thực tế vẫn tồn tại nếu có lệnh: stop 0,5% thiết kế không bảo đảm trước gap/slippage; dữ liệu nến H1 không đủ tái dựng trình tự tick; không có lịch sử Exness swap và khớp lệnh.

Không tự thay đổi điều kiện đã yêu cầu. Nếu thử biến thể khác, nên đăng ký trước và nêu rõ ngưỡng, ví dụ "thân engulfing >=2x thân nến trước, mỗi râu <=5% chiều cao nến", nhưng đó sẽ là một chiến lược khác và phải được kiểm định mới.
