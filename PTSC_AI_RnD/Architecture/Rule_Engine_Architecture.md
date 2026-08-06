# 📐 PAIP — Rule Engine & Enterprise Glossary Architecture Specification

> **Version:** 1.0  
> **Status:** Approved Architecture / Ready for Implementation  
> **Category:** Core Capability / Shared Infrastructure  
> **Module Path:** `PAIP/core/rule_engine/`  
> **Documentation Link:** [[PAIP_Architecture]]

---

## 1. Tổng quan & Tầm nhìn (Executive Overview)

Trong hệ sinh thái AI doanh nghiệp của PTSC, việc chuẩn hóa thuật ngữ chuyên ngành (Dầu khí, EPC, Xây lắp biển, Cảng biển, HSE...) và kiểm soát tuân thủ quy trình nghiệp vụ là nền tảng cốt lõi.

**Rule Engine** là một module độc lập (Shared Core Infrastructure) được thiết kế theo mô hình **Hybrid (Quy tắc chính xác 100% + AI suy luận linh hoạt)** nhằm:
1. **Chuẩn hóa ngôn ngữ & Tránh ảo giác (Zero-Hallucination on Domain Terms):** Ngăn chặn LLM dịch sai, suy diễn sai hoặc bắt lỗi nhầm các thuật ngữ/từ viết tắt đặc thù PTSC.
2. **Tối ưu chi phí & Tốc độ (High Performance, Low Cost):** 80% các lỗi về từ vựng, thể thức được xử lý bằng CPU tĩnh (< 10ms, chi phí 0đ). Chỉ 20% logic phức tạp mới gọi đến LLM.
3. **Khả năng Scale-up thành Bộ kiểm soát quy trình (Process Compliance Engine):** Từ kho từ điển giai đoạn 1, hệ thống có thể mở rộng để kiểm tra thể thức văn bản (Nghị định 30) và tuân thủ các bước quy trình phê duyệt/đấu thầu/hợp đồng.

---

## 2. Kiến trúc Phân tầng 3 Cấp độ (3-Tier Rule Hierarchy)

```
                  ┌─────────────────────────────────────────────────────────┐
   Level 3        │   Semantic & Process Rules (LLM-as-a-Judge / Hybrid)    │
 (Nghiệp vụ & AI) │   • Tuân thủ bước quy trình phê duyệt / đấu thầu        │
                  │   • Kiểm tra thẩm quyền ký duyệt theo hạn mức tài chính │
                  ├─────────────────────────────────────────────────────────┤
   Level 2        │   Structural & Template Rules (AST / Section Parser)    │
 (Cấu trúc & Mẫu) │   • Thể thức văn bản hành chính (Nghị định 30)          │
                  │   • Kiểm tra các mục bắt buộc trong Tờ trình/Hợp đồng   │
                  ├─────────────────────────────────────────────────────────┤
   Level 1        │   Deterministic Rules (Aho-Corasick / Trie / Regex)     │
(Tĩnh / Siêu tốc) │   • Từ điển thuật ngữ chuẩn (Glossary) & Từ viết tắt    │
                  │   • Quy chuẩn viết hoa tên dự án / ban ngành nội bộ     │
                  └─────────────────────────────────────────────────────────┘
```

| Cấp độ | Tên gọi | Công nghệ | Thời gian xử lý | Chi phí LLM |
|---|---|---|---|---|
| **Level 1** | Deterministic / Glossary | Trie / Aho-Corasick / Regex | `< 5ms` | **0 token (0đ)** |
| **Level 2** | Structural / Format | Section Parser / RegEx Schema | `< 20ms` | **0 token (0đ)** |
| **Level 3** | Process & Business Logic | Few-shot Prompting + LLM Judge | `1 - 3s` | Tiết kiệm (chỉ gửi trích đoạn) |

---

## 3. Sơ đồ Luồng Tổng Thể (End-to-End Execution Flow)

