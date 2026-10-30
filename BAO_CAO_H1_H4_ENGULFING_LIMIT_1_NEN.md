# Kết quả thật: Engulfing H1 hoặc H4 — Limit chỉ ở NẾN CÙNG KHUNG KẾ TIẾP

**Ngày:** 30/10/2026. **Kết luận:** chưa chứng minh được chiến lược có lợi nhuận bền vững; không giao dịch thật.

**Kiểm chứng:** [GitHub Actions thành công](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41098333270) · [Đề cương chốt trước kết quả](DE_CUONG_ENGULFING_H1_H4_NEN_KE_TIEP.md) · [Mã nguồn](scripts/htf_engulf_next_candle.py). Artifact GitHub: h1-h4-one-next-candle-price-action-2019-2025, gồm RESULTS_H1_H4_NEXT_CANDLE.json và **56 CSV sổ giao dịch**.

## Quy tắc

- Giá thực lịch sử Dukascopy H1 Bid/Ask cho EUR/USD, GBP/USD, AUD/USD, USD/JPY; 49.877 nến H1 cùng thời điểm trong giai đoạn 2018–2025. Năm 2018 dùng để khởi tạo vùng.
- Vùng hỗ trợ/kháng cự **4 lần chạm đảo chiều xác nhận** theo H4 hoặc D1, hai cách: cùng vai trò (same) hoặc có cả hai vai trò (flip).
- Tín hiệu H1: nến H1 body engulfing tại vùng cứng; đặt limit 50% High–Low của chính nến H1 đó, **chỉ tồn tại trong một nến H1 kế tiếp** (1 giờ), không khớp thì hủy.
- Tín hiệu H4: nến H4 body engulfing tại vùng cứng; đặt limit 50% High–Low của chính nến H4 đó, **chỉ tồn tại trong một nến H4 kế tiếp** (4 giờ UTC); kiểm tra khớp dựa trên bốn nến H1 bên trong. **Không phải H1 chờ 4 giờ.**
- BUY tại vùng hỗ trợ, SELL tại vùng kháng cự. SL BUY = Low engulfing −1 pip; SL SELL = High engulfing +1 pip. TP gộp 2R tính từ limit nhưng đặt trước vùng cứng đối diện nếu gần hơn. Lọc **R:R dự kiến sau chi phí >= 1:1,5** ngay lúc đặt và khi khớp.
- Rủi ro stop + phí thiết kế tối đa **0,5% vốn đang có/lệnh**, 5× đòn bẩy danh nghĩa, 0,01 lot tối thiểu/bước; chung một sổ vốn cho 4 cặp, tối đa 1 lần khớp/tuần. Không ép lệnh.
- Mỗi **năm** bắt đầu với 1.000 USD mô phỏng riêng, đóng lệnh cuối năm. Các tỷ lệ năm KHÔNG được cộng lại làm lợi nhuận kép một tài khoản 7 năm.

## A. Kết quả theo năm với Engulfing H1 (chỉ H1 kế tiếp khớp limit)

| Năm | Vùng H4 cùng vai | Vùng H4 đổi vai | Vùng D1 cùng vai | Vùng D1 đổi vai |
|---|---:|---:|---:|---:|
| 2019 | −0,39% (34) | +3,66% (37) | +0,77% (20) | −2,12% (30) |
| 2020 | −1,25% (34) | −5,86% (35) | −2,28% (14) | −3,85% (26) |
| 2021 | +3,93% (32) | −1,91% (38) | −1,09% (12) | −0,59% (24) |
| 2022 | −0,82% (18) | −2,93% (30) | −0,67% (4) | +2,41% (13) |
| 2023 | −3,52% (20) | −5,71% (34) | −0,86% (20) | −0,61% (34) |
| 2024 | +1,66% (27) | −1,05% (34) | +0,97% (30) | +2,91% (33) |
| 2025 | +3,82% (23) | −0,21% (37) | +0,91% (12) | +0,53% (27) |
| **Số năm có lãi** | **3/7** | **1/7** | **3/7** | **3/7** |

Số trong ngoặc = **lệnh limit thực sự khớp**, không phải số tín hiệu.

## B. Kết quả theo năm với Engulfing H4 (chỉ H4 kế tiếp khớp limit)

