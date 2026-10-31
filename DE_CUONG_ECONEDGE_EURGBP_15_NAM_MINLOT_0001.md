# PHÉP KIỂM ĐỊNH MỞ RỘNG EURUSD+GBPUSD — ĐĂNG KÝ TRƯỚC KẾT QUẢ

Ngày khóa: 31/10/2026. Đối tượng: áp dụng **cùng chính sách EUR/GBP mới được kiểm định 01–09/2026** lên toàn bộ quá khứ 2011–2025, 2010 warm-up.

## Tại sao đây là lần nghiên cứu khác

Backtest EconEdge 15 năm trước chọn cặp trên **4** cặp (EUR GBP AUD JPY) và chỉ khớp min **0.01 standard lot**. Kết quả mới 2026 dùng **2 cặp EUR/GBP** và giả định min **0.001 standard lot**: một chính sách khác. Không thể chuyển kết quả của nghiên cứu 4 cặp sang 2 cặp. Lần này chạy thật trên 2011–2025 theo quy tắc chính sách mới.

## Định nghĩa đã cố định

- 192 tháng H1 nguồn Dukascopy EUR/USD và GBP/USD trong 2010–2025; cả hai cặp phải có file từng tháng và SHA256 nguồn; 2010 để warm-up.
- Vào **thứ Hai 08:00 UTC**; dùng đúng 480 nến H1 hoàn thành trước thời điểm quyết định. Tính z=log-return 480 bar chia volatility 480 bar × sqrt(480), chọn cặp có |z| lớn hơn, chỉ xét |z|≥0.80. **Không** lọc riêng cặp có lợi nhuận nhìn thấy.
- Bên đảo chiều đi ngược dấu z; bên xu hướng đối chứng đi cùng dấu z trên **cùng cặp/tuần**. Không bắt buộc TP 2R. Chốt hết tuần trước hoặc tại thứ Sáu 20:00 UTC, hoặc chạm SL trước.
- SL bằng 6×median H1 High−Low của 72 nến đóng trước, tối thiểu 8 pip, nếu >70 pip thì bỏ. Entry tại Ask/Bid OPEN thực, slippage giả định 0.1pip/chiều, stop dùng H1 mid high-low ±nửa quote spread mở nến như proxy; không có tick. Không giả lập swap/carry.
- Vốn đầu **$1,000** mỗi báo cáo độc lập; rủi ro thiết kế 0.5% equity/lệnh, 5× danh nghĩa, max 1 lệnh/ISO week, hai mức bước lot **.010 (standard)** và **.001 (giả định standard equivalent)**. Kiểm tra lot không tròn sai, không chọn lọc thời điểm trả thưởng.
- Chi phí spread×2: giữ cùng entry/exit/size/stop và **trừ thêm** ½ spread mở lúc vào + ½ spread mở lúc thoát trên chính những lệnh đó.
- Nghiên cứu 2011–17, 2018–25 và 2011–25 (account compounding reset độc lập giữa các nhóm), thêm các năm 2011…2025 trên ledger **toàn kỳ 2011–25**. Không cộng PnL từ nhóm chồng nhau. Nếu muốn tổng lãi cả kỳ, dùng riêng sổ 2011–25 chạy nối tiếp không reset qua năm.
- Đủ dữ liệu theo nguồn, mỗi năm ít nhất 1 đầu tuần có dữ liệu; nếu không, fail closed.
- Bootstrap circular block 8 tuần, 2500 draw fixed seed, lấy phân vị 5%.
- Không được kết luận lợi thế trừ khi nhánh đảo chiều min .001 lot có **>=30 lệnh** trong mỗi giai đoạn 2011–17 và 2018–25, kỳ vọng net USD>0, spread×2 vẫn>0, PF>1.1, cận dưới 95% tuần>0, và tốt hơn nhánh xu hướng. Phân phối 2011–25 ghi từng năm, nếu quá lệ thuộc năm lãi cao phải coi là chứng cứ yếu.
- Bởi vì EUR/GBP được chọn **sau khi xem** phân rã 15 năm và cả 2011–2025 đã xem, **đây là kiểm tra độ nhất quán hồi cứu, KHÔNG phải out-of-sample mới**. Kết quả 2026 đã nhìn và không thể dùng làm holdout nguyên vẹn. Mọi phát hiện chỉ đi tới forward demo trên giá/swap broker mới, không có lệnh thật.

Báo cáo phải bao gồm số tuần, tín hiệu, bỏ lệnh vì >70pip, bỏ vì lot, số lệnh khớp, thắng, lãi USD và % 15 năm, PF, DD, stress spread, bootstrap, bản ledger từng lệnh, hash dữ liệu. Cả dữ liệu không đạt cũng phải công bố, không chọn kết quả đẹp.
