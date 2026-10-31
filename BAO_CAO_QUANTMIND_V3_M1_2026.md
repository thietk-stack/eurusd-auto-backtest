# QuantMind FX v3 — kiểm định 9 tháng M1 2026: chưa tìm được lợi thế

**Ngày hoàn thành: 31/10/2026. Quyết định đã đăng ký: NO-GO giao dịch tiền thật.**

- [Đề cương khóa trước khi xem M1 năm 2026](DE_CUONG_QUANTMIND_V3_M1_2026.md)
- [GitHub Actions thành công: 9 tháng + 1 job tổng hợp kiểm toán](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41147517156)
- Artifact `quantmind-v3-2026-9-months-AUDITED` gồm `QUANTMIND_V3_2026_RESULTS.json`, `V3_MONTHLY_RESULTS.csv`, `confirmed_ALL_REAL_TRADES_2026.csv` và `control_ALL_REAL_TRADES_2026.csv`. Có thêm 9 artifact tháng nguồn Dukascopy.
- [Mã chiến lược](scripts/quantmind_v3_m1_confirm.py), [tests](tests/test_quantmind_v3_m1_confirm.py), [mã tập hợp bắt buộc đủ 9 tháng](scripts/aggregate_quantmind_v3_2026.py).

## Giả thuyết đăng ký trước khi có kết quả

Bốn cặp EURUSD/GBPUSD/AUDUSD/USDJPY; **1.112.964 bản ghi M1 theo cặp** trong 9 tháng 01–09/2026, dữ liệu **Dukascopy Bid và Ask THẬT** từng tháng với SHA-256. Không tạo M1 giả từ H1/M15. Tín hiệu nền là giá xuyên qua đỉnh/đáy 60 phút trước ít nhất 0,8 pip rồi đóng lại vào phạm vi ít nhất 0,1 pip, với spread không quá 1,25 lần median 120 phút và tối đa 2,5 pip.

So sánh hai chính sách độc lập:
1. **Đối chứng**: vào OPEN M1 ngay sau tín hiệu false-break/reclaim.
2. **Có nến xác nhận**: chờ nến M1 **liền sau tín hiệu đóng** đi sâu hơn vào vùng ít nhất 0,25 pip, không quay lại vượt cực trị cú phá vỡ; spread ở CLOSE nến xác nhận ≤ spread CLOSE tín hiệu và ≤1,10 × median spread 120 nến M1 trước. Vào OPEN nến M1 tiếp theo, không vào trước khi nến xác nhận đóng.

Cả hai chỉ giao dịch **thứ Ba–Năm 10:00–16:00 UTC**. Stop ngoài cực trị nến phá vỡ giả 1 pip, take-profit thiết kế **2R sau chi phí ước lượng**, rủi ro stop thiết kế ≤0,5% vốn mỗi lệnh, 5× leverage, 0,01 lot step, tối đa một lệnh/tuần **bên trong mỗi tài khoản tháng**, giữ ≤120 phút quan sát. Mỗi tháng vốn mô phỏng bắt đầu riêng **1.000 USD**, không compounding cả chín tháng.

## Kết quả từng tháng: PnL USD đã tính giá Bid/Ask và 0,1 pip trượt mỗi chiều, CHƯA có swap

| Tháng | Đối chứng không xác nhận | Có xác nhận |
|---|---:|---:|
| 01/2026 | −1,09 | −6,05 |
| 02/2026 | −0,99 | −2,37 |
| 03/2026 | −5,16 | +5,24 |
| 04/2026 | −6,58 | −5,41 |
| 05/2026 | +0,54 | −6,89 |
| 06/2026 | +2,68 | +2,96 |
| 07/2026 | −0,93 | −1,38 |
| 08/2026 | −4,77 | +0,93 |
| 09/2026 | +0,33 | +0,46 |

## Kết quả hai kỳ xác định TRƯỚC KHI CHẠY

| Phương pháp | Giai đoạn | Ứng viên đáp ứng luật | Giao dịch | Thắng | PnL USD cộng các tháng | PF | PnL sau thêm 1 spread USD | Wilson lower 95% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Đối chứng | 01–04/2026 | 795 | 18 | 2 (11,1%) | **−13,82** | 0,199 | **−16,23** | 0,037 |
| Có xác nhận | 01–04/2026 | 165 | 18 | 5 (27,8%) | **−8,59** | 0,649 | **−12,70** | 0,142 |
| Đối chứng | 05–09/2026 | 576 | 23 | 8 (34,8%) | **−2,15** | 0,889 | **−7,72** | 0,208 |
| **Có xác nhận** | **05–09/2026** | **139** | **23** | **6 (26,1%)** | **−3,92** | **0,861** | **−9,40** | **0,141** |

