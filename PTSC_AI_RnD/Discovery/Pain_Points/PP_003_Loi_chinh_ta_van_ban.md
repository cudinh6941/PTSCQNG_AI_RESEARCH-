---
type: pain_point
department: Tất cả
reporter: 
frequency: Weekly
time_wasted_hours: 2
impact_level: Medium
ai_solution_type: LLM
estimated_roi: 
status: Mới ghi nhận
linked_poc: 
date_created: "2026-08-04"
---

# PP_003 — Hồ sơ văn bản hay bị lỗi chính tả và format

## Mô tả vấn đề
> Văn bản hành chính, hồ sơ kỹ thuật thường có lỗi chính tả, ngữ pháp, hoặc không đúng format chuẩn. Phải review thủ công nhiều lần.

## Quy trình hiện tại (Manual)
1. Bước 1: Soạn văn bản
2. Bước 2: Tự review hoặc nhờ đồng nghiệp review
3. Bước 3: Sửa lỗi → review lại → sửa lại (nhiều vòng)
4. Bước 4: Trình ký

## Tần suất & Tác động
- **Bao lâu gặp 1 lần:** Hàng tuần
- **Mỗi lần mất bao lâu:** 30-60 phút review/sửa
- **Bao nhiêu người bị ảnh hưởng:** Tất cả nhân viên viết văn bản
- **Hậu quả nếu không giải quyết:** Văn bản kém chuyên nghiệp, sai thuật ngữ

## Giải pháp AI dự kiến
- **Loại AI:** LLM
- **Input:** File Word/PDF
- **Output mong muốn:** Danh sách lỗi + gợi ý sửa + vị trí lỗi
- **Mức độ tự động hóa:** Hỗ trợ (AI gợi ý → người quyết định sửa)

## Ghi chú thêm
- Liên quan trực tiếp đến [[Agent_0_Document_Proofreader]]
- Đây là use case đơn giản nhất → nên làm đầu tiên
