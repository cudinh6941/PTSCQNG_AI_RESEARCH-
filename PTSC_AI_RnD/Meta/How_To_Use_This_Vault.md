# 📖 Hướng dẫn sử dụng Vault — PTSC AI R&D Lab

## Mục đích của vault này

Đây là "phòng lab" nghiên cứu ứng dụng AI cho PTSC. Tất cả quá trình nghiên cứu — từ phát hiện pain point, đến thử nghiệm POC, đến thiết kế agent — đều được ghi chép và liên kết trong vault này.

---

## Cấu trúc Folder

| Folder               | Mục đích                                    | Khi nào dùng                |
| -------------------- | ------------------------------------------- | --------------------------- |
| 📥 **Inbox**         | Ghi nhanh ý tưởng chưa phân loại            | Khi có ý tưởng bất chợt     |
| 🔍 **Discovery**     | Pain points, phỏng vấn, department profiles | Khi khảo sát phòng ban      |
| 🧪 **Lab&Research**  | POC, tech notes, prompts, benchmarks        | Khi nghiên cứu & thử nghiệm |
| 🏛️ **Architecture** | Kiến trúc PAIP, Agent Catalog               | Khi thiết kế hệ thống       |
| 📊 **Strategy**      | Roadmap, ROI, stakeholders                  | Khi lập kế hoạch            |
| 📈 **Dashboard**     | Dataview dashboards                         | Xem tổng quan (tự động)     |
| 📝 **Journal**       | Daily & Weekly notes                        | Ghi chép hàng ngày/tuần     |
| 📚 **References**    | Tài liệu tham khảo, papers                  | Khi đọc tài liệu bên ngoài  |
| 🗂️ **Templates**    | Templates cho note mới                      | Không sửa trực tiếp         |
| 🔧 **Meta**          | Hướng dẫn, conventions                      | Tham khảo khi cần           |

---

## Workflow hàng ngày

### 1. Bắt đầu ngày
→ Mở **Dashboard/Research_Overview** để xem snapshot
→ Tạo **Daily Note** (Ctrl+T → chọn Tpl_Daily)

### 2. Phát hiện pain point mới
→ Tạo note trong **Discovery/Pain_Points/** (dùng Tpl_Pain_Point)
→ Điền frontmatter đầy đủ (department, frequency, impact...)
→ Link tới Interview note nếu có

### 3. Nghiên cứu/Thử nghiệm
→ Tạo **Tech Note** trong Lab&Research/Tech_Notes/
→ Tạo **POC** trong Lab&Research/POC/ khi bắt đầu thử nghiệm
→ Lưu **Prompt** trong Lab&Research/Prompts/

### 4. Cuối tuần
→ Tạo **Weekly Review** (dùng Tpl_Weekly)
→ Cập nhật Roadmap nếu cần

---

## Quy tắc đặt tên

| Loại note | Format | Ví dụ |
|---|---|---|
| Pain Point | PP_XXX_Tên_ngắn | PP_001_Log_loi_doc_bang_mat |
| POC | POC_XXX_Tên_ngắn | POC_001_Document_Proofreader |
| Interview | INT_Department_Date | INT_HSEQ_2026-08-05 |
| Tech Note | Tên mô tả tự do | RAG_Pipeline_Research |
| Agent | Agent_X_Tên | Agent_0_Document_Proofreader |
| Daily | YYYY-MM-DD | 2026-08-04 |
| Weekly | WXX_YYYY | W32_2026 |

---

## Frontmatter quan trọng

Mỗi note có YAML frontmatter (`---` block ở đầu). **Luôn điền `type`** — đây là key để Dataview query hoạt động.

| Type | Dùng cho |
|---|---|
| `pain_point` | Pain point notes |
| `poc` | POC notes |
| `agent` | Agent notes |
| `interview` | Phỏng vấn phòng ban |
| `tech_note` | Ghi chép kỹ thuật |
| `prompt` | Prompt library |
| `daily` | Daily notes |
| `weekly` | Weekly reviews |

---

## Plugins cần thiết

| Plugin | Mục đích | Cài chưa? |
|---|---|---|
| **Dataview** | Dashboard, query metadata | ✅ Đã cài |
| **Templater** | Template nâng cao | ❌ Nên cài |
| **Calendar** | Xem daily notes theo lịch | ❌ Nên cài |
| **Kanban** | Board tiến độ POC/Agent | ❌ Tùy chọn |
| **Tasks** | Quản lý TODO xuyên suốt vault | ❌ Tùy chọn |

---

## Tips

- **Link mọi thứ:** Dùng `[[tên note]]` để liên kết Pain Point → POC → Agent
- **Dùng Graph View:** Ctrl+G để xem toàn cảnh liên kết
- **Search mạnh:** Ctrl+Shift+F để tìm kiếm toàn vault
- **Quick Switch:** Ctrl+O để mở nhanh note bất kỳ
