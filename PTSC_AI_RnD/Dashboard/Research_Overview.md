# 🏠 Research Overview

> Trang tổng quan — mở đầu tiên mỗi khi vào vault.

## 📊 Snapshot

| Metric      | Số lượng                                                                            |
| ----------- | ----------------------------------------------------------------------------------- |
| Pain Points | `$= dv.pages('"Discovery/Pain_Points"').where(p => p.type == "pain_point").length`  |
| POCs        | `$= dv.pages('"Lab&Research/POC"').where(p => p.type == "poc").length`              |
| Agents      | `$= dv.pages('"Architecture/Agent_Catalog"').where(p => p.type == "agent").length`  |
| Tech Notes  | `$= dv.pages('"Lab&Research/Tech_Notes"').where(p => p.type == "tech_note").length` |
| Prompts     | `$= dv.pages('"Lab&Research/Prompts"').where(p => p.type == "prompt").length`       |

---

## 🔥 Pain Points cần giải quyết gấp

```dataview
TABLE 
  department AS "Phòng ban",
  time_wasted_hours AS "Giờ/Tuần",
  status AS "Trạng thái"
FROM "Discovery/Pain_Points"
WHERE type = "pain_point" AND impact_level = "High"
SORT time_wasted_hours DESC
LIMIT 5
```

## 🧪 POCs gần đây

```dataview
TABLE
  status AS "Trạng thái",
  model_used AS "Model"
FROM "Lab&Research/POC"
WHERE type = "poc"
SORT date_created DESC
LIMIT 5
```

## 🤖 Agent Roadmap

```dataview
TABLE
  status AS "Trạng thái",
  difficulty AS "Độ khó"
FROM "Architecture/Agent_Catalog"
WHERE type = "agent"
SORT agent_id ASC
```

---

## 🔗 Quick Links

- [[Pain_Point_Heatmap|📍 Pain Point Heatmap]]
- [[POC_Tracker|🧪 POC Tracker]]
- [[Agent_Progress|🤖 Agent Progress]]
- [[AI_Opportunity_Matrix|📊 Opportunity Matrix]]
- [[PAIP_Architecture|🏛️ Kiến trúc PAIP]]
- [[Roadmap|🗺️ Roadmap]]
