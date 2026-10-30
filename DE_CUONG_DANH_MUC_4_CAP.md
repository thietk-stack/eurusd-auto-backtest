# Đề cương cố định trước khi xem kết quả: danh mục Forex 4 cặp

Ngày đóng băng phương pháp: 30/10/2026. Mã chiến lược và workflow đã được commit trước khi chạy báo cáo.

## Giả thuyết

Nguồn giá: Dukascopy lịch sử H1 Bid/Ask cho EURUSD, GBPUSD, AUDUSD và USDJPY. Đã có dữ liệu EURUSD trong cache; tải riêng 3 cặp còn lại từ 2020 đến 30/10/2026, mỗi tháng ghi checksum. Không tạo hay bù nến giả khi thiếu.

1. **Time-series momentum**: cùng dấu xu hướng 480/1440 nến H1, phân bổ nghịch biến động thực tế 480 nến, trọng số tối đa 55% một cặp, tổng gross tối đa 150%; mục tiêu mỗi leg ~8% annual volatility chia sqrt(số cặp hoạt động).
2. **Cross-sectional momentum**: xếp hạng 60 ngày sức mạnh ngoại tệ so với USD, mua mạnh nhất và bán yếu nhất; USDJPY đảo dấu tín hiệu để đại diện JPY.
3. **Equal-weight baseline**: mua đều bốn cặp, mỗi cặp 25% vốn danh nghĩa, đối chứng chứ không coi là danh mục trung hòa USD.

Vào vị thế mỗi thứ Hai 08:00 UTC với **tín hiệu lấy từ nến đã đóng trước giờ mở**; giữ đến thứ Hai tuần sau. Không sử dụng giá tương lai, không giao dịch thật.

## Kiểm định và tiêu chuẩn quyết định

- Dữ liệu từ 2020; 2020 chỉ tạo lịch sử chỉ báo.
- Validation **01/01/2021 – 31/12/2022**, rồi kiểm định cuối **01/01/2023 – 29/10/2026**.
- Chỉ chọn phương án nếu validation lợi nhuận sau phí dương, drawdown theo equity tuần >=-15% và >=70 tuần đủ dữ liệu. So sánh theo lợi nhuận validation, không nhìn trước holdout.
- Sau đó chỉ công nhận có dấu hiệu lợi thế nếu holdout lãi sau phí, drawdown >=-15%, kết quả dương cả khi *spread stress x2*. Dù vượt qua cũng CHƯA giao dịch tiền thật.
- Lưu sổ tái cân bằng, vị thế từng cặp, gross/chi phí/net, vốn cuối, drawdown và số tháng >=5/8%.
- Không tối ưu tham số sau khi nhìn kết quả holdout.

## Phí và rủi ro còn thiếu

Giá mua bán Bid/Ask quan sát từ Dukascopy ở thời điểm tái cân bằng, đối chiếu với kịch bản phí Exness Standard *giả định* (0,8/1,2/1,5/1,1 pip theo EUR/GBP/AUD/USDJPY), trượt giá 0,1 pip mỗi lần điều chỉnh vị thế, và kịch bản spread x2. **Những mức này KHÔNG được xác nhận là spread quá khứ của Exness.**

Chưa có chuỗi lãi suất/rollover lịch sử của Exness để tính carry/swap; **không coi nghiên cứu này là chiến lược carry**, không tự chế lãi suất. Chưa có mark-to-market trong tuần để tính DD intraday; tính dựa trên số dư/giá đầu tuần. Chưa có mô hình margin call/tin tức/tick spread động Exness. Chỉ để tìm giả thuyết đáng kiểm chứng, không chứng minh có thể kiếm 5–8%/tháng.

Tài liệu nền: https://www.bis.org/publications/working-paper-366-currency-momentum-strategies ; https://www.annualreviews.org/content/journals/10.1146/annurev-financial-102710-144913
