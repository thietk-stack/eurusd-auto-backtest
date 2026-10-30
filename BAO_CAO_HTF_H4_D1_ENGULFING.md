# Backtest vùng hỗ trợ/kháng cự cứng H4/D1 + Engulfing H1

**Ngày:** 30/10/2026. **Trạng thái:** Kiểm định ngoài mẫu hoàn thành; **chưa có chiến lược nào đủ điều kiện dùng vốn thật**.

- [Đề cương khóa trước khi xem kết quả](DE_CUONG_HTF_H4_D1_ENGULFING.md)
- [GitHub Actions chạy thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41094413654)
- [Mã nguồn thực thi](scripts/htf_hard_zones_engulf.py)
- Artifact `htf-four-touch-engulfing-results`: 16 CSV sổ lệnh theo phiên bản/vùng và phí stress, `RESULTS_HTF_PRICE_ACTION.json`, báo cáo tự xuất.

## Quy tắc SL/TP được áp dụng

- Vùng H4 hoặc D1 chỉ được công nhận sau **4 pivot giá đã xoay chiều**; mỗi pivot cần 2 nến khung lớn đóng phía sau để xác nhận.
- Vùng `same`: 4 chạm hỗ trợ hoặc 4 chạm kháng cự. Vùng `flip`: tổng 4 chạm và có đủ hai vai trò hỗ trợ–kháng cự. Cùng thời điểm chỉ dùng các vùng đã xuất hiện từ quá khứ.
- Nến H1 xác nhận bắt buộc là **body-engulfing** đúng hướng phản ứng; chạm vùng, đóng vượt đường giữa vùng; vào ở open nến H1 kế tiếp.
- **BUY**: SL nằm dưới mức thấp hơn giữa mép dưới vùng và đáy engulfing, thêm 1,5 pip. **SELL**: SL nằm trên mức cao hơn giữa mép trên vùng và đỉnh engulfing, thêm 1,5 pip.
- TP gộp ban đầu **2R** khoảng SL; nếu có vùng cứng ngược chiều cản trước TP thì TP dời về ngay trước mép vùng (đệm 1 pip). Chỉ nhận khi **R:R dự kiến sau phí ≥ 1:1,5**.
- Rủi ro thiết kế **0,5R/lệnh = 0,5% equity lúc đặt lệnh**, theo quy ước 1R=1% vốn; đòn bẩy hiệu dụng tối đa 5 lần, lot bội 0,01; tối đa một vị thế toàn bộ 4 cặp và một tín hiệu vào mỗi tuần ISO. Lệnh hết hạn sau 96 nến H1.
- Không sử dụng RSI, EMA, ATR, volume hoặc yếu tố ML; toàn bộ tín hiệu là price action.

## Kết quả chính

Dữ liệu lịch sử **thực từ Dukascopy H1 Bid/Ask**, giao nhau của 4 cặp EUR/USD, GBP/USD, AUD/USD, USD/JPY gồm **42.589 nến H1**. Mỗi phiên bản trong từng giai đoạn bắt đầu với **1.000 USD** giả định, không có lệnh tiền thật.

| Vùng / vai trò | Validation 2021–22: lệnh | Lãi/lỗ | Profit factor | DD | Holdout 2023–26: lệnh | Lãi/lỗ | Profit factor | DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **H4 cùng vai trò** | 53 | **+1,32%** | 1,095 | −3,98% | 110 | **+0,93%** | 1,035 | −4,79% |
| H4 đổi vai | 77 | −4,35% | 0,782 | −6,13% | 152 | +0,60% | 1,016 | −5,27% |
| **D1 cùng vai trò** | 23 | +3,94% | 1,854 | −1,88% | 101 | **−7,90%** | 0,687 | −8,92% |
| D1 đổi vai | 33 | −1,73% | 0,792 | −2,23% | 126 | +1,37% | 1,047 | −4,60% |

Lãi/lỗ phần trăm ở trên tính **cho cả giai đoạn nhiều năm**, không phải mỗi tháng.

### Thắng và phí spread x2 trên giai đoạn 2023–2026

| Vùng | Win rate | Lãi/lỗ khi spread tăng x2 | RR dự kiến sau phí nhỏ nhất | Tháng đạt +5% |
|---|---:|---:|---:|---:|
| H4 cùng vai | 35,45% | **−2,01%** | 1,518 | 0 |
| H4 đổi vai | 36,84% | **−0,09%** | 1,514 | 0 |
| D1 cùng vai | 27,72% | **−7,62%** | 1,538 | 0 |
| D1 đổi vai | 38,89% | **+0,65%** | 1,504 | 0 |

Không một phép thử holdout nào có tháng lợi nhuận >=8% theo phương pháp lãi/lỗ đã hiện thực hóa.

**H4 cùng vai trò** là phiên bản hiếm hoi dương ở cả hai kỳ, nhưng PF validation chỉ **1,095** (<1,10 đã chốt), PF holdout **1,035** và spread x2 chuyển thành lỗ. **D1 cùng vai** validation +3,94% nhưng chỉ 23 giao dịch (<25 theo tiêu chí), còn holdout lỗ 7,90%. **D1 đổi vai** có lãi trong kỳ cuối và vượt stress, nhưng validation trước đó lỗ, nên không được chọn sau khi nhìn kết quả mới.

## Kiểm toán từng giao dịch

Tôi đã kiểm tra **toàn bộ 8 CSV chính** của bốn cấu hình trong hai giai đoạn:

- Không giao dịch nào có <4 lần chạm, RR dự kiến dưới **1,5**, hoặc *designed_risk_usd* vượt **0,5% vốn trước lệnh**.
- Không có tuần ISO nào chứa hai lệnh vào trong cùng phép thử. Tất cả giao dịch của từng cấu hình có trật tự thời gian.
- `gross_usd − fees_usd = net_usd` với sai lệch tối đa khoảng 4×10⁻¹⁵ USD; số dư tính lại khớp với xuất CSV ở sai số làm tròn máy.
- Có trường hợp **lỗ hiện thực hóa vượt ngân sách rủi ro thiết kế** vì chi phí tại lúc thoát/gap/khớp gần đúng, nên 0,5R **không phải mức thua tuyệt đối được bảo đảm**.

## Những hạn chế cần nêu rõ

Các nến H4 và D1 được kết từ H1 có dữ liệu đồng thời của bốn cặp; **không phải tick Exness**. H1 OHLC không xác định thứ tự chính xác SL/TP bên trong mỗi nến; chọn SL trước nếu cùng chạm (thận trọng). Giá đóng và spread nội nến chỉ được ước lượng; mô hình phí dùng Bid/Ask Dukascopy ở giá mở nến, giả định trượt giá 0,1 pip mỗi chiều, **chưa tính swap/rollover, lãi suất, hoa hồng riêng, lịch tin hoặc latency Exness**. Drawdown thống kê từ lệnh đã đóng, chưa bao gồm rủi ro thả nổi. Các kết quả không chứng minh tài khoản Exness sẽ được khớp ở mức tương đương.

## Quyết định

**NO-GO cho vốn thật.** Không điều chỉnh các ngưỡng theo dữ liệu holdout 2023–2026 đã nhìn thấy rồi gọi kết quả đó là kiểm định độc lập. Nếu muốn nâng chất lượng, chạy thử forward demo một phương pháp đã chốt trước, hoặc thu thập dữ liệu mới tách biệt; chú ý giá trị thực của việc lọc vùng H4 so với D1 và nến engulfing trong điều kiện spread động.
