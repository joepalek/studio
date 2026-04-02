# Coordinator Agent Architecture

**Status**: ARCHITECTURE PHASE (Pre-build)  
**Purpose**: Central inventory, audit, and optimization of all scraping/data-gathering operations  
**Build Sequence**: Architecture → Phase 1-5 implementation

---

## System Position

```
Supervisor (orchestrates agents, greenlighs tasks)
    ↓
Coordinator Agent ← queries all active scrapes
    ├→ scrape-registry.json (inventory + metadata)
    ├→ scrape-audit-daily.json (health + gaps)
    ├→ scrape-log.json (historical tracking)
    └→ coordinator-inbox.json (escalations to Supervisor)
    
Whiteboard Agent ← reads coordinator daily audit
    ↓
Your Inbox (flagged opportunities + fixes)
```

---

## Core Files

### 1. `scrape-registry.json`
**Source of truth**: All active and pending scrapes.

**Structure per scrape entry**:
```json
{
  "id": "unique_scrape_id",
  "agent_owner": "Agent_Name",
  "type": "scrape_category",
  "target_description": "What is being harvested",
  "frequency": "daily|weekly|monthly|manual",
  "status": "ACTIVE|PENDING_BUILD|PAUSED|FAILED",
  "cost_tier": "FREE|PAID|HYBRID",
  "provider": "API/service name",
  
  "schedule": {
    "last_run": "ISO8601_timestamp or null",
    "next_scheduled": "ISO8601_timestamp or null",
    "expected_interval_hours": number,
    "timezone": "UTC"
  },
  
  "output": {
    "file_location": "G:/My Drive/Projects/...",
    "format": "json|csv|txt",
    "schema": { "field": "type", "..." },
    "records_count": number,
    "size_mb": number,
    "last_modified": "ISO8601_timestamp"
  },
  
  "downstream_consumers": [
    { "project": "ProjectName", "usage": "how this feed is used" },
    ...
  ],
  
  "health": {
    "status": "HEALTHY|WARNING|FAILED",
    "last_check": "ISO8601_timestamp",
    "issues": ["issue_1", "issue_2"],
    "uptime_percent_7d": number
  },
  
  "optimization": {
    "suggested_improvements": ["suggestion_1", ...],
    "unused_potential": "description if any",
    "scaling_readiness": "ready_now|needs_prep|blocked_by"
  }
}
```

### 2. `scrape-audit-daily.json`
**Generated**: Every 6 AM UTC (or on-demand)

**Structure**:
```json
{
  "audit_date": "YYYY-MM-DD",
  "audit_timestamp": "ISO8601",
  "summary": {
    "total_scrapes_active": number,
    "healthy": number,
    "warnings": number,
    "failures": number,
    "total_data_volume_gb": number,
    "free_quota_consumed_percent": number,
    "paid_spend_today": "$X.XX"
  },
  "anomalies": [
    {
      "scrape_id": "id",
      "type": "STALE|MISSING|SCHEMA_ERROR|QUOTA_EXCEEDED|RATE_LIMIT",
      "detected_at": "ISO8601",
      "severity": "INFO|WARNING|CRITICAL",
      "details": "description",
      "suggested_action": "description",
      "escalation_level": "AUTO_FIX|SUPERVISOR_REVIEW|HUMAN_DECISION"
    },
    ...
  ],
  "opportunities": [
    {
      "opportunity_type": "NEW_SCRAPE|EXPAND_EXISTING|DECOMMISSION|CONSOLIDATE",
      "suggested_scrape_id": "id_or_null",
      "description": "description",
      "feeds_projects": ["Project1", "Project2"],
      "estimated_effort": "LOW|MEDIUM|HIGH",
      "estimated_value": "LOW|MEDIUM|HIGH",
      "priority_score": 1-10,
      "approval_status": "PENDING_SUPERVISOR|APPROVED|REJECTED"
    },
    ...
  ],
  "efficiency_notes": ["gain_1", "gain_2", ...]
}
```

### 3. `scrape-log.json`
**Historical record**: Every run, every scrape logs results.

**Structure**:
```json
{
  "entries": [
    {
      "timestamp": "ISO8601",
      "scrape_id": "id",
      "run_status": "SUCCESS|PARTIAL|FAILED",
      "records_retrieved": number,
      "records_new": number,
      "duration_seconds": number,
      "data_size_mb": number,
      "errors": ["error_1", ...],
      "notes": "free-form"
    },
    ...
  ]
}
```

