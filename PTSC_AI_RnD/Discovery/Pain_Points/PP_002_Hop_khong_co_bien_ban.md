---
type: pain_point
department: Tất cả
reporter: 
frequency: Daily
time_wasted_hours: 3
impact_level: High
ai_solution_type: LLM
estimated_roi: 
status: Mới ghi nhận
linked_poc: 
date_created: "2026-08-04"
---

# PP_002 — Họp xong không có biên bản hoặc biên bản viết rất lâu

## Mô tả vấn đề
> Sau mỗi cuộc họp, biên bản thường bị bỏ qua hoặc mất rất lâu để viết. Các quyết định và action items bị quên.

## Quy trình hiện tại (Manual)
1. Bước 1: Họp xong, 1 người phải ngồi ghi lại biên bản
2. Bước 2: Gửi email cho attendees review
3. Bước 3: Chỉnh sửa qua nhiều vòng
4. Bước 4: Lưu vào thư mục chung

## Tần suất & Tác động
- **Bao lâu gặp 1 lần:** Hàng ngày (nhiều cuộc họp mỗi ngày)
- **Mỗi lần mất bao lâu:** 30-60 phút viết biên bản
- **Bao nhiêu người bị ảnh hưởng:** Toàn công ty
- **Hậu quả nếu không giải quyết:** Mất thông tin, quên action items, lặp lại thảo luận

## Giải pháp AI dự kiến
- **Loại AI:** LLM (+ Whisper nếu có audio)
- **Input:** Transcript cuộc họp (text hoặc audio recording)
- **Output mong muốn:** Biên bản, danh sách quyết định, action items, email tóm tắt
- **Mức độ tự động hóa:** Bán tự động (AI sinh draft → người review & chỉnh sửa)

## Ghi chú thêm
- Liên quan trực tiếp đến [[Agent_1_Meeting_Assistant]]
- Impact rất lớn vì áp dụng cho toàn bộ công ty
