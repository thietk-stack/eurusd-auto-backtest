# QuantMind FX v3: nến M1 xác nhận phá vỡ giả và kiểm soát thiên lệch đầu tuần

**Quy tắc khóa ngày 31/10/2026 trước khi xem bất kỳ kết quả M1 năm 2026 của v3.** Đây là giả thuyết mới, **không có lệnh thực** và không phải lời hứa rằng có một lợi thế chưa ai phát hiện.

## Lý do thử v3

QuantMind v2 thất bại validation 2023 và 2024–25: trong giai đoạn về sau chỉ có 8/35 giao dịch đảo chiều thắng, tổng −15,16 USD trên 7 tài khoản tháng vốn giả định 1.000 USD riêng biệt, spread stress tăng lỗ lên −23,04 USD. Trong 74 lệnh v2, 67 rơi vào thứ Hai, chủ yếu vì chọn giao dịch đầu tiên mỗi tuần. V3 **không sửa lại kết quả v2**, mà đăng ký một giả thuyết mới với khung giờ không có phiên sáng thứ Hai.

## Giả thuyết và hai nhánh độc lập

Dữ liệu là **nến M1 Bid/Ask thật** của EURUSD, GBPUSD, AUDUSD, USDJPY từ Dukascopy, mỗi tháng có SHA-256 nguồn; không dùng dữ liệu H1/M15 để nội suy.

Mỗi nến M1 tín hiệu phải vượt **đỉnh/đáy 60 nến M1 đã đóng trước đó >=0,8 pip**, rồi đóng lại bên trong vùng ít nhất 0,1 pip. Spread close nến tín hiệu <=2,5 pip và <=1,25 × median spread 120 nến trước; giống v2.

- **Đối chứng A — reclaim gốc:** vào lệnh tại OPEN nến M1 ngay sau nến false-break, chỉ xét **thứ Ba, thứ Tư và thứ Năm 10:00–15:59 UTC**.
- **Giả thuyết B — reclaim có xác nhận:** phải chờ **toàn bộ nến M1 liền sau false-break đóng**. Với SELL nến xác nhận phải đóng sâu hơn trong vùng ít nhất **0,25 pip** và **High không vượt High false-break**. BUY đối xứng: Close cao hơn 0,25 pip và Low không thấp hơn Low false-break. **Spread Close xác nhận <= spread Close tín hiệu**, đồng thời <=1,10 × median spread 120 M1 liền trước. Nếu đủ, vào tại OPEN của **nến M1 thứ hai sau tín hiệu**, phải liền kề thời gian đúng một phút; nếu không đủ, bỏ tín hiệu. Không dùng nến xác nhận trước khi nó đóng.
- Cả hai nhánh chỉ nhận entry **thứ Ba–Năm 10:00–16:00 UTC**; không dùng dữ liệu thứ Hai đầu phiên để chọn thứ lợi nhuận tốt. Mỗi nhánh riêng **tối đa một lệnh được vào mỗi tuần ISO** trên cả bốn cặp. Khi có nhiều sự kiện cùng lúc, dùng quy tắc cố định: độ xuyên phá sâu hơn, sau đó tên cặp; không chọn sau khi nhìn lời/lỗ.

Giữ nguyên: SL ngoài cực trị nến phá vỡ giả 1 pip, TP **+2R ròng dự kiến** theo Bid/Ask và giả định trượt giá 0,1 pip mỗi chiều; rủi ro thiết kế tối đa **0,5% equity/lệnh**, lot bước 0,01, đòn bẩy danh nghĩa tối đa 5×, giữ tối đa 120 nến M1, mô phỏng SL trước nếu một nến chạm cả SL và TP. Kiểm định x2 spread **giữ nguyên entry/SL/TP/lot** và trừ thêm một lần spread thực tại entry trên chính các lệnh gốc, không cho stress vô tình cải thiện PnL.

## Khoảng thời gian mới, đặt trước khi nhìn kết quả

Năm **2026**, **chín tháng liên tiếp từ 01/2026 đến hết 09/2026**, gồm **36 file dữ liệu tháng/cặp** từ nguồn M1 mới:
- **Khảo sát sớm:** 01–04/2026 (4 tháng).
- **Kiểm tra về sau, chưa điều chỉnh dựa vào khảo sát sớm:** 05–09/2026 (5 tháng).

Các năm 2019–2025 đã được quan sát nhiều lần và **không tái sử dụng để “chứng minh” v3**. Năm 2026 có thể đã xuất hiện trên nghiên cứu H1 trước đó, nên không tuyên bố “pristine holdout” ở cấp toàn dự án; đây là **độ phân giải dữ liệu M1 mới chưa dùng thử v3**.

**Tài khoản mỗi tháng bắt đầu 1.000 USD riêng.** Không cộng các tỷ lệ phần trăm tháng thành lợi nhuận 9 tháng hay lãi kép liên tục; chỉ cộng USD như thống kê chín phép thử. Có thể có hai lệnh ở cùng tuần ISO thuộc hai tháng khác nhau, phải ghi chú và KHÔNG được gọi là một tài khoản liên tục tuân thủ max 1 lệnh mỗi tuần khi ghép lại.

## Cổng kiểm định nghiêm ngặt

Giả thuyết B cần đạt cả:
- Nhóm 01–04/2026: **>=12 giao dịch**, tổng PnL USD >0, PF>1,1, spread x2 PnL>0.
- Nhóm 05–09/2026: **>=16 giao dịch**, tổng PnL USD >0, PF>1,1, spread x2 >0 và **cận dưới Wilson một phía 95% p(win)>33,33%** (trong thực tế lệnh hết giờ làm payoff khác lý tưởng +2R/-1R, vì vậy cần xét PnL riêng).
- Nhóm B nên tốt hơn nhóm đối chứng A trong cùng giai đoạn về sau. Do hai nhánh không đảm bảo giao dịch ghép cặp 1-1, chỉ là so sánh chính sách và không phải chứng minh nhân quả.
- Kể cả vượt cổng cũng chỉ được **GO kiểm tra tick + forward demo ít nhất 3 tháng**, chưa phải dùng tiền thật.

Số mẫu tuần rất hạn chế; báo cáo tỷ lệ thắng, chi phí, Profit factor, drawdown sau giao dịch đóng, tình huống trùng giờ/cặp và sai khác giữa từng tháng. Nếu thất bại, giữ nguyên kết quả **NO-GO**. Không thay thông số 0,25pip, spread 1,10×, thời gian 10–16 chỉ vì kết quả 2026.

Không có tick nội phút, swap, slippage thực Exness, order book FX toàn thị trường hay dữ liệu dòng lệnh tổ chức. Dấu hiệu “quét giá” ở đây chỉ mô tả giá vượt rồi quay lại, **không chứng minh có người cố ý quét thanh khoản**.

[Mã](scripts/quantmind_v3_m1_confirm.py) · [Kiểm thử nhân quả](tests/test_quantmind_v3_m1_confirm.py).
