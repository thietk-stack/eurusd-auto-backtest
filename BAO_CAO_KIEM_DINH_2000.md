# Báo cáo backtest EUR/USD thực tế — 30/10/2026

**Nguồn kiểm chứng:** [GitHub Actions run #3](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41083461646) — `success`; tải báo cáo và sổ giao dịch tại artifact `eurusd-report`.

## Dữ liệu & phương pháp

- Nguồn giá: EUR/USD lịch sử H1 Bid/Ask tải qua thư viện `dukascopy-node` từ Dukascopy; **không phải dữ liệu giao dịch thực tế Exness**.
- Tổng nến hợp lệ: **104.967**; 202 tệp/tháng đã tải và lưu checksum/cache.
- Kiểm định ngoài mẫu: từ 01/01/2015 tới 29/10/2026.
- Chiến lược: Donchian breakout 18, ATR14, SL 1,9 ATR, TP 2,8 ATR, thời gian nắm tối đa 48 giờ, vào lệnh dựa trên nến đã đóng.
- Vốn ban đầu: **1.000 USD**; rủi ro thiết kế mỗi lệnh 0,5% vốn, đòn bẩy hiệu dụng tối đa 5 lần; lot 0,01. Không có lệnh giao dịch thật.
- Chi phí giả định Exness Standard: spread **0,8 pip cố định**, trượt giá **0,1 pip mỗi chiều**, hoa hồng **0**, swap **giả định 0**; không phản ánh spread thực thay đổi hoặc điều kiện thực thi riêng của tài khoản.
- Kronos AI **chưa chạy**. Đây là chiến lược kỹ thuật đối chứng.

## Chính xác 2.000 giao dịch đầu tiên (không chọn lọc theo lợi nhuận)

Khoảng giao dịch 02/01/2015 – 24/08/2022, lấy theo thứ tự thời gian.

| Chỉ tiêu | Giá trị |
|---|---:|
| Số giao dịch khép kín | 2.000 |
| Tỷ lệ thắng | 41,05% |
| Profit factor | 1,00049 |
| Lãi/lỗ trước phí mô hình | +310,19 USD |
| Spread | −246,40 USD |
| Trượt giá | −61,60 USD |
| Lãi/lỗ **sau chi phí** | **+2,19 USD (+0,22%)** |
| Vốn còn lại | 1.002,19 USD |
| Drawdown tối đa theo vốn sau đóng lệnh | −17,90% |
| Lãi kép bình quân tháng | ~0,0024% |

## Toàn bộ kiểm định H1 ngoài mẫu (không dừng ở 2.000)

| Spread giả định | Lệnh khép kín | Lãi/lỗ vốn | Vốn cuối kỳ | Drawdown tối đa |
|---|---:|---:|---:|---:|
| 0,8 pip | 3.113 | −29,28% | 707,20 USD | −41,10% |
| 1,2 pip | 3.065 | −32,18% | 678,25 USD | −40,57% |
| 2,0 pip | 2.757 | −47,73% | 522,75 USD | −51,29% |

Với spread 0,8 pip, trong **142 tháng có lệnh đóng**, 65 tháng lãi và 77 tháng lỗ. Mức lợi suất tháng cao nhất là **+5,29%**, thấp nhất **−6,62%**, theo phương pháp lãi/lỗ đã thực hiện. **0 tháng đạt mục tiêu +8%.**

Ở riêng 2.000 lệnh đầu, spread 1,2 pip cho −6,33% và 2,0 pip cho −28,29%; hiệu quả rất nhạy với chi phí khớp lệnh.

## Kết luận độc lập

Không tìm được bằng chứng chiến lược Donchian 18 đạt lợi thế duy trì >=8%/tháng trên dữ liệu đã kiểm định. Kết quả 2.000 lệnh đầu gần như hòa vốn, nhưng kéo dài giai đoạn kiểm định chuyển thành lỗ đáng kể.

**Không khuyến nghị dùng tiền thật**. Cần kiểm định walk-forward độc lập, dữ liệu tick và chênh lệch giá thực tế từ Exness, điều kiện swap và khả năng thực thi; tiếp theo mới so sánh chiến lược sử dụng Kronos AI với baseline cố định. Kịch bản stress là mô phỏng thay đổi spread, không chứng minh hiệu quả giao dịch.

Nguồn đầy đủ: artifact CSV và RESULTS.json của [run #3](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41083461646). Nếu artifact hết hạn, GitHub Actions có thể chạy lại, nhưng kết quả có thể thay đổi nếu nhà cung cấp sửa dữ liệu lịch sử.
