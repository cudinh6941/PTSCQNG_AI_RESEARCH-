# 🤖 Agent Progress

## Tiến độ tất cả Agents

```dataview
TABLE 
  agent_id AS "ID",
  difficulty AS "Độ khó",
  status AS "Trạng thái",
  estimated_weeks AS "Tuần (ước tính)",
  serves_department AS "Phòng ban",
  solo_feasible AS "Solo?"
FROM "Architecture/Agent_Catalog"
WHERE type = "agent"
SORT agent_id ASC
```

## Agents đang phát triển

```dataview
LIST
FROM "Architecture/Agent_Catalog"
WHERE type = "agent" AND (status = "In Progress" OR status = "Testing")
```

## Agents chờ bắt đầu

```dataview
LIST
FROM "Architecture/Agent_Catalog"
WHERE type = "agent" AND status = "Planning"
SORT priority ASC
```

## Liên kết Agent ↔ Pain Points

```dataview
TABLE
  linked_pain_points AS "Pain Points giải quyết",
  linked_pocs AS "POCs liên quan"
FROM "Architecture/Agent_Catalog"
WHERE type = "agent"
SORT agent_id ASC
```