### 4. `coordinator-inbox.json`
**Real-time escalations**: High-priority items for Supervisor review.

**Structure**:
```json
{
  "entries": [
    {
      "id": "unique_id",
      "timestamp": "ISO8601",
      "scrape_id": "related_scrape_or_null",
      "message_type": "CRITICAL_FAILURE|OPTIMIZATION_SUGGESTED|NEW_OPPORTUNITY|QUOTA_WARNING",
      "message": "free-form description",
      "proposed_action": "description",
      "urgency": "NOW|TODAY|THIS_WEEK",
      "requires_approval": boolean,
      "approved": boolean,
      "approval_timestamp": "ISO8601_or_null"
    },
    ...
  ]
}
```

---

## Coordinator Core Loop

**Runs at**:
- **6 AM UTC** (daily audit)
- **On every scrape completion** (real-time health check)
- **On demand** (triggered by Supervisor or Whiteboard)

**Pseudocode**:
```python
def coordinator_audit_cycle():
    # 1. LOAD CURRENT STATE
    registry = load_json('scrape-registry.json')
    previous_audit = load_json('scrape-audit-daily.json')
    
    # 2. CHECK EACH SCRAPE
    anomalies = []
    for scrape in registry.scrapes:
        health = check_scrape_health(scrape)
        if health.has_issues:
            anomalies.append(health.issue)
        update_registry_entry(scrape, health)
    
    # 3. DETECT GAPS & OPPORTUNITIES
    opportunities = []
    
    # 3a. Scrapes not scheduled (pending builds)
    pending = [s for s in registry.scrapes if s.status == 'PENDING_BUILD']
    for s in pending:
        if s.has_high_downstream_value:
            opportunities.append({
                'type': 'NEW_SCRAPE',
                'scrape_id': s.id,
                'reason': 'High-value pending build'
            })
    
    # 3b. Downstream usage patterns
    low_usage = [s for s in registry.scrapes if usage_percent(s) < 5]
    for s in low_usage:
        opportunities.append({
            'type': 'DECOMMISSION',
            'scrape_id': s.id,
            'reason': f'Only {usage_percent(s)}% downstream usage'
        })
    
    # 3c. Whiteboard new scrape requests
    whiteboard = load_json('whiteboard.json')
    new_scrape_ideas = [i for i in whiteboard.ideas if 'NEW_SCRAPE' in i.tags]
    for idea in new_scrape_ideas:
        opportunities.append({
            'type': 'NEW_SCRAPE',
            'suggested_target': idea.description,
            'reason': f'Whiteboard scored {idea.score}/10'
        })
    
    # 4. ESCALATE CRITICAL ISSUES
    for anomaly in anomalies:
        if anomaly.severity == 'CRITICAL':
            escalate_to_supervisor(anomaly)
    
    # 5. GENERATE AUDIT REPORT
    audit = {
        'audit_date': today(),
        'summary': {
            'total_scrapes_active': len([s for s in registry.scrapes if s.status == 'ACTIVE']),
            'healthy': len([a for a in anomalies if a.severity == 'INFO']),
            'warnings': len([a for a in anomalies if a.severity == 'WARNING']),
            'failures': len([a for a in anomalies if a.severity == 'CRITICAL']),
            ...
        },
        'anomalies': anomalies,
        'opportunities': opportunities
    }
    save_json('scrape-audit-daily.json', audit)
    
    # 6. LOG RUN
    log_coordinator_run(audit)
```

---

## Phase Breakdown

### Phase 1: Core Infrastructure (2 hours)
- Create `scrape-registry.json` with all current scrapes documented
- Create `coordinator-inbox.json` (initially empty)
- Build `coordinator.py` core loop (health check, registry update)
- Hook into Task Scheduler: runs 6 AM UTC daily

**Deliverable**: `scrape-registry.json` with 12+ entries, all scrapes inventoried

---

### Phase 2: Audit & Anomaly Detection (2 hours)
- Implement health check logic (file recency, schema validation, record count trending)
- Build `scrape-audit-daily.json` generator
- Detect: stale data, missing files, schema errors, quota exceeded
- Escalate CRITICAL anomalies to `coordinator-inbox.json`

