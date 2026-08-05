# 🧪 POC Tracker

## Tất cả POCs

```dataview
TABLE 
  status AS "Trạng thái",
  model_used AS "Model",
  complexity AS "Độ khó",
  cost_estimate_usd AS "Chi phí (USD)",
  roi_score AS "ROI Score",
  solves_pain_point AS "Pain Point"
FROM "Lab&Research/POC"
WHERE type = "poc"
SORT status ASC
```

## POCs đang chạy

```dataview
LIST
FROM "Lab&Research/POC"
WHERE type = "poc" AND status = "Testing"
```

## POCs đã hoàn thành

```dataview
LIST
FROM "Lab&Research/POC"
WHERE type = "poc" AND status = "Done"
```

## POCs theo Model

```dataview
TABLE 
  length(rows) AS "Số POCs"
FROM "Lab&Research/POC"
WHERE type = "poc"
GROUP BY model_used
```
