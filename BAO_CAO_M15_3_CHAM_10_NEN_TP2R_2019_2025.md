# Kết quả kiểm định: M15 chỉ ba lần chạm cùng vùng, cách nhau tối đa 10 nến — TP ròng 2R

**Nghiên cứu hoàn tất ngày 30/10/2026. KẾT LUẬN: chưa có lợi thế giao dịch. Không dùng tiền thật.**

- [Quy tắc chốt trước khi nhìn kết quả](DE_CUONG_M15_3_CHAM_TOI_DA_10_NEN_2R.md)
- [GitHub Actions 7 năm 2019–2025 — tất cả công việc thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41104800811).
- Artifact: `m15-three-touch-2019` tới `m15-three-touch-2025`, mỗi tệp gồm JSON, CSV sổ lệnh và báo cáo năm.
- [Mã chiến lược chỉ M15](scripts/m15_three_touch_engulf_2r.py) · [Unit tests 3 điểm chạm](tests/test_m15_three_touch_engulf_2r.py).

## Định nghĩa ba chạm được thử

**Bỏ HOÀN TOÀN điều kiện vùng cứng H4/D1**, không lấy chỉ báo từ khung lớn. Với BUY, lần 1 và 2 là **hai đáy pivot M15 độc lập** đã được xác nhận khi nến liền sau đóng và bật lên, lần 3 là chính nến Engulfing tăng M15 quay lại cùng vùng rồi đóng đảo chiều. Với SELL, dùng hai đỉnh pivot cùng vai trò và nến Engulfing giảm. Mỗi khoảng giữa lần 1–2 và lần 2–3 được phép **tối đa 10 cây M15** (thử nghiệm đặt tối thiểu **2 cây** để không đếm hai nến sát nhau của một cú chạm thành hai cú phản ứng). Tổng ba chạm không kéo dài quá 20 nến M15.

Ba mức giá phải nằm trong vùng có nửa độ rộng `max(2 pip, 0,35 × median biên độ 40 nến M15 quan sát)`. Hai pivot đầu tiên được xác nhận bằng giá nến *đã hoàn tất* sau pivot, không bao giờ dùng pivot chưa thể biết ở thời điểm quyết định. Nến thứ ba chính là Engulfing đã đóng, không chờ nến xác nhận tương lai.

Giữ nguyên **Engulfing thân ≥2 lần thân nến ngay trước, từng râu ≤5% High−Low nến tín hiệu**, body-engulfing ngược màu, Limit tại 50% toàn nến, chỉ hiệu lực trong **nến M15 ngay kế tiếp**, SL cách râu Engulfing 1 pip, mục tiêu **TP = R:R ròng dự kiến 2,0** (trượt giá giả định 0,1 pip/chiều); vốn rủi ro thiết kế **0,5% tài khoản** mỗi lệnh, tối đa một lệnh khớp mỗi tuần trên cả bốn cặp.

Giá **M15 Dukascopy Bid/Ask thực**, không chia H1 thành bốn nến giả. Đã kiểm tra SHA-256 manifests của từng tháng. Mỗi năm bắt đầu lại với 1.000 USD mô phỏng riêng, không cộng các phần trăm thành lãi kép.

## Toàn bộ kết quả 2019–2025

| Năm | Số Engulfing mạnh M15 (4 cặp) | Đủ 3 chạm | Limit đặt | Limit khớp | Không khớp | Lãi/lỗ ròng năm | Tỷ lệ thắng (nếu có lệnh) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 511 | 16 | 15 | 3 | 12 | **+0,0365%** | 33,3% |
| 2020 | 430 | 6 | 6 | 0 | 6 | **0,0000%** | Không có lệnh |
| 2021 | 429 | 7 | 6 | 3 | 3 | **−0,5088%** | 0% |
| 2022 | 426 | 11 | 10 | 1 | 9 | **−0,2540%** | 0% |
| 2023 | 348 | 5 | 4 | 2 | 2 | **−0,4868%** | 0% |
| 2024 | 386 | 4 | 4 | 2 | 2 | **−0,4030%** | 0% |
| 2025 | 355 | 8 | 8 | 2 | 6 | **−0,3166%** | 0% |
| **Tổng** | **2.885** | **57** | **53** | **13** | **40** | — | **1 thắng / 13 lệnh** |

**Tổng số tiền hiện thực hóa của bảy tài khoản mô phỏng khởi tạo theo năm:** Gross `−18,4046 USD`; slippage mô phỏng `0,9215 USD`; **Net `−19,3261 USD`**. Đây là tổng tiền từ **bảy phép thử vốn 1.000 USD reset hàng năm**, không phải tỷ suất lãi kép chung 2019–2025.

## Kiểm toán

- Đã đọc đủ 7 JSON báo cáo và 7 CSV (riêng năm 2020 CSV rỗng vì 0 lệnh).
- Tổng **53 Limit được đặt, 13 khớp trong nến M15 tiếp theo, 40 hết hạn không khớp**.
- Tất cả 13 giao dịch có đúng 3 phản ứng theo quy tắc và thiết kế R:R ròng dự kiến **ít nhất 2,0**, lot làm tròn xuống bội 0,01; không quá 1 lệnh khớp/tuần trong từng năm.
- **12 lệnh lỗ và 1 lệnh lãi**; không có chuỗi thắng cho thấy ưu thế xác suất.
- Giá vào BUY kiểm tra theo Ask, SELL theo Bid; dừng lỗ/TP kiểm tra theo mặt giá đối ứng. Chênh lệch bid/ask nằm trong giá khớp, **không trừ spread hai lần**; trượt giá giả định 0,1 pip/chiều.
- Nến vào vừa chạm Limit và SL được tính stop trước (thận trọng). Khi thiếu tick nội nến, không thể xác nhận trình tự thực.
- Risk 0,5% là ngân sách thiết kế lúc vào; stop và chi phí thực tế vẫn có thể vượt vì gap, thị trường thiếu thanh khoản. Không có Exness swap/rollover thực, tin kinh tế hay tick level.

## Kết luận

**Không đạt tiêu chí đủ lệnh lẫn lợi nhuận dương nhiều năm; tuyệt đối không kích hoạt tiền thật.** Bộ lọc nến rất mạnh, yêu cầu ba chạm cách nhau tối đa 10 nến và Limit chỉ tồn tại 15 phút khiến lệnh được khớp cực hiếm. Ba chạm M15 **không tạo được kỳ vọng dương** trên tập giá đã kiểm định này.

Nếu muốn nghiên cứu biến thể nữa, cần định nghĩa mới trước khi mở dữ liệu kiểm tra và dùng forward/demo hoặc kỳ giá mới, tránh chỉnh tham số bằng cách nhìn kết quả cũ.