| Năm | Vùng H4 cùng vai | Vùng H4 đổi vai | Vùng D1 cùng vai | Vùng D1 đổi vai |
|---|---:|---:|---:|---:|
| 2019 | −4,13% (22) | −1,38% (23) | −0,84% (8) | +2,26% (13) |
| 2020 | −0,20% (13) | −1,67% (19) | −0,58% (4) | +1,24% (9) |
| 2021 | +0,63% (10) | +2,31% (20) | −0,21% (6) | −1,98% (7) |
| 2022 | −0,96% (12) | +1,63% (16) | −0,23% (3) | +0,81% (8) |
| 2023 | −0,07% (9) | +0,34% (21) | −2,59% (13) | −0,91% (19) |
| 2024 | −3,03% (7) | −2,85% (13) | −0,99% (11) | −2,23% (11) |
| 2025 | −1,74% (10) | −3,21% (18) | +0,10% (6) | −2,91% (15) |
| **Số năm có lãi** | **1/7** | **3/7** | **1/7** | **3/7** |

## Tỷ lệ khớp limit trong đúng một nến sau tín hiệu

| Nến tín hiệu | Kiểu vùng | Limit đặt | Khớp | Tỷ lệ khớp | Hết hạn chưa khớp |
|---|---|---:|---:|---:|---:|
| H1 | H4 same | 363 | 188 | 51,8% | 175 |
| H1 | H4 flip | 437 | 245 | 56,1% | 192 |
| H1 | D1 same | 236 | 112 | 47,5% | 124 |
| H1 | D1 flip | 351 | 187 | 53,3% | 164 |
| H4 | H4 same | 171 | 83 | 48,5% | 88 |
| H4 | H4 flip | 225 | 130 | 57,8% | 94 |
| H4 | D1 same | 116 | 51 | 44,0% | 65 |
| H4 | D1 flip | 189 | 82 | 43,4% | 107 |

Một số limit bị hủy vì gap hoặc điều kiện giá/chi phí khi thử khớp nên tỷ lệ 'hết hạn' không phải lúc nào cũng bằng toàn bộ số đặt trừ số khớp. **Tổng cộng 1.078 lệnh khớp giữa tám phép thử độc lập**; không phải một tài khoản mở 1.078 lệnh.

## Kiểm toán và hạn chế

- Kiểm tra toàn bộ CSV: mọi limit được yêu cầu tại đúng midpoint của nến engulfing thuộc khung tín hiệu; SL BUY = Low−1 pip và SL SELL = High+1 pip; tất cả giao dịch có ít nhất 4 phản ứng vùng được xác nhận, R:R dự kiến sau phí >=1,5 và rủi ro thiết kế <=0,5% vốn lúc vào.
- Không có lần khớp limit nào sau khi nến H1 hoặc H4 kế tiếp kết thúc. Không có phép thử nào mở >1 lệnh đã khớp trong cùng tuần ISO. Gross − fees = net với sai số <10⁻⁷ USD.
- **Tồn tại lệnh lỗ thực tế vượt 0,5% vốn** do gap/giả định thực thi. Ví dụ trong H1 + H4 same, có lệnh lỗ 18,18 USD dù rủi ro thiết kế khoảng 5 USD. Không coi 0,5R là mức lỗ tuyệt đối được bảo đảm.
- Mô phỏng H1 OHLC không cho thứ tự tick thật của giao dịch limit, stop và take profit, đặc biệt khi nhiều mức giá cùng nằm trong một nến. Nếu limit và stop cùng có thể chạm, giả định stop bị khớp trước; không ghi TP cùng giờ khớp limit. Dữ liệu Dukascopy Bid/Ask **không phải dữ liệu thực thi Exness**, không có swap/rollover và chưa đo tin kinh tế.
- Các giai đoạn đã được xem trong các nghiên cứu trước đó nên **không còn là dữ liệu holdout nguyên vẹn**. Kết quả này chỉ là kiểm định khám phá, không phải xác nhận độc lập một hệ thống giao dịch có lãi.

**Kết luận:** Việc chỉ chờ 1 cây H1 hoặc 1 cây H4 sau Engulfing giúp giảm những lệnh khớp chậm, nhưng **không tạo ra bằng chứng hiệu quả sinh lời qua nhiều năm**. Kết quả H1 có một số năm dương; H4 không tốt hơn H1 một cách nhất quán. **Không khuyến nghị dùng tiền thật** trên kết quả hiện tại.
