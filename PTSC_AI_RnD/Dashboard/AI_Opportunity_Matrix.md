```dataview
TABLE 
  department AS "Phòng ban", 
  frequency AS "Tần suất", 
  time_wasted_hours AS "Giờ lãng phí (Tuần)", 
  impact_level AS "Mức độ ảnh hưởng", 
  status AS "Trạng thái"
FROM "Discovery/Pain_Points"
WHERE type = "pain_point"
SORT time_wasted_hours DESC
```