```
[ Người dùng / Agent gửi Văn bản / Tài liệu ]
                      │
                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│  BƯỚC 1: RULE ENGINE PRE-PROCESSING (Xử lý sơ bộ bằng Luật tĩnh)      │
│  ────────────────────────────────────────────────────────────────────  │
│  1. Scan Dictionary/Glossary:                                          │
│     • Quét và bắt ngay các lỗi viết tắt sai, viết hoa sai quy chuẩn.   │
│     • Trích xuất danh sách thuật ngữ chuyên ngành có trong tài liệu.   │
│  2. Build Context & Guards:                                            │
│     • Whitelist: Danh sách từ chuẩn cấm LLM tự ý sửa/dịch.             │
│     • Glossary Injection: Bơm định nghĩa chuẩn vào Prompt LLM.         │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       [ Danh sách lỗi từ điển ]         [ Prompt Context đã được nạp ]
        (Chính xác 100%, 0đ LLM)         [ định nghĩa thuật ngữ PTSC  ]
                    │                             │
                    │                             ▼
                    │            ┌───────────────────────────────────────┐
                    │            │ BƯỚC 2: LLM INFERENCE (AI Xử lý)      │
                    │            │ ───────────────────────────────────── │
                    │            │ • LLM chỉ tập trung vào ngữ cảnh khó: │
                    │            │   Ngữ pháp, hành văn, logic lập luận. │
                    │            │ • KHÔNG bắt lỗi nhầm từ chuyên ngành  │
                    │            │   (nhờ Whitelist & Glossary context). │
                    │            └──────────────────┬────────────────────┘
                    │                               │
                    │                               ▼
                    │                     [ Danh sách lỗi do AI tìm ]
                    │                               │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  BƯỚC 3: POST-PROCESSING & MERGE (Hợp nhất kết quả)                    │
│  ────────────────────────────────────────────────────────────────────  │
│  • Gộp kết quả: [Lỗi Rule Engine Level 1] + [Lỗi LLM].                 │
│  • Khử trùng lặp (Deduplication) & Trọng số ưu tiên:                   │
│    (Quy tắc nội bộ luôn có quyền ưu tiên cao nhất nếu có xung đột).    │
│  • Đóng gói ComplianceReport chuẩn cấu trúc JSON.                      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
[ Trả về Kết quả Hoàn chỉnh cho Client / Agent ]
```

---

## 4. Cấu trúc Thư mục Module (`core/rule_engine/`)

```text
PAIP/core/rule_engine/
├── __init__.py
├── engine.py                  # RuleEngine điều phối thực thi Pipeline
├── base.py                    # BaseRule (Abstract), RuleResult, Severity (ERROR, WARNING, INFO)
├── context.py                 # RuleContext (chứa text, metadata văn bản, phòng ban, role)
│
├── rules/                     # Các module rule độc lập (Plug-and-Play)
│   ├── __init__.py
│   ├── glossary_rule.py       # [Level 1] Soát từ điển, viết tắt, danh từ riêng PTSC
│   ├── format_rule.py         # [Level 2] Soát thể thức văn bản hành chính & mẫu chuẩn
│   └── process_rule.py        # [Level 3] Soát quy trình & logic nghiệp vụ (LLM Hybrid)
│
├── loaders/                   # Quản lý đọc & đồng bộ dữ liệu quy tắc
│   ├── __init__.py
│   ├── base_loader.py         # BaseLoader interface
│   ├── json_loader.py         # Đọc từ file JSON/YAML cấu hình
│   └── excel_loader.py        # Import/Export từ file Excel (.xlsx)
│
└── data/                      # Kho dữ liệu chuẩn (Config-driven)
    ├── glossary.json          # Danh mục từ vựng, viết tắt, tên đơn vị/dự án
    ├── format_specs.json      # Quy chuẩn thể thức tờ trình, thông báo, quyết định
    └── workflows.json         # Quy trình mẫu: Mua sắm, Đấu thầu, HSE, Phê duyệt
```

---

## 5. Cấu trúc Dữ liệu Chuẩn (Data Schemas)

