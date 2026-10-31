# EconEdge — chẩn đoán hướng giá theo tuần, KHÔNG PHẢI một chiến lược giao dịch khả thi

**Ngày kiểm toán:** 31/10/2026. **Kết luận nghiên cứu chính: NO-GO.** Ghi nhận **giả thuyết hồi quy về trung bình** đáng đặt bài kiểm tra mới, **chưa chứng minh được lợi thế**.

### Nguồn và khả năng tái tạo
- [Báo cáo thực thi chiến lược xu hướng vốn $1.000 đã kiểm định](BAO_CAO_ECONEDGE_XU_HUONG_TUAN_2019_2025.md).
- [GitHub Actions chẩn đoán thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41151534226), artifact `econedge-readonly-forward-direction-diagnostic`.
- Artifact chứa **278 dòng tình huống có tín hiệu vào thứ Hai 08:00 UTC** trong `WEEKLY_ALL_CANDIDATE_SIGNALS.csv`; JSON và báo cáo Markdown đã được xuất.
- [Mã chẩn đoán không giao dịch](scripts/econedge_directional_diagnostic.py). Bốn cặp EURUSD, GBPUSD, AUDUSD, USDJPY từ giá Dukascopy H1 2018–2025 đã kiểm tra checksum. Đối chứng giá ngược hướng giao dịch cùng cặp và cùng thứ Hai.

### Câu hỏi riêng

Khi có tín hiệu động lượng 480 nến H1 trước đó `|z|>=0,80`, liệu giá **từ thứ Hai 08 tới thứ Sáu 20:00 UTC** tiếp tục xu hướng hay thường quay lại? Chỉ đo biến động và PnL theo **PIP** sau chênh lệch Bid/Ask và giả định slippage 0,1pip mỗi chiều. **Không có stop, không giới hạn 0,01 lot, không giới hạn đòn bẩy, không tính swap hay vay lãi**. Do đó phép chẩn đoán này **không phải backtest có thể triển khai** và không được dịch pip thành lợi nhuận của tài khoản $1.000.

## Kết quả cặp đối chiếu ngay tại cùng tín hiệu

| Kỳ | Tín hiệu (tuần) | Theo xu hướng: pip TB | Đánh ngược: pip TB | Ngược hướng thắng | Cận dưới bootstrap 95% ngược hướng (pip/tuần) |
|---|---:|---:|---:|---:|---:|
| 2019–2021 | 117 | −14,77 | **+12,92** | 53,85% | **−6,93** |
| 2022–2023 | 82 | −6,63 | **+4,46** | 54,88% | **−14,34** |
| 2024–2025 | 79 | −18,23 | **+16,58** | 54,43% | **−7,86** |
| **Tổng 2019–2025** | **278** | **−13,35** | **+11,47** | **54,32%** | **−1,32** |

**Phương pháp bootstrap:** circular moving-block 8 tuần, 2.500 lượt lấy mẫu, seed cố định 20261031; trình bày percentile 5% một phía. Các kỳ đã xuất hiện ở nhiều nghiên cứu trước đó; kết quả *không phải holdout còn nguyên vẹn*. Phép chẩn đoán cũng được đặt ra **sau khi thấy kết quả backtest v1**, nên chỉ có tác dụng đặt giả thuyết, không phải kiểm định xác nhận.

### Diễn giải

- Những tuần có động lượng mạnh trên bốn cặp Forex này cho thấy **dấu hiệu đảo chiều trong tuần kế tiếp**. Xu hướng bốn tuần có thể không tiếp tục ngay vào tuần sau.
- Nhưng **ở cả ba kỳ và cả tập 278 tuần, cận dưới bootstrap của hiệu quả ngược hướng vẫn âm**. Không đủ bằng chứng thống kê về lợi thế dương sau phí.
- Khi đưa lại **SL theo biến động, min lot 0,01, rủi ro thiết kế 0,5% và tối đa 5× đòn bẩy**, nhánh giao dịch ngược trong backtest chính thua lỗ ở 2019–21 (−27,32 USD) và 2024–25 (−31,65 USD), chỉ có **1 lệnh trong 2022–23** (+13,76 USD); không được coi phép dự báo pip là hệ thống giao dịch kiếm tiền.
- Độ lớn pip chưa thể so sánh trực tiếp giữa các cặp với chi phí theo USD bằng một hệ số chung; mô phỏng này chỉ kiểm tra dự báo hướng/biến động giá.

### Quyết định

**Không có chiến lược được phép giao dịch tiền thật.**

Hướng nghiên cứu mới hợp lý là xem liệu **sự kéo giá quay lại sau bốn tuần tăng/giảm mạnh** có tiếp tục xuất hiện ở **dữ liệu niêm yết mới và cấu trúc chi phí khác** hay không. Phải chốt trước thuật toán chọn lệnh, stop và kỳ kiểm tra mới. Nếu broker không hỗ trợ kích thước vị thế nhỏ hơn 0,01 lot, với vốn $1.000 và trần 0,5%/lệnh, nhiều chiến lược dừng lỗ rộng sẽ **không khả thi** dù một số chỉ báo dự báo đúng.

Nghiên cứu carry trade chỉ có thể tiếp tục sau khi có lịch sử **chênh lệch lãi suất và swap thực tế**, không chế ra lợi nhuận carry từ OHLC.
