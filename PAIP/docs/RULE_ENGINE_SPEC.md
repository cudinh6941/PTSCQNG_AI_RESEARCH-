# PAIP — Rule Engine & Enterprise Glossary Specification

> **Tài liệu đặc tả kỹ thuật module Rule Engine**  
> **Module:** `PAIP/core/rule_engine/`  
> **Phiên bản:** 1.0  
> **Trạng thái:** Thiết kế kiến trúc hoàn tất — Chờ triển khai  

---

## 1. Mục tiêu & Phạm vi (Scope & Objectives)

Module **Rule Engine** được xây dựng như một thành phần cốt lõi dùng chung (`core/`) cho toàn bộ nền tảng PAIP, nhằm thực thi các bài toán:
1. **Quản lý & chuẩn hóa Từ điển thuật ngữ (Enterprise Glossary):**
   - Từ viết tắt chuyên ngành dầu khí, hàng hải, EPC, HSE, năng lượng tái tạo.
   - Tên cơ quan, đơn vị, phòng ban, phân xưởng, chức danh, dự án theo chuẩn PTSC.
   - Các biến thể viết sai thường gặp (typos, sai định dạng hoa/thường).
2. **Hỗ trợ Agent AI (Agent Grounding & Anti-Hallucination):**
   - Tiền xử lý (Pre-scan): Bắt nhanh lỗi từ điển tĩnh mà không tốn token LLM.
   - Glossary Injection: Bơm định nghĩa chuẩn vào System Prompt cho LLM.
   - Whitelist Guard: Bảo vệ các từ đặc thù nội bộ không bị LLM sửa bậy.
3. **Mở rộng kiểm tra Quy trình & Thể thức (Future Roadmap):**
   - Kiểm tra thể thức văn bản hành chính theo Nghị định 30.
   - Đối soát tuân thủ các bước quy trình phê duyệt / mua sắm / an toàn.

---

## 2. Thiết kế Kiến trúc Module (`PAIP/core/rule_engine/`)

```text
PAIP/core/rule_engine/
├── __init__.py
├── engine.py                  # Class RuleEngine (Điều phối toàn bộ Pipeline)
├── base.py                    # BaseRule (Abstract Base Class), RuleResult, Severity Enum
├── context.py                 # RuleContext (Text, metadata tài liệu, phòng ban, user role)
│
├── rules/                     # Tập hợp các Rules độc lập (Plug-and-Play)
│   ├── __init__.py
│   ├── glossary_rule.py       # [Level 1] Soát từ điển, viết tắt, danh từ riêng PTSC
│   ├── format_rule.py         # [Level 2] Soát thể thức văn bản hành chính & mẫu chuẩn
│   └── process_rule.py        # [Level 3] Soát quy trình & logic nghiệp vụ (LLM Hybrid)
│
├── loaders/                   # Bộ nạp dữ liệu cấu hình
│   ├── __init__.py
│   ├── base_loader.py         # Interface cho các Loader
│   ├── json_loader.py         # Nạp từ file JSON/YAML
│   └── excel_loader.py        # Nạp & xuất file Excel (.xlsx)
│
└── data/                      # Kho dữ liệu chuẩn (Config-driven)
    ├── glossary.json          # Danh mục từ vựng, viết tắt, tên đơn vị/dự án
    ├── format_specs.json      # Quy chuẩn thể thức tờ trình, thông báo, quyết định
    └── workflows.json         # Quy trình mẫu: Mua sắm, Đấu thầu, HSE, Phê duyệt
```

---

## 3. Luồng Xử Lý Tích Hợp (Integration Pipeline)

```
[ Input Document / Request ]
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. RuleContext Creation                                     │
│    • Đóng gói text, loại văn bản, phòng ban                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. RuleEngine Pre-Scan (Fast Pass)                          │
│    • Chạy GlossaryRule (Trie / Regex matcher)               │
│    • Thu thập lỗi từ điển trực tiếp (< 10ms)                │
│    • Trích xuất danh sách thuật ngữ xuất hiện trong bài     │
└─────────────────────────────┬───────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
  [ Danh sách lỗi từ điển ]         [ Prompt Context đã được nạp ]
  (100% chính xác, 0đ LLM)          [ định nghĩa thuật ngữ PTSC  ]
               │                             │
               │                             ▼
               │            ┌────────────────────────────────┐
               │            │ 3. LLM Inference (AI Xử lý)    │
               │            │    • Soát lỗi ngữ pháp, hành   │
               │            │      văn phức tạp              │
               │            │    • Không bị ảo giác thuật ngữ│
               │            └────────────────┬───────────────┘
               │                             │
               │                             ▼
               │                   [ Danh sách lỗi do AI ]
               │                             │
               └──────────────┬──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Result Merge & Deduplication                             │
│    • Gộp kết quả Rule Engine + LLM                          │
│    • Rule nội bộ luôn có quyền ưu tiên cao nhất             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
[ Output: Structured Compliance / Proofread Response ]
```

---

## 4. Đặc tả Cấu trúc Dữ liệu (Schemas)

### 4.1. Glossary Item Schema (`glossary.json`)
```json
{
  "FPSO": {
    "term": "FPSO",
    "full_name_en": "Floating Production Storage and Offloading",
    "full_name_vi": "Kho nổi chứa, xử lý và xuất dầu thô",
    "domain": "Offshore",
    "standard_case": "FPSO",
    "incorrect_variants": ["fpso", "Fpso", "F.P.S.O"],
    "synonyms": ["kho nổi chứa xuất dầu", "tàu FPSO"],
    "do_not_translate": true,
    "description": "Tàu/kho nổi chuyên dụng trong khai thác dầu khí ngoài khơi."
  }
}
```

### 4.2. Rule Result Output Schema
```json
{
  "rule_id": "GLOSSARY_VARIANT_MISMATCH",
  "rule_type": "glossary",
  "severity": "ERROR",
  "term": "PTSC-QNg",
  "suggested_fix": "PTSC QNG",
  "position": {
    "start_char": 45,
    "end_char": 53,
    "line": 3
  },
  "explanation": "Tên đơn vị viết sai quy chuẩn nhận diện thương hiệu PTSC QNG."
}
```

---

## 5. Thiết kế Giao diện & Quản trị (UI/UX)

1. **Admin Management Dashboard:**
   - Bảng hiển thị danh mục thuật ngữ (Search, Filter by Domain).
   - Nút **Import Excel (.xlsx)** và **Export Excel**.
   - Bật / Tắt từng bộ Rule.
2. **Crowdsourced Suggestion Flow (End-user):**
   - Nút tương tác nhanh *"Đề xuất từ mới vào Từ điển"* khi người dùng phát hiện thuật ngữ chưa có trong hệ thống.
   - Hàng đợi `Pending Approval` dành cho Admin phê duyệt trước khi kích hoạt.
