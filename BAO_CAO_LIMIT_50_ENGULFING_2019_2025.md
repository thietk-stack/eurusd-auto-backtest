# Price Action H4/D1 + H1 Engulfing — LIMIT 50% nến, kết quả từng năm 2019–2025

**Ngày:** 30/10/2026  
**Trạng thái:** GitHub Actions chạy THÀNH CÔNG; chiến lược **CHƯA CHỨNG MINH lợi thế giao dịch đủ ổn định**. Không đặt lệnh tiền thật.

- [Đề cương cố định trước khi chạy](DE_CUONG_LIMIT_50_ENGULFING_2019_2025.md)
- [Lượt chạy GitHub Actions và sổ giao dịch/JSON đầy đủ](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41095941707) (artifact: `htf-limit-midpoint-yearly-2019-2025`)
- [Mã nguồn thực thi](scripts/htf_limit_mid_yearly.py), [kiểm thử limit](tests/test_htf_limit_mid.py)

## Phương pháp

Giá **Dukascopy EUR/USD, GBP/USD, AUD/USD, USD/JPY H1 Bid/Ask thật**, 49.877 nến H1 cùng thời điểm và có dữ liệu 2018 khởi tạo vùng. Không có giá khớp lệnh tick Exness, swap hoặc lịch tin lịch sử.

Bốn định nghĩa vùng 4 lần phản ứng HTF như trước: `H4_same` (4 cùng vai trò), `H4_flip` (4 có cả hai vai trò), `D1_same`, `D1_flip`. Chỉ kích hoạt sau pivot đã xác nhận hai nến HTF phía sau, không sử dụng RSI, EMA, ATR hay khối lượng.

**Điểm vào thay đổi theo yêu cầu:** limit tại **50% toàn bộ chiều dài nến H1 engulfing** `(High+Low)/2`; không phải 50% thân. BUY LIMIT chờ giá hồi xuống, SELL LIMIT chờ giá hồi lên; nếu không chạm trong **12 nến H1 quan sát** thì hủy. Mức giá mở nến tốt hơn được ghi nhận nếu có gap qua limit; nếu trong nến khớp chạm cả limit và SL thì coi là lỗ SL (bảo thủ, không biết tick order), không ghi TP cùng nến khớp.

**SL BUY:** dưới Low engulfing 1 pip; **SL SELL:** trên High engulfing 1 pip. TP bắt đầu ở 2R gộp so với giá limit; hạ về trước vùng cứng đối diện nếu chắn đường đi. Trước khi gửi và ngay lúc limit khớp, chỉ nhận nếu **R:R kỳ vọng sau chi phí ≥1:1,5**. Rủi ro thiết kế **0,5% equity mỗi lệnh**, giới hạn notional 5x, lot 0,01, tối đa **một lệnh được khớp mỗi tuần** và một vị thế mở. Vì limit có thể hết hạn không khớp, **số limit đặt có thể nhiều hơn số tuần**; giới hạn là các lệnh *khớp* chứ không phải các tín hiệu được xét.

Vốn thử nghiệm đầu **mỗi năm** được reset riêng về **1.000 USD**, không cộng lợi nhuận từng năm thành lãi kép để tuyên bố hiệu quả thực tế liên tục.

## Lợi nhuận ròng mỗi năm (% vốn đầu năm)

| Năm | H4 cùng vai trò | H4 đổi vai | D1 cùng vai | D1 đổi vai |
|---|---:|---:|---:|---:|
| 2019 | −0,79% | **+4,10%** | −0,69% | −2,11% |
| 2020 | −3,09% | −1,58% | −1,40% | −4,72% |
| 2021 | **+1,00%** | −6,62% | −0,37% | **+2,17%** |
| 2022 | −0,26% | −3,29% | **+0,05%** | **+1,14%** |
| 2023 | −2,46% | −2,52% | −0,38% | −5,85% |
| 2024 | **+1,67%** | −0,38% | −1,69% | **+2,47%** |
| 2025 | −0,93% | −2,13% | **+0,01%** | −1,47% |
| **Năm có lãi** | **2/7** | **1/7** | **2/7** | **3/7** |

Các số là kết quả trong **toàn bộ 12 tháng** tương ứng, chưa tính swap. Không chiến lược nào ghi nhận khả năng đều đặn 5–8% **mỗi tháng**.

## Lệnh limit được đặt và khớp trong 7 năm

