# EconEdge EUR/USD + GBP/USD — kiểm định thật H1 2026 Jan–Sep, ngược bốn tuần

**Ngày thực hiện:** 31/10/2026.  
**Phán quyết:** **CHƯA XÁC NHẬN LỢI THẾ / KHÔNG GIAO DỊCH TIỀN THẬT**. Nhưng có dấu hiệu giá và kích thước hợp đồng đáng kiểm tra forward.

## Nguồn / công việc đã hoàn thành

- [GitHub Actions 2026 hoàn thành thành công, 13 unit tests passed](https://github.com/thietk-stack/eurusd-auto-backtest/actions/runs/41155530651)
- Artifact **`econedge-eurgbp-2026-verified-results`** gồm: `EURGBP_2026_RESULTS.json`, `FROZEN_2026_WEEKLY_DIRECTION.csv`, bốn CSV sổ lệnh, bốn CSV quyết định đặt/bỏ, `BAO_CAO_EURGBP_2026.md`.
- [Mã nghiên cứu 2026 đã chạy](scripts/econedge_2026_eurgbp.py) · [Regression tests](tests/test_econedge_2026_eurgbp.py) · [Lệnh chạy tự động](.github/workflows/econedge_eurgbp_2026_run.yml).
- Dữ liệu **Dukascopy H1 thật**, báo giá BID/ASK **lúc mở nến**, kiểm chứng **26 file tháng/cặp** từ 09/2025–09/2026 với SHA-256 từng file; 6.754 nến H1 giao nhau của EUR/USD và GBP/USD. 2026 chỉ có 38 tuần hoàn chỉnh từ Jan–Sep, **không phải toàn bộ 2026**.
- 2026 không phải holdout hoàn toàn nguyên vẹn của toàn dự án vì lịch sử 2026 từng xuất hiện trong nghiên cứu M1; riêng lựa chọn chỉ EUR/USD và GBP/USD đã quyết định từ kết quả 2011–25, do đó kiểm định 2026 **vẫn cần forward demo ngoài mẫu mới**.

## Quy tắc được giữ nguyên

- 08:00 UTC thứ Hai, dùng **480 nến H1 đã hoàn thành** của hai cặp để tính z momentum; chọn cặp |z| cao nhất, phải ≥0,80.
- Phương án chính: đảo chiều so với xu hướng bốn tuần; đối chứng: đi theo xu hướng, cùng cặp và cùng thứ Hai.
- Không TP 2R cố định: đóng thứ Sáu 20:00 UTC hoặc SL trước. Stop = 6×median biên độ 72 H1, tối thiểu 8pip, bỏ lệnh nếu >70pip.
- Rủi ro Stop Loss **thiết kế 0,5% vốn $1.000/lệnh**, max danh nghĩa 5×, mỗi tuần không quá một lệnh; spread theo giá BID/ASK và giả định slippage 0,1pip mỗi chiều. Stress spread ×2 giữ nguyên lệnh/lot và trừ phí gia tăng quan sát, không dịch mục tiêu.
- Hai biến thể hợp đồng: **min 0,01 lot chuẩn** và **min 0,001 standard-lot tương đương** (*chỉ mô phỏng*, chưa kiểm chứng điều kiện tài khoản/broker).
- Đã sửa **lỗi kỹ thuật làm tròn lot** ở chính hàm backtest: `LOT_STEP=0.001` phải làm tròn 3 chữ số thay vì 2; **giữ nguyên logic khi LOT_STEP=0.01**. Lỗi và sửa lỗi được ghi trong lịch sử commit, bài kiểm tra đảm bảo ngân sách rủi ro không bị vượt. Đây là sửa lỗi thực thi, không phải chọn lại ngưỡng sau khi nhìn lợi nhuận.

## Dữ liệu 2026 — không phóng đại giá trị

| Chỉ tiêu | Kết quả |
|---|---:|
| Số tuần lịch đầy đủ đã xem xét | 38 |
| Tuần đủ `|z|≥0,8` | 21 |
| Đảo chiều, pip trung bình sau chi phí ước lượng | **+9,3619 pip/tuần tín hiệu** |
| Thuận xu hướng cùng tuần, pip trung bình | **−10,5143 pip/tuần tín hiệu** |
| Bootstrap 8 tuần, cận dưới 95% đảo chiều pip | **−3,7955 pip/tuần** |

**Cận dưới bootstrap âm: chưa thể xác nhận rằng kỳ vọng chuyển động giá dương.** Số pip đo giá đến cuối tuần, **không áp dụng stop/lot và không đại diện cho tiền thật**.

### Kết quả tài khoản mô phỏng $1.000 theo kích cỡ lệnh

| Quy mô | Hướng | Lệnh thực hiện | Thắng | Lãi/lỗ USD | Profit factor | Spread ×2 USD | Bootstrap lower bình quân USD/tuần |
|---|---|---:|---:|---:|---:|---:|---:|
| **Min 0,01 standard lot** | Đảo chiều | **2** | **0** | **−4,535** | **0,000** | −4,605 | −0,2595 |
| Min 0,01 standard lot | Thuận xu hướng | 2 | 0 | −7,640 | 0,000 | −7,705 | −0,5009 |
| **Min 0,001 standard lot, giả định** | **Đảo chiều** | **13** | **8** | **+17,7985** | **1,862** | **+17,3835** | **−0,1431** |
| Min 0,001 standard lot, giả định | Thuận xu hướng | 13 | 3 | −25,8180 | 0,406 | −26,2140 | −1,4340 |

Kịch bản min 0,01: 38 quyết định, 17 tuần tín hiệu yếu, **8 tuần stop quá rộng**, **11 tuần không đạt min lot**, chỉ còn 2 giao dịch. Min 0,001 giả định: 13 giao dịch từ các tuần tín hiệu, 8 thắng, lợi nhuận sau phí quote/slippage mô phỏng ≈1,78% **cho 9 tháng Jan–Sep**, không phải mỗi tháng. Chưa có swap, triple-swap hoặc điều kiện khớp Exness nên **không công bố 1,78% là lợi nhuận broker**.

### Tài khoản Exness Standard Cent — điều kiện khả thi hơn về lot

Tài liệu Exness cập nhật tháng 09/2026: [Standard Cent](https://get.exness.help/hc/en-us/articles/17537782786588-Standard-Cent-account) ghi **1 cent lot bằng 0,01 standard lot** (1.000 đơn vị tiền cơ sở) và mức tối thiểu 0,01 cent lot. **0,1 cent lot tương đương 0,001 standard lot** về lượng tiền cơ sở. Vì vậy, về mặt kích thước danh nghĩa, mô hình 0,001 standard lot **có thể** tái hiện dưới dạng 0,1 cent lot, **nếu tài khoản người dùng hỗ trợ loại account, bước lot và cặp tương ứng**. Không sử dụng spread Dukascopy để khẳng định PnL Standard Cent: Exness có bảng giá/điều kiện riêng, và swap/rollover theo tài khoản có thể khác. Nguồn chính thức Standard account là [Exness Standard](https://get.exness.help/hc/en-us/articles/17537782738460-Standard-account), mức tối thiểu 0,01 standard lot.

Cần kiểm tra chính xác khối lượng danh nghĩa, pip value, contract size, bước lot, swap và spreads của **EURUSDc/GBPUSDc** trên MT4/MT5 demo hoặc thông số broker trước khi đưa chi phí vào nghiên cứu.

## Kết luận / cổng an toàn

Dù đảo chiều trong kịch bản lot nhỏ có PnL dương, **13 lệnh không đủ cho lợi thế vững**; bootstrap lower của lợi nhuận tuần **âm**. Kịch bản lot 0,01 tiêu chuẩn còn âm. Giai đoạn 2011–17 đã được thấy trước; dữ liệu 2026 H1 không giải quyết toàn bộ nhiều lần thử nghiệm/hậu nghiệm. **Cổng trước kiểm định không đạt** và không được chuyển qua giao dịch thật.

**Đề xuất nghiên cứu tiếp:** khóa chính sách dùng **EURUSDc/GBPUSDc Standard Cent quy mô tương đương 0,001 standard lot**, thu thập giá Bid/Ask + swap thực tế broker (ưu tiên dữ liệu demo/ghi chép), quan sát tuần mới từ cuối 2026 sang 2027 với cùng quy tắc và cập nhật cận bootstrap, PF, DD, chi phí x2. Không tăng rủi ro 0,5% và không thay stop hoặc ngưỡng z chỉ vì dữ liệu 2026.
