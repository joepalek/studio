# CX Agent Integration Guide

## Overview
CX Agent is the quality gate and traffic cop for ALL agent-created assets. It:
1. **Receives** assets from all 16 creator agents (eBay, CTW, Ghost_Book, Jobs, etc.)
2. **Validates** format + quality + brand alignment
3. **Routes** to final destinations (eBay API, project folders, characters_final, job repository)
4. **Tracks usage** and feeds high-performers to social media for amplification

This guide shows how to integrate CX Agent into your existing studio infrastructure.

---

## Files Created

| File | Purpose | Location |
|------|---------|----------|
| `asset_distribution_manifest.json` | Routing rules for all creator agents | `/home/claude/` (copy to G: drive) |
| `CX_Agent_Validation_Protocol.md` | Operational playbook + grading rubric | `/home/claude/` (reference) |
| `asset_creation_log.json` | Master asset registry (lives in G: drive) | `G:/My Drive/studio_logs/` |
| `cx_agent.py` | Python implementation (scheduler-ready) | `/home/claude/` or `G:/My Drive/Projects/_studio/` |

---

## Step 1: Add CX Agent to CLAUDE.md Rules

In your **CLAUDE.md**, add this to the Behavioral Rules section:

```markdown
## CX Agent Rules (NEW)

### Kay Rule (Supervisor sends goals not scripts) + CX Extension
- Supervisor forwards **all creator agent outputs** to CX Agent inbox
- Creator agents emit structured JSON: `{asset_id, creator_agent, asset_type, content, metadata}`
- CX Agent does NOT receive implementation directives—only asset payloads
- CX Agent reads routing logic from `asset_distribution_manifest.json`

### CX Agent Daily Routine
1. **Receive** new assets from creators (poll or event-driven)
2. **Validate** format, quality (1-10), brand alignment
3. **Route** to destination per manifest
4. **Track** usage and feed social media intelligence
5. **Escalate** failures to Whiteboard (for manual review)
6. **Cull** expired jobs (daily, 2 AM UTC)

### Asset Emission Standard (All Creator Agents)
```json
{
  "asset_id": "unique_id_or_agent_timestamp",
  "creator_agent": "agent_name",
  "asset_type": "listing|character_file|script_draft|job_posting|...",
  "created_at": "ISO8601_timestamp",
  "project": "project_name",
  "content": { /* asset-specific fields */ },
  "metadata": { /* optional extra context */ }
}
```

### CX Agent Validation Thresholds
- **Pass:** format ✓ + quality ≥8 + brand ✓
- **Review:** format ✓ + quality 5-7 OR brand ✗
- **Reject:** format ✗ OR quality <5
```

---

## Step 2: Wire Supervisor to CX Agent

Add this to **Supervisor Agent** logic:

```python
# In Supervisor Agent loop:

def route_to_cx_agent(asset_payload):
    """
    Forward creator agent output to CX Agent.
    CX Agent returns routing decision + asset log entry.
    """
    cx_inbox = get_decision_inbox("cx_agent_queue")
    
    # Enqueue asset for CX Agent processing
    cx_inbox.append({
        "type": "asset_for_validation",
        "payload": asset_payload,
        "enqueued_at": datetime.utcnow().isoformat() + "Z",
        "priority": "normal"  # Can be "urgent" for time-sensitive assets
    })
    
    # Supervisor can optionally wait for CX Agent response
    # or fire-and-forget if assets are processed asynchronously
```

---

## Step 3: Schedule CX Agent Tasks

In **Windows Task Scheduler**, add these scheduled tasks:

### Task 1: Daily CX Agent Scan (2 AM UTC)
```
Program: python
Arguments: C:\path\to\cx_agent.py --mode daily_scan
Trigger: Daily at 02:00 UTC
Repeat: Every 24 hours
Log: C:\path\to\cx_agent.log
```

**This runs:**
- Culls expired jobs from repository
- Identifies high-performers for social media
- Generates `social_media_feed.json` for Social_Media_Agent

