# ECONEDGE MACRO v1 — nghiên cứu thật nguồn lợi suất, dòng vị thế và phần thưởng rủi ro FX

**Ngày hoàn thành:** 31/10/2026. **Trạng thái thực tế:** cả 2 workflow chạy thành công; **chưa xác nhận được lợi thế ổn định, NO-GO tiền thật.**

## 1. Kết quả dòng vị thế tổ chức (CFTC TFF Futures Only) — thực thi kiểm định sau chi phí

- [Đề cương trước khi chạy](DE_CUONG_ECONEDGE_MACRO_COT_CARRY_V1.md)
- [GitHub Actions 2011–2025 CFTC thực sự hoàn thành](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41160441156)
- [Mã nguồn kiểm thử](scripts/econedge_macro_cftc_v1.py) · [Kiểm thử độ trễ](tests/test_econedge_macro_cftc_v1.py)
- Artifact `econedge-macro-cftc-real-data-2011-2025` gồm **17 tệp**, trong đó **28.532.279 byte CSV nguồn CFTC nguyên bản**, source SHA256 `3f4c0cc8759b062f67407c64474764b1f9c276df7ef54af3169168c4f5c22a17`, 3.340 bản ghi FX đã xử lý, 779 sự kiện/tuần, sổ lệnh và sổ quyết định ở các giai đoạn.
- Chính thức truy xuất API [CFTC TFF Futures Only, dataset gpe5-46if](https://publicreporting.cftc.gov/resource/gpe5-46if.csv); đây là **vị thế hợp đồng tương lai được công bố**, KHÔNG phải dữ liệu vốn ngoại hối thực chảy vào thị trường spot. Bốn hợp đồng thực được xác nhận từ source: `EURUSD = 099741`, `GBPUSD = 096742`, `AUDUSD = 232741`, `JPY = 097741` (JPY futures LONG tương ứng SELL USDJPY spot); 835 báo cáo/cặp giai đoạn 2010–2025.
- Không nhìn trước thời gian công bố: mỗi thứ Hai 08 UTC chỉ được phép dùng dữ liệu vị thế thứ Ba **đã qua ít nhất 13 ngày lịch**; thông thường CFTC công bố thứ Sáu, nhưng các ngày trễ lịch không được kiểm toán từng năm. Tín hiệu là **thay đổi bốn bản báo cáo liên tiếp của tỷ lệ (Asset manager net long-short)/Open Interest**; chọn cặp |thay đổi| lớn nhất. So sánh đi **cùng** thay đổi vị thế với đi **ngược** thay đổi vị thế tại cùng cặp/tuần. Không chỉnh chỉ tiêu sau khi xem kết quả.
- Giao dịch mô phỏng một tuần vào thứ Hai 08, thoát stop hoặc thứ Sáu 20, dữ liệu Dukascopy H1 Bid/Ask OPEN thật và nến H1 mid High Low để ước lượng stop, stop 6×median 72H tối đa 70pip, rủi ro thiết kế ≤0,5% vốn, 5× leverage, lot min/bước 0,001 giả định, giả định trượt giá 0,1pip mỗi chiều; đã mô hình hóa spread thật lúc Open và stress spread×2. **Không bao gồm phí swap/forward/carry thực hoặc tick dealer**.

| Giai đoạn (tài khoản $1.000 reset từng nhóm) | Đi cùng thay đổi vị thế: lệnh | PnL USD | PF | Đi ngược thay đổi vị thế: lệnh | PnL USD | PF | Đi ngược: spread×2 USD | Đi ngược: bootstrap LB 95% USD/tuần |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2011–2017 | 94 | **−110,14** | 0,576 | 94 | **+95,54** | 1,443 | +90,16 | +0,0193 |
| 2018–2025 | 167 | **−63,39** | 0,849 | 167 | **−32,68** | 0,925 | −43,73 | −0,3202 |
| **Toàn 2011–2025, vốn chạy liên tục riêng** | 261 | **−166,64** | 0,735 | 261 | **+56,52** | 1,081 | +39,15 | **−0,1080** |

- Đối chứng giao dịch **ngược** thay đổi vị thế của asset managers tốt hơn chính sách đi cùng vị thế trong giai đoạn cũ; song **không giữ được lợi thế ở 2018–2025**. Cận bootstrap toàn kỳ vẫn âm, và PF 1,081 thấp hơn cổng 1,1; chính sách giao dịch theo thay đổi vị thế có drawdown −17,93% ở 15 năm, vượt trần 15% vốn đóng lệnh.
- **Không thể gọi dòng vị thế CFTC là “dòng tiền lớn biết trước giá”**. Báo cáo vị thế được sử dụng **trễ** và có thể đại diện cho hedging, thay đổi phân loại nhóm, hay thị trường futures riêng.

## 2. Kiểm định chênh lệch lãi suất liên ngân hàng 3 tháng — CHỈ thử khả năng dự báo biến động giá

- [GitHub Actions lãi suất OECD/FRED thực sự hoàn thành](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41160588432)
- [Mã kiểm định](scripts/econedge_macro_rate_proxy_v1.py) · [Kiểm thử](tests/test_econedge_macro_rate_proxy_v1.py).
- Artifact `econedge-3month-rate-spotsignal-2011-2025` gồm **CSV nguyên bản 5 series tỷ suất 3 tháng**, SHA256 `66ea842c8833af62b1cfa6b92e6b0e90104303711f939e2441d3b2ead901c1e9`, toàn bộ 178 tín hiệu tháng và báo cáo; nguồn [FRED/ OECD 3-Month Interbank Rate](https://fred.stlouisfed.org/series/IR3TIB01USM156N), EUR `IR3TIB01EZM156N`, GBP `IR3TIB01GBM156N`, AUD `IR3TIB01AUM156N`, JPY `IR3TIB01JPM156N`.
- Mỗi tháng xem lãi suất tham chiếu **lùi hai tháng lịch**, chọn đồng tiền có chênh lệch (foreign−USD) tuyệt đối lớn nhất và đi theo phía **có rate cao hơn**, đo biến động giá spot trong một tháng tiếp theo theo Bid/Ask và 0,1pip slippage mỗi chiều. **Không có STOP, không có lot sizing, vì vậy là chẩn đoán hướng giá theo basis points, KHÔNG phải mô phỏng giao dịch $1.000.**
- Quan trọng: **KHÔNG cộng chênh lệch lãi suất vào lợi nhuận giao dịch.** Lãi suất 3 tháng là proxy cho giá vốn, không phải forward points, swap Exness, tiền lãi thật có thể nhận, hoặc phần thưởng đã được khóa. OECD/FRED time series có khả năng điều chỉnh hồi tố; độ trễ hai tháng không bảo đảm dữ liệu là vintage bất biến đúng tại thời điểm lịch sử.

| Giai đoạn | Số tháng | Đi theo đồng tiền rate cao: bình quân biến động spot bps/tháng | Đối chứng ngược chiều bps/tháng | Bootstrap cận dưới 95% bps/tháng |
|---|---:|---:|---:|---:|
| 2011–2017 | 84 | **−30,67** | +28,11 | −82,36 |
| 2018–2025 | 94 | **+32,80** | −33,78 | −1,55 |
| **2011–2025** | **178** | **+2,85** | −4,57 | **−29,42** |

- Giai đoạn 2011–2017, nhóm **lãi suất cao hơn lại mất giá spot** trong thử nghiệm này, nên không thể suy ra lợi suất danh nghĩa cao → Forex tăng giá.
- Trong giai đoạn 2018–2025, mức spot trung bình dương nhưng bootstrap vẫn có cận dưới âm; **chưa có lợi thế dự báo được xác nhận**. Chênh lệch lãi suất có thể đi kèm rủi ro mất giá, nên giá spot và dòng tài trợ phải được phân tách.

## 3. Vậy “rủi ro nào được thị trường trả công”?

Thử nghiệm cho thấy **rủi ro của việc cầm đồng tiền lãi suất cao** không được trả công một cách ổn định trong giá spot của bốn cặp. Nhưng **không thể kết luận chiến lược carry thực sự thua hay thắng từ bài này**, vì thiếu thành phần thu nhập forward/swap.

Có ba cách tạo thu nhập khác nhau mà không được trộn:
1. **Dealer spread/liquidity revenue:** người tạo giá thu chênh lệch Bid/Ask đổi lại quản lý inventory và nhận rủi ro người có thông tin giao dịch. Không thể backtest thu nhập dealer chỉ bằng nến H1.
2. **Interest differential / FX forwards:** có thể phản ánh các điều kiện lãi suất, basis, tài trợ và rủi ro sụp đổ giá; cần giá forward hoặc lịch sử swap broker thực để tính PnL thực.
3. **Currency risk premium / large trend convexity:** có thể là lợi thế đặc thù nhiều tài sản, thời kỳ, cấu trúc funding; một mô hình đơn lẻ 4 cặp USD mà không có kiểm định forward không được coi là đã nắm được nguồn premium.

## 4. Kế hoạch kiểm định mới, không dùng dữ liệu đã xem để cố lọc ra lời

- **CFTC:** nếu muốn nghiên cứu tiếp, dùng nguồn TFF đã lưu để phân biệt Asset Managers và Leveraged Funds, nhưng việc xem phân loại nhóm hoặc thay đổi lookback **sẽ là giả thuyết mới, không còn holdout 2011–25**. Phải chốt tiêu chí trước, đánh giá forward sau thời điểm nghiên cứu.
- **Interest carry:** ưu tiên thu thập **giá forward points lịch sử và/hoặc lịch sử swap của chính cặp/tài khoản/broker đang định sử dụng**, bao gồm swap thứ Tư/triple-swap, spread, commission, lịch rollover; không dùng lãi suất 3m hiện tại để cộng giả định lợi nhuận quá khứ.
- **Risk management:** chỉ xem GO khi có mẫu đủ lớn từ các giai đoạn mới, lãi sau tất cả chi phí, stress vẫn dương, bootstrap lower >0; giữ rủi ro ≤0,5% vốn, test lot 0,001 theo điều kiện tài khoản xác thực, không có lệnh tiền thật.

**Kết luận chung: NO-GO real-money.** Đã tìm được một số giả thuyết có cơ sở kinh tế, nhưng **chưa có bằng chứng một lợi thế có thể giao dịch ổn định**. Đây là kết luận thực nghiệm, không phải dự báo rằng mọi trader sẽ thua.

### Nguồn kinh tế chính thống

- [CFTC — TFF Futures Only](https://publicreportinghub.cftc.gov/d/gpe5-46if)
- [CFTC — ngày công bố báo cáo COT và độ trễ ngày nghỉ](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm)
- [OECD/FRED — lãi suất liên ngân hàng 3 tháng Hoa Kỳ](https://fred.stlouisfed.org/series/IR3TIB01USM156N)
- [BIS — FX swaps, forwards và chức năng tài trợ thị trường](https://www.bis.org/publications/202509-commentary-otc-derivatives)
