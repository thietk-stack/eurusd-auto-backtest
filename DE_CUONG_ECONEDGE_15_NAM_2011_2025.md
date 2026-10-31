# Khóa trước kiểm định: EconEdge FX Long Horizon (2011–2025)

**Chốt ngày 31/10/2026, trước khi xem dữ liệu mở rộng 2010–2017.** Tất cả nghiên cứu chỉ sử dụng giá lịch sử, không đặt lệnh broker.

**Mục đích:** Bản thử nghiệm trước (2019–2025) có dấu hiệu hồi quy về trung bình tuần sau xu hướng mạnh bốn tuần, nhưng cận dưới bootstrap 95% vẫn âm. Không được tuyên bố đã tìm được lợi thế. Phép thử này kiểm tra **tính bền vững qua chu kỳ dài hơn**, tuyệt đối không chỉnh lại các thông số sau khi nhìn dữ liệu trước 2018.

**Cửa sổ và nguồn:**
- Dukascopy **H1 BID/ASK có SHA-256 từng tháng**, EURUSD, GBPUSD, AUDUSD, USDJPY.
- **2010 warmup**; 2011–2017 là giai đoạn lịch sử **mới bổ sung** (không phải forward out-of-sample); 2018–2025 đã được xem qua nhiều thí nghiệm trước. Tất cả giá H1 thật, không fill giả giờ thiếu. Phải có đủ **192 tháng 2010–2025 × 4 cặp**, nếu không báo thiếu nguồn và KHÔNG công bố hiệu quả đầy đủ.
- 2011–2025 có 15 năm giao dịch, bao gồm các trạng thái tiền tệ 2011–2017, 2018–2021, 2022–2025. Mỗi nhóm phân kỳ bắt đầu tài khoản 1.000 USD **RIÊNG**; tổng hợp đầy đủ 15 năm có một tài khoản khác giả định chạy nối tiếp theo điều kiện giao dịch gốc.

**Quy tắc tín hiệu KHÔNG THAY ĐỔI từ EconEdge trước:**
1. Chỉ chọn mốc **thứ Hai 08:00 UTC**; dữ liệu tín hiệu là 480 nến H1 **đã đóng trước điểm vào**.
2. Tính điểm động lượng 480 nến H1 theo cách đã cố định (log-return 480 nến / độ lệch chuẩn returns nhân căn 480), chọn một cặp có trị tuyệt đối điểm lớn nhất, yêu cầu **|z|≥0,8**.
3. **Nhánh đảo chiều (reversal)**: giao dịch NGƯỢC dấu xu hướng đã hình thành. **Nhánh thuận xu hướng (trend control)**: đi THEO dấu điểm z trên cùng cặp và cùng thời điểm. Đây là hai chính sách song song kiểm chứng, không giả vờ có dữ liệu order flow.
4. **Chẩn đoán hướng giá toàn bộ sự kiện**: giả định vào Open H1 thứ Hai theo Bid/Ask thật, giữ đến **thứ Sáu 20:00 UTC** và tính pip sau spread/slippage 0,1 pip mỗi chiều. Báo cáo một cách riêng biệt và **KHÔNG gọi đó là lợi nhuận trên vốn 1.000 USD**, vì không áp dụng Stop Loss, lot, rủi ro.
5. **Thử khả thi thực thi**: mỗi nhánh chỉ tối đa 1 lệnh/tuần, stop cách entry **6× trung vị biên độ H1 của 72 nến đã đóng**, ít nhất 8 pip; nếu quá 70 pip thì hủy; TP không cố định, thoát khi stop hoặc thứ Sáu 20:00 UTC. Giá vào BUY Ask+0,1pip, SELL Bid−0,1pip; phí spread có trong quote, slippage bổ sung 0,1pip phía thoát. Giá Bid/Ask ở CLOSE không có trong file H1 nên nếu cần dùng **mid Close ±0,5×spread open** và ghi rõ xấp xỉ. Spread ×2 trừ thêm ½ spread entry + ½ spread exit khỏi **chính các giao dịch đó**, không dời SL, không sửa tín hiệu. Rủi ro thiết kế ≤0,5% equity/lệnh, tối thiểu/bước 0,01 lot và ≤5× leverage; bỏ giao dịch không thể định cỡ vốn. **Chưa có phí swap/overnight**, nên nếu có lãi vẫn chưa được gọi là lợi nhuận broker thực.
6. Stop-first khi biết High/Low nến chạm cả mức stop và hướng ra lời; không thể dựng lại tick nội nến. Không được khẳng định giới hạn tuyệt đối mức mất vốn ở 0,5% khi gap.

**Báo cáo bắt buộc:** mỗi năm 2011–2025 số tuần, số tín hiệu, pip trung bình đảo chiều / thuận xu hướng, hiệu ứng trừ chi phí, tỷ lệ tuần đúng, bootstrap theo **cụm 8 tuần và 2.500 lần lấy mẫu** (cận dưới 95%), cặp đóng góp, nhánh có thể đặt giao dịch thật số lệnh đã vào, tỷ lệ hủy vì stop/lot, PnL USD, PF và drawdown. Các nhóm được ghi riêng (2011–14, 2015–17, 2018–21, 2022–25). Không kết luận hiệu quả nếu nhóm mới 2011–17 không có ít nhất 100 tín hiệu và không có cận dưới bootstrap dương.

**Cổng “tạm có bằng chứng”:** giả thuyết đảo chiều phải có trung bình sau chi phí >0 trong **cả giai đoạn mới 2011–17 lẫn giai đoạn 2018–25**, cận dưới bootstrap 95% (8 tuần) >0 trên cả hai nhóm và số tín hiệu >=100 mỗi nhóm. Khi phân kỳ 2011–14/2015–17/2018–21/2022–25, cần ít nhất 3/4 phân kỳ dương; báo cáo thời kỳ nào không đạt. **Nếu không: NO-GO** cho nhận định hướng giá đáng tin. Để gọi là hệ thống giao dịch còn cần tài khoản mô phỏng dương sau chi phí và stress x2, đủ số lệnh ≥30 trên nhóm mới, PF>1,1, cận dưới bootstrap trên lợi nhuận tuần sau sizing >0 và kiểm chứng swap + forward demo. Không được chọn lại ngưỡng dựa vào kỳ nào có lãi.

Tài liệu phản biện: Raza, Marshall & Visaltanachoti, 2014, *Is there momentum or reversal in weekly currency returns?*, Journal of International Money and Finance, 45:38–60. Trong tập 63 đồng tiền, nghiên cứu họ thấy xu hướng ngắn hạn cross-sectional hơn là đảo chiều; giả thuyết của chúng ta là time-series reversal trên chỉ bốn cặp USD và **có thể khác hoặc là nhiễu mẫu**. https://doi.org/10.1016/j.jimonfin.2014.02.009

Không cấp phép giao dịch vốn thật dựa trên việc kéo dài dữ liệu về quá khứ.