**Deliverable**: First audit report shows health status + detected issues

---

### Phase 3: Opportunity Detection & Suggestions (1 hour)
- Analyze downstream consumer usage per scrape
- Flag unused scrapes for decommission
- Identify pending builds with high value (Game Archaeology, etc.)
- Integrate Whiteboard idea scanning

**Deliverable**: Audit report includes optimization suggestions + new opportunities

---

### Phase 4: Game Archaeology Build (4-6 hours)
- Implement Game_Archaeology_Agent
- Wayback CDX queries for abandonware sites, game databases
- Copyright/license status validation
- Output schema: game title, release date, platform, archive location, license_status
- First batch: 50-100 game candidates

**Deliverable**: `game-archaeology-results.json` with initial harvest

---

### Phase 5: Supervisor Integration (2 hours)
- Hook Coordinator → Supervisor inbox escalation
- Supervisor auto-approves LOW-risk fixes (schedule adjustments, new targets)
- Supervisor routes MEDIUM/HIGH-risk items to your inbox
- Coordinator autonomously implements approved fixes

**Deliverable**: Self-healing scrape system—fixes apply overnight without manual intervention

---

## Current Known Scrapes (To Be Inventoried)

### From Agent List & Memory:

| Scrape ID | Agent | Type | Target | Frequency | Status |
|---|---|---|---|---|---|
| wayback-c2c | AI_Intel_Agent | Wayback CDX | Coast to Coast AM (1998-2005) | weekly | ACTIVE |
| wayback-tech-forums | AI_Intel_Agent | Wayback CDX | Dead tech forums (Slashdot, Kuro5hin, Heise, 2ch) | weekly | ACTIVE |
| job-source-discovery | Job_Match_Agent | Common Crawl + Sitemap | Job posting URLs (global) | daily | ACTIVE |
| job-scrape-daily | Job_Match_Agent | HTTP scrape | Active job postings | daily | ACTIVE? |
| ai-intel-layer2 | AI_Intel_Agent | Multiple feeds | Tavily, YouTube, lab sitemaps, GitHub Trending | daily | ACTIVE? |
| foreign-ministry-japanese | Foreign_Ministry_Agent | 2ch scrape | Japanese forums/boards | weekly | PENDING_BUILD? |
| foreign-ministry-german | Foreign_Ministry_Agent | CCC/Heise | German tech/culture | weekly | PENDING_BUILD? |
| foreign-ministry-russian | Foreign_Ministry_Agent | Habr scrape | Russian tech forums | weekly | PENDING_BUILD? |
| ghost-book-validation | Ghost_Book_Agent | Wayback CDX | Archive for copyright validation | on-demand | ACTIVE |
| game-archaeology | Game_Archaeology_Agent | Wayback CDX | Abandonware/old game sites | weekly | **PENDING_BUILD** |
| ebay-agent | eBay_Agent | eBay API | Active listings, comps, pricing | daily | ACTIVE |
| market-scout | Market_Scout_Agent | HTTP + eBay API | Collectibles pricing trends | weekly | ACTIVE? |

**Status**: Partial inventory; needs full enumeration and scope definition.

---

## Next Steps

1. **You provide**: Complete list of all 16 agents + which ones perform scrapes
2. **You provide**: Job Match project specifics (scrape targets, frequency, output)
3. **We define**: Each scrape's:
   - Exact scope (what is being harvested)
   - Desired output schema
   - Frequency + timing
   - Which CX Agent workflows consume it
4. **We build**: Phase 1 Coordinator core with full registry

---

## Questions for Definition Phase

**For each scrape**:
- [ ] What exactly is being harvested? (be specific)
- [ ] What's the output schema? (fields, types, structure)
- [ ] How often should it run? (daily/weekly/monthly/triggered?)
- [ ] When should it run? (time of day, timezone)
- [ ] Where does output go? (file path)
- [ ] Which projects/agents consume it downstream?
- [ ] What assets does CX Agent create from it? (listings, posts, etc.)
- [ ] Is it free tier or paid? (which provider, quota limits)
- [ ] Any rate-limiting or auth requirements?
- [ ] How do we validate success? (minimum records, schema check, etc.)
