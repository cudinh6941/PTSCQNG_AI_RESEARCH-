---
type: pain_point
department: Chuyển đổi số
reporter: 
frequency: Daily
time_wasted_hours: 5
impact_level: High
ai_solution_type: Log Analysis / Classification
estimated_roi: 
status: Mới ghi nhận
linked_poc: 
date_created: "2026-08-04"
---

# PP_001 — Log lỗi hệ thống phải đọc bằng mắt

## Mô tả vấn đề
> Hiện tại log lỗi hệ thống phải đọc thủ công bằng mắt, không có công cụ tự động phân tích hoặc phân loại lỗi.

## Quy trình hiện tại (Manual)
1. Bước 1: Mở log file (text hoặc event viewer)
2. Bước 2: Đọc từng dòng, tìm pattern lỗi
3. Bước 3: Phân loại lỗi (critical/warning/info) thủ công
4. Bước 4: Ghi chép lại và báo cáo

## Tần suất & Tác động
- **Bao lâu gặp 1 lần:** Hàng ngày
- **Mỗi lần mất bao lâu:** ~5 giờ/tuần
- **Bao nhiêu người bị ảnh hưởng:** Team IT/DT
- **Hậu quả nếu không giải quyết:** Bỏ sót lỗi critical, phản ứng chậm

## Giải pháp AI dự kiến
- **Loại AI:** LLM + Classification
- **Input:** Log files (text/CSV)
- **Output mong muốn:** Phân loại lỗi, highlight critical, đề xuất action
- **Mức độ tự động hóa:** Bán tự động (AI phân loại → người review)

## Ghi chú thêm
- Có thể là use case tốt cho Agent 6 (IT Assistant) trong tương lai
