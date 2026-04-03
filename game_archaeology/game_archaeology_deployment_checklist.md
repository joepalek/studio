# Game Archaeology: Quick Deployment Checklist

## Files to Deploy

Place these in: `G:\My Drive\Projects\_studio\game_archaeology\`

```
game_archaeology/
├── game_archive_crawler_expanded.py          (NEW)
├── game_archaeology_legal_agent.py           (EXISTING - UPDATE logging)
├── game_archaeology_orchestrator_updated.py  (NEW)
├── supabase_config.py                        (NEW)
└── run_orchestrator.py                       (NEW - Task Scheduler entry point)
```

---

## Pre-Flight Checks

### ✅ Studio Config Already Has Supabase Keys
Your `studio-config.json` should contain:
```json
{
  "supabase_url": "https://nepnytazalthnjqpyzcx.supabase.co",
  "supabase_anon_key": "eyJhbGc...",
  "supabase_service_role_key": "eyJhbGc..."
}
```

**Verify it exists:**
```powershell
Test-Path "G:\My Drive\Projects\_studio\studio-config.json"
# Should return: True
```

### ✅ Install Supabase SDK
```bash
pip install supabase --break-system-packages
```

### ✅ Supabase Tables Already Created
Tables in your Supabase project (created earlier):
- `game_candidates`
- `game_assessments`
- `game_reviews`
- `cx_queue`
- `cx_completions`

---

## Quick Test (Before Task Scheduler)

```bash
cd "G:\My Drive\Projects\_studio\game_archaeology"

# Test Supabase connection
python supabase_config.py

# Expected output:
# ✓ Supabase client initialized
# ✓ Connection successful
# ✓ game_candidates
# ✓ game_assessments
# ✓ cx_queue
# ✓ cx_completions
```

If errors, check:
1. studio-config.json exists and has valid JSON
2. supabase_url and supabase_anon_key fields present
3. Supabase project is active (not archived)

---

## Full Pipeline Test

```bash
python run_orchestrator.py

# Expected output:
# =============================================
# Game Archaeology Daily Cycle
# Started: 2026-04-03T...
# =============================================
#
# [INFO] DAILY GAME ARCHAEOLOGY CYCLE
# [INFO] STEP 1: System Health Check
# [INFO]   CPU: 45.3%
# [INFO] STEP 2: Archive Crawl
# [INFO]   ✓ Found 31 new games
# [INFO] STEP 3: Legal Assessment
# [INFO]   ✓ Assessed 31 games: 12 GREEN/YELLOW
#
# =============================================
# EXECUTION SUMMARY
# =============================================
# Status: SUCCESS
#   Games found: 31
#   Games inserted: 31
#   Games assessed: 12
#   Duration: 35.2s
# =============================================
```

---

## Verify Supabase Data

After running the test:

1. Go to: https://app.supabase.com/project/nepnytazalthnjqpyzcx/editor
2. Click on `game_candidates` table
3. Should see **31 new rows** from the crawl
4. Click on `game_assessments` table
5. Should see **12 rows** (GREEN + YELLOW only, RED filtered out)

---

## Set Up Task Scheduler

### Create Daily 2:00 AM UTC Task

1. **Open Task Scheduler** (Windows)
2. **Create Basic Task:**
   - Name: `Game Archaeology Daily Cycle`
   - Trigger: Daily, 2:00 AM (UTC)
   
3. **Set Action:**
   - Program/script: `python`
   - Add arguments: `G:\My Drive\Projects\_studio\game_archaeology\run_orchestrator.py`
   - Start in: `G:\My Drive\Projects\_studio`

4. **Configure Settings:**
   - Run with highest privileges: ☑
   - If task is already running: Do not start new instance
   - Hidden: ☑ (optional)

5. **Click OK**

---

## Monitoring

### Check Daily Run Success

```powershell
# View Task Scheduler log
Get-EventLog -LogName "System" -Source TaskScheduler | Where-Object {$_.Message -like "*Game Archaeology*"} | Select-Object -First 5
```

### Quick Supabase Check

Query in Supabase console:
```sql
-- Count games found in past 24 hours
SELECT COUNT(*) FROM game_candidates 
WHERE created_at > NOW() - INTERVAL '1 day';

-- Count assessments (GREEN + YELLOW)
SELECT risk_level, COUNT(*) as count 
FROM game_assessments 
GROUP BY risk_level;
```

### Check Orchestrator Logs

Logs are written to `studio_core/logger` directory:
```bash
ls G:\My Drive\Projects\_studio\logs\GameArchaeology_Orchestrator*
```

---

## What Happens Daily

**2:00 AM UTC:**
1. Orchestrator checks system load
2. Runs Crawler: finds 30-40 games from 6 sources
3. Runs Legal Agent: assesses & filters GREEN+YELLOW
4. Pushes to Supabase: game_candidates + game_assessments
5. Logs completion to inbox

**Data grows:**
- `game_candidates`: +30-40 rows/day
- `game_assessments`: +12-20 rows/day (qualified games only)

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| "studio-config.json not found" | Path is correct? `Test-Path "G:\My Drive\Projects\_studio\studio-config.json"` |
| "Supabase not configured" | Check studio-config.json has `supabase_url` and `supabase_anon_key` |
| "Connection refused" | Supabase project active? Check: https://app.supabase.com/projects |
| Task Scheduler fails silently | Check Event Viewer logs (Task Scheduler category) |
| Fewer than 30 games found | Crawler sources may be rate-limited; will catch up next run |

---

## Success Metrics (First Week)

- [ ] Task runs at 2:00 AM UTC daily without errors
- [ ] game_candidates table grows by 30-40 rows/day
- [ ] game_assessments has 12-20 GREEN/YELLOW per day
- [ ] RED games correctly filtered (not in assessments table)
- [ ] Weekly digest ready Friday 5PM UTC (next step)

---

## Next Steps (Week 2+)

1. **Friday 5PM UTC:** Weekly digest generation
   - Aggregate all GREEN+YELLOW from past 7 days
   - Send digest email to you

2. **You review Friday digest:**
   - Pick 1-2 games to queue for CX production

3. **Monday 9AM UTC:** Queue games
   - Supervisor reads your decision
   - Inserts selected games into cx_queue

4. **On-demand:** CX Agent assignment
   - Assign PENDING games to CX Agent for conversion

---

## Questions?

- **Studio config not set up?** Let me know the exact keys in your config.json
- **Supabase tables missing?** They were auto-created earlier via SQL migration.
- **Want to test a specific game?** Run orchestrator with `force=True` flag.