### 5.1. Schema Từ điển (`glossary.json`)
```json
{
  "FPSO": {
    "term": "FPSO",
    "full_name_en": "Floating Production Storage and Offloading",
    "full_name_vi": "Kho nổi chứa, xử lý và xuất dầu thô",
    "domain": "Offshore / Oil & Gas",
    "standard_case": "FPSO",
    "incorrect_variants": ["fpso", "Fpso", "F.P.S.O", "kho fpso"],
    "synonyms": ["kho nổi chứa xuất dầu", "tàu FPSO"],
    "do_not_translate": true,
    "description": "Tàu/kho nổi chuyên dụng trong khai thác dầu khí ngoài khơi."
  },
  "PTSC QNG": {
    "term": "PTSC QNG",
    "full_name_vi": "Công ty Cổ phần Dịch vụ Dầu khí Quảng Ngãi PTSC",
    "domain": "Corporate",
    "standard_case": "PTSC QNG",
    "incorrect_variants": ["PTSC-QNg", "PTSC QNg", "ptsc qng", "PTSC Quảng Ngãi"],
    "do_not_translate": true,
    "description": "Tên viết tắt chuẩn của đơn vị theo Quy chế nhận diện thương hiệu."
  }
}
```

### 5.2. Schema Quy trình Nghiệp vụ (`workflows.json` - Dùng cho Scale-up)
```json
{
  "procurement_under_100m": {
    "workflow_id": "WF_PROC_01",
    "name": "Quy trình mua sắm chỉ định thầu dưới 100 triệu",
    "department": "Procurement",
    "mandatory_documents": [
      "Phiếu yêu cầu mua sắm",
      "Tối thiểu 02 báo giá cạnh tranh",
      "Biên bản thương thảo giá",
      "Tờ trình phê duyệt kết quả mua sắm"
    ],
    "approver_authority": "Giám đốc đơn vị / Trưởng phòng ủy quyền",
    "max_amount_vnd": 100000000
  }
}
```

---

## 6. Chiến lược Quản trị & Giao diện (UI/UX & Governance)

```
                       ┌──────────────────────────────────────┐
                       │           ADMIN DASHBOARD            │
                       │  • Quản lý Bảng Từ điển (CRUD)       │
                       │  • [IMPORT EXCEL] / [EXPORT EXCEL]   │
                       │  • Bật/Tắt Rule & Chọn Severity      │
                       │  • Phê duyệt từ chờ duyệt (Approve)  │
                       └──────────────────▲───────────────────┘
                                          │ Phê duyệt (Approve / Reject)
                                          │
                       ┌──────────────────┴───────────────────┐
                       │          END-USER WORKSPACE          │
                       │  • Proofreading / Chat / RAG         │
                       │  • Nút: [💡 Đề xuất thêm từ mới]     │
                       └──────────────────────────────────────┘
```

1. **Admin Dashboard (Quản trị tập trung):**
   * Cho phép Quản trị viên / Ban Tiêu chuẩn Thêm/Sửa/Xóa từ vựng, quy tắc.
   * **Nút Import / Export Excel (.xlsx):** Giúp nạp hàng nghìn thuật ngữ từ tài liệu sẵn có mà không cần gõ tay.
   * Công tắc Bật/Tắt (Toggle) và tùy chỉnh mức độ cảnh báo (`ERROR` vs `WARNING`).
2. **Crowdsourced Suggestion Flow (Người dùng đóng góp):**
   * Khi nhân viên sử dụng hệ thống và phát hiện từ mới chuyên môn, bấm nút *"Đề xuất thêm từ này"*.
   * Đề xuất rơi vào hàng đợi `Pending`. Sau khi được Admin duyệt, từ mới sẽ lập tức đồng bộ vào toàn hệ thống.

---

## 7. Lộ trình Triển khai (Roadmap)

* [ ] **Phase 1: Foundation (Kho Từ điển & Core Engine)**
  * Xây dựng `core/rule_engine/engine.py`, `base.py`, `context.py`.
  * Xây dựng `glossary_rule.py` (Aho-Corasick/Regex) + `json_loader.py` nạp file `glossary.json`.
  * Tích hợp vào `Agent_0_Proofreader` (Pre-scan + Whitelist + Glossary Injection + Result Merge).
* [ ] **Phase 2: Management & Import UI**
  * Xây dựng API CRUD `/api/v1/rules/dictionary` và endpoint `/import-excel`.
  * Xây dựng giao diện Web Admin quản lý từ điển & nút đề xuất từ phía End-user.
* [ ] **Phase 3: Structural & Process Expansion**
  * Xây dựng `format_rule.py` kiểm tra mẫu văn bản hành chính (Nghị định 30).
  * Xây dựng `process_rule.py` đối soát quy trình nghiệp vụ chuyên sâu.
