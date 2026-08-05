# 🔍 Pain Point Heatmap

## Tổng quan Pain Points theo phòng ban

```dataview
TABLE 
  department AS "Phòng ban", 
  frequency AS "Tần suất", 
  time_wasted_hours AS "Giờ lãng phí/Tuần", 
  impact_level AS "Mức ảnh hưởng",
  ai_solution_type AS "Loại AI",
  status AS "Trạng thái"
FROM "Discovery/Pain_Points"
WHERE type = "pain_point"
SORT impact_level DESC
```

## Pain Points chưa có giải pháp

```dataview
LIST
FROM "Discovery/Pain_Points"
WHERE type = "pain_point" AND (status = "Mới ghi nhận" OR !linked_poc)
SORT time_wasted_hours DESC
```

## Thống kê theo phòng ban

```dataview
TABLE 
  length(rows) AS "Số Pain Points"
FROM "Discovery/Pain_Points"
WHERE type = "pain_point"
GROUP BY department
SORT length(rows) DESC
```