### Task 2: CX Agent Monitoring (Every Hour)
```
Program: python
Arguments: C:\path\to\cx_agent.py --mode monitor --hours 1
Trigger: Every 1 hour
Log: C:\path\to\cx_agent.log
```

**This runs:**
- Updates usage metrics for all active assets
- Flags underperformers for Whiteboard
- Polls eBay API for listing performance (views, CTR, etc.)

---

## Step 4: Integrate with Existing Projects

### For eBay Listing Agent
Modify emission to include:
```python
asset_payload = {
    "asset_id": f"ebay_listing_{timestamp}",
    "creator_agent": "eBay_Listing_Agent",
    "asset_type": "listing",
    "created_at": datetime.utcnow().isoformat() + "Z",
    "project": "eBay_Resale",
    "content": {  # Your listing JSON
        "title": "...",
        "price": ...,
        "condition": "...",
        # ... rest of listing fields
    },
    "metadata": {
        "sku": "...",
        "category": "...",
        "source": "HiBid", # etc
    }
}
# Send to CX Agent via Supervisor
route_to_cx_agent(asset_payload)
```

### For CTW Agent
Modify emission to include:
```python
asset_payload = {
    "asset_id": f"ctw_{asset_type}_{timestamp}",
    "creator_agent": "CTW_Agent",
    "asset_type": asset_type,  # "character_file", "script", "mp4", etc.
    "created_at": datetime.utcnow().isoformat() + "Z",
    "project": "CTW",
    "content": {
        "name": "...",
        "type": asset_type,
        # ... asset-specific fields
    },
    "metadata": {
        "creator": "CTW_Agent + Hunter (Blender)",
        "design_phase_duration": "...",
        # ...
    }
}
route_to_cx_agent(asset_payload)
```

### For Ghost_Book Agent
```python
asset_payload = {
    "asset_id": f"ghost_book_{asset_type}_{timestamp}",
    "creator_agent": "Ghost_Book_Agent",
    "asset_type": "script_draft|script_done|script_final",
    "created_at": datetime.utcnow().isoformat() + "Z",
    "project": "Ghost_Book",
    "content": {
        "title": "...",
        "status": "draft|done|final",
        "word_count": ...,
        "chapter_count": ...,
        # ...
    },
    "metadata": {
        "creator": "Ghost_Book_Agent",
        "source": "Estate clearing interviews",
        # ...
    }
}
route_to_cx_agent(asset_payload)
```

### For Jobs Agent
```python
asset_payload = {
    "asset_id": f"job_{timestamp}",
    "creator_agent": "Jobs_Agent",
    "asset_type": "job_posting",
    "created_at": datetime.utcnow().isoformat() + "Z",
    "project": "Job_Match",
    "content": {
        "title": "...",
        "description": "...",
        "location": "...",
        "salary_range": "...",
        # ...
    },
    "metadata": {
        "source": "job_board_scraper",
        # ...
    }
}
route_to_cx_agent(asset_payload)
```

---

## Step 5: Monitor CX Agent Output

### Check Asset Log
```bash
# View asset log in G: drive
G:/My Drive/studio_logs/asset_creation_log.json
```

### Check Social Media Feed
```bash
# CX Agent generates this daily (2 AM UTC)
social_media_feed.json
```

**Example output:**
```json
{
  "generated_at": "2026-03-29T02:00:00Z",
  "amplification_candidates": [
    {
      "asset_id": "ebay_listing_20260329_001",
      "asset_type": "listing",
      "quality_score": 9,
      "metrics": {
        "impressions": 342,
        "click_through_rate": "5.2%"
      },
      "creator_agent": "eBay_Listing_Agent"
    },
    { ... }
  ]
}
```

Feed this to **Social_Media_Agent** for amplification decisions.

### Check CX Agent Log
```bash
# Real-time log
tail -f cx_agent.log
```

---

## Step 6: Whiteboard Escalation Protocol

When CX Agent routes an asset to "whiteboard" (validation fails):

1. **Auto-entry created** in Decisions inbox:
   ```
   [ASSET_REVIEW] {asset_id} - {failure_reason}
   Content: asset_data, validation_feedback, CX_Agent_recommendation
   ```

2. **Creator agent** reviews feedback and revises

