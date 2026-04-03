# CX Agent Input Spec: Game Archaeology Conversions

## Purpose
CX Agent receives a single game assignment from `cx_queue`, converts old game → new game artifact.

---

## Input Format (from cx_queue)

CX Agent receives this JSON payload when assigned a game:

```json
{
  "task_id": "cx_queue_001",
  "game_id": "game_001",
  "game_title": "Hellmaze",
  "source_url": "https://web.archive.org/web/20100101/example.com/hellmaze",
  "original_game_type": "Flash",
  "original_creator": "Unknown",
  "release_year": 2010,
  
  "legal_tier": "GREEN",
  "legal_confidence": 0.88,
  "transformation_requirements": {
    "visual_redesign_percent": 30,
    "mechanic_changes_required": "Core loop can stay same, enemy behavior/AI can change",
    "layout_flexibility": "Can keep room structure",
    "attribution_needed": true
  },
  "tier_recommendation": "TIER_1_RECORDING",
  "notes_for_user": "Safe to convert. 30% visual redesign recommended.",
  
  "instructions": {
    "output_format": "Playable HTML5 web game",
    "target_platforms": ["web"],
    "accessibility_requirements": ["WCAG 2.1 AA compliant"],
    "performance_target_fps": 60,
    "browser_compatibility": ["Chrome 90+", "Firefox 88+", "Safari 14+"]
  }
}
```

---

## Output Format (to cx_completions)

CX Agent records completion with:

```json
{
  "cx_queue_id": 1,
  "game_id": 1,
  "output_artifact_url": "https://studio.joepalek.com/games/hellmaze-2026/index.html",
  "output_game_file": "hellmaze-2026.zip",
  "conversion_hours": 18.5,
  "notes": "Converted from Flash to Phaser 3.55. Visual redesign 35% (exceeded spec by 5%). Core loop preserved. Testing passed.",
  "completion_date": "2026-04-05",
  "status": "COMPLETE"
}
```

---

## CX Agent Workflow

**Input Trigger:**
```
Supervisor checks cx_queue WHERE status='PENDING' ORDER BY priority_rank LIMIT 1
→ Assigns game to CX Agent
→ Updates cx_queue: status='IN_PROGRESS', assigned_to_cx_agent=true, started_date=NOW()
```

**CX Agent Actions:**
1. Receive assignment from Supervisor (via Supabase or inbox message)
2. Download/access original game from `source_url`
3. Plan transformation (visual redesign %, code salvage %, framework target)
4. Execute conversion (18-48 hours depending on tier)
5. Test & validate output
6. Upload artifact to studio deployment or GitHub
7. Record completion → INSERT into `cx_completions`
8. Update `cx_queue` → status='COMPLETE', completed_date=NOW()
9. Report to Supervisor inbox

**Error Handling:**
- If conversion blocked (source missing, unable to decompile, etc.)
- Update `cx_queue` → status='ERROR', add note
- Escalate to Supervisor inbox with error details

---

## Status Codes (cx_queue)

| Status | Meaning | Next Step |
|--------|---------|-----------|
| PENDING | Game in queue, awaiting assignment | Supervisor assigns to CX Agent |
| IN_PROGRESS | CX Agent actively converting | Wait for completion |
| COMPLETE | Conversion done, artifact ready | Track in cx_completions |
| ERROR | Conversion failed or blocked | Manual review required |

---

## Integration Points

**Supervisor → CX Agent:**
```python
# Pseudo-code: Daily check (or on-demand)
def assign_next_game_to_cx_agent():
    pending = supabase.table("cx_queue") \
        .select("*") \
        .eq("status", "PENDING") \
        .order("priority_rank") \
        .limit(1) \
        .execute()
    
    if pending.data:
        game_assignment = pending.data[0]
        cx_agent.inbox.add_item(
            agent_id="cx_agent",
            project_id="GameArchaeology",
            question=f"Convert {game_assignment['game_title']}",
            required_action=f"Execute conversion per spec: {game_assignment['tier_recommendation']}",
            urgency="HIGH",
            attachment=game_assignment  # Full game spec as JSON
        )
        supabase.table("cx_queue") \
            .update({"status": "IN_PROGRESS", "started_date": "now()"}) \
            .eq("id", game_assignment['id']) \
            .execute()
```

**CX Agent → Supervisor (Completion):**
```python
def report_completion(game_title, artifact_url, hours_spent, notes):
    # Record in cx_completions
    supabase.table("cx_completions").insert({
        "cx_queue_id": task_id,
        "game_id": game_id,
        "output_artifact_url": artifact_url,
        "conversion_hours": hours_spent,
        "notes": notes,
        "completion_date": "now()"
    }).execute()
    
    # Update cx_queue
    supabase.table("cx_queue") \
        .update({"status": "COMPLETE", "completed_date": "now()"}) \
        .eq("id", task_id) \
        .execute()
    
    # Report to Supervisor
    supervisor.inbox.add_item(
        agent_id="cx_agent",
        project_id="GameArchaeology",
        question=f"Completed: {game_title}",
        required_action=f"Review artifact and publish",
        urgency="MEDIUM",
        attachment={"artifact_url": artifact_url, "hours": hours_spent}
    )
```

---

## Tier Definitions (What CX Agent Receives)

### TIER_1_RECORDING
- Pure screen recording + replay of original game
- No code salvage
- Just visual modernization
- Output: HTML5 Canvas or Phaser (simple)
- **Effort:** 8-16 hours

### TIER_1_PLUS_2
- Visual modernization + partial code salvage
- Keep core engine, rewrite UI/rendering
- **Effort:** 24-40 hours

### TIER_2_SALVAGE
- Aggressive code reuse (60%+ salvage)
- Requires source code available
- Modernize framework/dependencies
- **Effort:** 40-60 hours

---

## Example Assignment (Full Context)

**Supervisor sends to CX Agent:**

```json
{
  "assignment_id": "cx_queue_001",
  "priority": 1,
  "game_info": {
    "id": 1,
    "title": "Hellmaze",
    "original_type": "Flash",
    "release_year": 2010,
    "source_url": "https://web.archive.org/web/20100101/hellmaze.swf"
  },
  "legal_clearance": {
    "tier": "GREEN",
    "confidence": 0.88,
    "reasoning": "16 years old, unknown creator, fair use applies"
  },
  "transformation_spec": {
    "tier": "TIER_1_RECORDING",
    "visual_redesign": "30%",
    "core_loop_preservation": "keep intact",
    "notes": "Safe conversion. Focus on visual modernization."
  },
  "output_requirements": {
    "format": "HTML5 game",
    "deployment": "https://studio.joepalek.com/games/hellmaze-2026/",
    "accessibility": "WCAG 2.1 AA",
    "fps_target": 60
  },
  "your_notes": "This is a solid candidate. Players loved the original. Estimate 16 hours."
}
```

---

## Questions for CX Agent

**Before you start:**
1. Can you access the source URL and retrieve the original game?
2. What framework/tools will you use for conversion?
3. What's your estimated effort based on tier and game complexity?
4. Any blockers before beginning?

**During conversion:**
- Report progress to Supervisor inbox (weekly status)
- Flag any blockers immediately

**On completion:**
- Test on target platforms (Chrome, Firefox, Safari)
- Validate accessibility (WCAG 2.1 AA)
- Record effort hours + notes
- Upload artifact URL to cx_completions