Tổng qua chín tài khoản tháng: phương pháp **có xác nhận 41 giao dịch, 11 thắng, PnL cộng −12,51 USD; đối chứng 41 giao dịch, 10 thắng, PnL cộng −15,97 USD**. Đây **không phải lỗ của một tài khoản $1.000 chạy liên tục trong chín tháng**, và cũng không cho phép công bố “lợi nhuận tháng” ổn định. Thử nghiệm spread x2 **giữ nguyên các giao dịch và TP/SL**, trừ thêm một lần chênh lệch giá, không được nâng TP hay thay tín hiệu để cải thiện kết quả.

## Kiểm toán sổ lệnh

- Hai sổ lệnh có **41 giao dịch mỗi chính sách**. Chính sách có xác nhận: **28 chạm SL sau phút vào, 2 chạm SL ngay trong phút vào, 9 TP +2R và 2 hết thời gian**. Chỉ có 11 giao dịch có PnL dương, không phải 11 TP +2R.
- Không giao dịch nào vượt ngân sách rủi ro stop **thiết kế** 0,5% tại lúc vào; mức sử dụng tối đa khoảng **86,1% của ngân sách 0,5%** do ràng buộc leverage/lot. Tuy nhiên gap/slippage có thể vượt mức thua dự kiến.
- Điều kiện không giao dịch thứ Hai được giữ: **36/41 giao dịch xác nhận rơi vào thứ Ba, 5/41 rơi vào thứ Tư, 0 lệnh vào thứ Năm**. Đối chứng: 39/41 thứ Ba và 2 thứ Tư. **Thiên lệch chọn giao dịch đầu tuần chưa được loại bỏ hoàn toàn**, nó chuyển từ thứ Hai sang thứ Ba! Chính sách mới đúng là “chọn tín hiệu đầu tiên của cửa sổ được phép trong tuần”, không phải kiểm định khách quan mọi phiên.
- Các phép thử **reset đầu mỗi tháng**, có **1 tuần ISO trùng giữa hai tháng trong kỳ đầu và 1 tuần trùng trong kỳ sau ở mỗi chính sách**. Quy tắc một lệnh/tuần chỉ được kiểm toán trong **mỗi tháng riêng**, không thể tuyên bố có một sổ vốn chung 2026 tuân thủ một lệnh/tuần xuyên các ranh giới tháng.
- Tính PnL dựa trên báo giá Bid/Ask M1, **không có thứ tự tick nội phút**; trường hợp nến chứa TP và SL được tính SL trước và không thưởng TP ngay phút vào. Không có phí qua đêm, spread broker Exness theo tick, độ trễ, lịch tin kinh tế hoặc sổ lệnh tập trung FX.
- Dữ liệu 2026 ở phân giải M1 mới cho chiến lược này, nhưng các năm 2026 có thể đã được xem trong thí nghiệm H1 khác: **không phải holdout nguyên vẹn cấp toàn dự án**.

## Cổng giao dịch xác định từ trước

- **01–04/2026:** >=12 lệnh, PnL sau phí >0, PF>1,1, spread x2 vẫn dương. **KHÔNG ĐẠT**: dù có 18 lệnh, lãi âm và PF 0,649.
- **05–09/2026:** >=16 lệnh, PnL >0, PF>1,1, spread x2 dương, cận dưới Wilson 95% cho p(win)>33,33%, đồng thời tốt hơn đối chứng. **KHÔNG ĐẠT**: 23 lệnh, PnL −3,92 USD, PF0,861, stress −9,40 USD, Wilson 0,141, **tệ hơn đối chứng −2,15 USD**.

**Kết luận: KHÔNG TÌM ĐƯỢC LỢI THẾ CÓ THỂ XÁC NHẬN QUA VÒNG NÀY. NO-GO real money.**

### Bài học và hướng tiếp theo

1. Giới hạn một lệnh mỗi tuần bằng “tín hiệu đầu tiên” dẫn đến thiên lệch mạnh vào đầu cửa sổ giao dịch. Không được coi thay thứ Hai bằng thứ Ba là đã giải quyết được.
2. Nếu muốn nghiên cứu tiếp, **gắn nhãn toàn bộ ứng viên** và đánh giá hiệu quả theo nhóm ngày/phiên cố định, lấy mẫu khối theo tuần, gộp khoảng nhãn trùng, và cho chính sách chọn sự kiện được **xác định trước khi nhìn kết quả**. Không thể coi hàng nghìn ứng viên chồng lấn như hàng nghìn lệnh độc lập.
3. Sử dụng **dữ liệu tick thật + forward demo tương lai** cho bài kiểm tra hoàn toàn mới. Không tiếp tục sửa ngưỡng 0,25 pip, spread 1,10× trên chính dữ liệu 2026 vừa xem rồi công bố một edge.
4. Khi xét nghiên cứu nhiều quy tắc, cần điều chỉnh data-snooping; tham khảo [White et al. (1998) Data-Snooping, Technical Trading Rule Performance and the Bootstrap](https://cepr.org/publications/dp1976) và phương pháp purged/embargo cross-validation cho các nhãn có khoảng thời gian chồng lấn.

**Không có kết nối broker thực và không phát lệnh.**