| Kiểu vùng | Limit đặt | Thật sự khớp | Hết hạn không khớp | Tỷ lệ thắng khi khớp | RR sau phí tối thiểu |
|---|---:|---:|---:|---:|---:|
| H4 cùng vai | 298 | **238** | 55 | 35,7% | 1,504 |
| H4 đổi vai | 351 | **274** | 72 | 31,4% | 1,501 |
| D1 cùng vai | 191 | **142** | 43 | 31,7% | 1,504 |
| D1 đổi vai | 280 | **226** | 50 | 31,9% | 1,502 |

Phần còn lại là các trường hợp limit hủy vì điều kiện fill/RR/lot và một số lệnh còn chờ tại ranh giới năm. Tổng cộng **880 lệnh khớp trên bốn phép kiểm định**, nhưng đây là **bốn chiến lược thử độc lập**, không phải 880 lệnh trong một tài khoản.

## Kiểm toán sổ lệnh

Dùng toàn bộ 28 file CSV thực tế:
- **Mọi limit khớp** đúng điểm giữa `(High + Low)/2` nếu không mở cửa vượt limit theo hướng có lợi. Điểm **limit yêu cầu** đúng bằng 50% High/Low đối với tất cả lệnh.
- **SL** đúng Low H1 engulfing −1 pip (BUY), hoặc High +1 pip (SELL), **không có sai lệch** trên tất cả các lệnh.
- Không có lệnh khớp nào vi phạm R:R dự kiến **≥1,5**; min RR thực tế theo từng phương án 1,501–1,504.
- Ngân sách rủi ro theo stop + phí được giới hạn thiết kế **≤0,5% vốn trước lệnh**. Không có hai lệnh khớp trong một ISO week cho cùng phép thử.
- Kiểm toán `gross - fees = net` sai lệch nhỏ hơn 4×10⁻¹⁵ USD.

**Cảnh báo rủi ro quan trọng:** Có những lệnh *lỗ thực tế nhiều hơn ngân sách stop* do khoảng trống cuối tuần / nhảy giá và điều kiện khớp mô phỏng. Ví dụ:
- `H4_same`: giao dịch **EURUSD SELL** vào 09/09/2022, thoát 11/09/2022, **lỗ 18,18 USD**, dù rủi ro thiết kế chỉ **4,47 USD**.
- `H4_same`: giao dịch **USDJPY BUY** 02/04/2025, **lỗ 13,95 USD** dù rủi ro thiết kế **4,54 USD**.

**Không nên hiểu 0,5R là mức lỗ tối đa có thể đảm bảo bằng stop**, nhất là khi giữ lệnh qua khoảng trống giá, thị trường ít thanh khoản hoặc tin mạnh.

## Phương pháp và giới hạn cần cải thiện trước mọi quyết định vốn

1. Bộ khớp limit hiện là **H1 OHLC gần đúng**: không có thứ tự tick Bid/Ask bên trong H1 nên không kiểm tra được chính xác lệnh pending đã khớp trước khi SL/TP xuất hiện.
2. Giá nến có nguồn Dukascopy; spread lấy ở điểm mở H1, chi phí trượt giá giả định 0,1 pip/chiều, **không phải lịch sử thực thi Exness**.
3. Không có swap/rollover, chênh lệch spread từng giây, phí broker và ảnh hưởng tin tức; drawdown báo cáo dựa trên lệnh đóng.
4. Dữ liệu 2019–2025 có thể đã được quan sát trong các thử nghiệm trước đó. Đây là **nghiên cứu khám phá**, không phải kết quả out-of-sample nguyên vẹn của một ý tưởng hoàn toàn chưa từng thử.
5. Chạy lại với spread x2 có thể thay đổi cả lệnh được chấp nhận và số lot, chứ không chỉ trừ thêm phí từ một sổ lệnh cố định; không nên suy luận stress dương ở một năm là bằng chứng chiến lược thắng.

**Kết luận:** Phương pháp Limit 50% engulfing và SL 1 pip chưa thể hiện lợi thế bền vững. **NO-GO giao dịch tiền thật** trên cơ sở dữ liệu hiện tại. Nếu muốn nghiên cứu biến thể “50% thân nến” hay “không giữ qua cuối tuần”, cần đăng ký như giả thuyết mới và kiểm tra trên dữ liệu/forward chưa dùng để chọn thông số.