3. **Re-submit** asset to CX Agent (gets new `asset_id`)

4. **CX Agent** re-validates and routes or escalates again

---

## Step 7: Update State.json

Add CX Agent status to your **state.json** project status:

```json
{
  "projects": {
    "studio_core": {
      "status": "operational",
      "agents": {
        "CX_Agent": {
          "status": "active",
          "last_scan": "2026-03-29T02:00:00Z",
          "assets_processed_today": 4,
          "assets_passing": 4,
          "assets_review": 0,
          "assets_rejected": 0,
          "amplification_candidates": 3,
          "jobs_culled_today": 2,
          "heartbeat": "healthy"
        }
      }
    }
  }
}
```

---

## Example: Full Asset Flow

Here's what happens when eBay_Listing_Agent creates a new listing:

```
1. eBay_Listing_Agent generates listing JSON
   └─> Emits: asset_payload (asset_distribution_manifest format)

2. Supervisor receives payload
   └─> Enqueues to CX_Agent_inbox

3. CX_Agent picks up asset
   └─> Validates format ✓
   └─> Scores quality (1-10) → 9
   └─> Checks brand alignment ✓
   └─> overall_status = "pass"

4. CX_Agent routes (per manifest)
   └─> destination: eBay API
   └─> method: POST /v1/item/upload
   └─> response: 201 (success)

5. CX_Agent logs to asset_creation_log.json
   └─> Adds entry with validation, routing, usage_tracking fields

6. CX_Agent monitors usage (hourly)
   └─> Polls eBay for impressions, CTR, engagement
   └─> quality_score 9 + CTR 5.2% = "amplification_candidate"

7. Daily scan (2 AM) identifies high-performers
   └─> Writes to social_media_feed.json
   └─> Social_Media_Agent picks up and creates Twitter/Instagram posts

8. Social media amplification → more impressions → asset becomes "trending"
   └─> CX_Agent flags for additional amplification
   └─> Community sees asset on multiple channels
```

---

## Testing Checklist

- [ ] Manifest JSON loads without errors
- [ ] `cx_agent.py --mode daily_scan` runs and completes
- [ ] asset_creation_log.json updates after each scan
- [ ] social_media_feed.json is generated correctly
- [ ] Whiteboard escalation creates decision entries
- [ ] Job culling removes expired postings (30+ days old)
- [ ] Creator agents emit JSON in correct format
- [ ] Supervisor successfully routes to CX Agent
- [ ] Windows Task Scheduler tasks run on schedule
- [ ] Google Drive sync keeps asset_creation_log.json current

---

## Troubleshooting

### Issue: Assets not validating
- Check `format_check` in asset_creation_log.json
- Ensure creator agents emit required fields per asset type
- Validate JSON schema against manifest

### Issue: Wrong routing destination
- Verify creator agent name matches manifest entry
- Check asset_type in content object
- Ensure manifest routing rules are correct

### Issue: Jobs not being culled
- Check Windows Task Scheduler "Daily CX Agent Scan" is running
- Verify job creation dates are correct (ISO 8601 format)
- Check cx_agent.log for cull output

### Issue: Social media feed not generated
- Verify `asset_creation_log.json` has entries with quality_score ≥8
- Check cx_agent.py has permission to write social_media_feed.json
- Check daily scan is running (2 AM UTC)

---

## Next Steps

1. **Copy files to G: drive:**
   ```
   asset_distribution_manifest.json → G:/My Drive/studio_logs/
   asset_creation_log.json → G:/My Drive/studio_logs/
   cx_agent.py → G:/My Drive/Projects/_studio/
   ```

2. **Set up Windows Task Scheduler tasks** (see Step 3)

3. **Update creator agents** to emit correct JSON format (see Step 4)

4. **Update Supervisor** to route to CX Agent (see Step 2)

5. **Update CLAUDE.md** with CX Agent rules (see Step 1)

6. **Test** with sample assets (use examples in asset_creation_log.json)

7. **Monitor** logs and feed for 1 week to validate system is working

---

**Contact:** Joe Palek | Last Updated: 2026-03-29
