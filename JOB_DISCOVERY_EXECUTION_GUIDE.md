# Job Source Discovery - EXECUTION GUIDE
## Phase 1 Launcher Ready for Tonight

**Status**: ✅ ALL FILES READY TO DEPLOY  
**Deploy Date**: 2026-04-02  
**Start Time**: Tonight (immediately or 06:00 UTC scheduled)

---

## FILES CREATED

### Core Execution
- `job-source-discovery-launcher.py` (237 lines)
  - Phase 1 discovery orchestrator
  - Runs all 5 discovery methods sequentially
  - Outputs: job-source-registry.json, blocking-investigation.json
  - Location: `G:\My Drive\Projects\_studio\`

### Scheduling & Automation
- `job-source-discovery-scheduler.bat` (28 lines)
  - Task Scheduler wrapper for Python script
  - Logs all runs with timestamp
  - Location: `G:\My Drive\Projects\_studio\`

- `register-job-discovery-task.ps1` (59 lines)
  - PowerShell registration script (run once as Admin)
  - Configures weekly schedule: Wednesday 06:00 UTC (1 AM EST)
  - Location: `G:\My Drive\Projects\_studio\`

- `run-discovery-NOW.bat` (37 lines)
  - Immediate launcher for testing/manual runs
  - Bypasses scheduler, runs right now
  - Location: `G:\My Drive\Projects\_studio\`

### Configuration & Registry
- `scrape-registry.json` (113 lines)
  - Updated with job-source-discovery entry
  - Status: PENDING_BUILD → will become ACTIVE after first run
  - All 5 scrapes now registered

- `job-source-discovery-complete-spec.md` (638 lines)
  - Complete technical specification
  - 5 discovery methods + blocking solutions + escalation framework
  - Reference document

---

## IMMEDIATE EXECUTION OPTIONS

### Option 1: Start NOW (Test Run)
```batch
cd G:\My Drive\Projects\_studio
run-discovery-NOW.bat
```
**What happens**:
- Launcher starts immediately
- Discovers URLs across all 5 methods
- Outputs to: `G:/My Drive/Projects/job-match/source-discovery/`
  - `job-source-registry.json` (master index)
  - `blocking-investigation.json` (blockers log)
- Takes ~30-60 minutes for first run

**Output Files**:
```
G:\My Drive\Projects\job-match\source-discovery\
├── job-source-registry.json          (all URLs found)
├── blocking-investigation.json       (all blockers documented)
└── coverage-benchmark-{date}.json    (weekly comparison to competitors)
```

### Option 2: Schedule for Tonight (6 AM UTC = 1 AM EST)
```powershell
# Run as Administrator
cd G:\My Drive\Projects\_studio
powershell -ExecutionPolicy Bypass -File register-job-discovery-task.ps1
```
**What happens**:
- Task registered in Windows Task Scheduler
- Runs automatically: Weekly Wednesday 06:00 UTC
- Logs stored in: `G:\My Drive\Projects\_studio\logs\`
- Can manually trigger anytime

**Verify Registration**:
```powershell
Get-ScheduledTask -TaskName "Job_Source_Discovery_Weekly" -TaskPath "\Studio\"
```

**Run Immediately (After Registration)**:
```powershell
Start-ScheduledTask -TaskName "Job_Source_Discovery_Weekly" -TaskPath "\Studio\"
```

---

## DISCOVERY METHODS (What Runs)

### Method 1: Common Crawl Patterns (50,000 URLs)
- Queries Common Crawl CDX index
- 50+ job-related URL patterns
- Examples: `*/careers`, `*/jobs`, `*/hiring`, `*/employment`
- Cost: FREE

### Method 2: Company Sitemaps (20,000 URLs)
- Fetches sitemaps from 5,000+ companies
- Extracts career/job paths
- Handles rate limits and 403 blocks
- Logs all blocked domains
- Cost: FREE

### Method 3: Government APIs (100,000 URLs)
- USAJOBS API (federal)
- 50 state job boards
- Municipal government sites
- Cost: FREE

### Method 4: Community Boards (5,000 URLs)
- Reddit (r/jobs, r/forhire, industry subs)
- Discord servers
- Telegram channels
- Facebook groups
- Cost: FREE

### Method 5: Free Job Boards (10,000 URLs)
- GitHub Jobs
- Stack Overflow Jobs
- AngelList, Dribbble, Behance
- And 100+ niche boards
- Cost: FREE

**Total Target**: 145,000-190,000 job posting surfaces

---

## OUTPUT STRUCTURE

### job-source-registry.json
```json
{
  "generated": "2026-04-02T06:30:00Z",
  "sources": [
    {
      "id": "cc-pattern-careers",
      "source_type": "common_crawl_patterns",
      "urls_found": 5000,
      "status": "ACTIVE",
      "last_scan": "2026-04-02T06:00:00Z"
    },
    // ... 5000+ entries
  ],
  "blocked_sources": [
    {
      "platform": "LinkedIn",
      "reason": "IP ban + Cloudflare",
      "free_workarounds": [],
      "paid_solutions": ["LinkedIn API ($$$)", "Residential proxies ($50-200/mo)"],
      "escalation_status": "PENDING_DECISION"
    }
  ]
}
```

### blocking-investigation.json
```json
{
  "investigation_log": [
    {
      "source": "linkedin.com",
      "status_code": 403,
      "blocking_type": "IP Ban + Cloudflare",
      "free_workarounds": ["Residential proxy"],
      "recommended_action": "ESCALATE if coverage gap >20%"
    }
  ],
  "blockers_identified": 15,
  "escalation_pending": []
}
```

---

## MONITORING & TROUBLESHOOTING

### Check Recent Logs
```batch
dir /od G:\My Drive\Projects\_studio\logs\job-source-discovery*.log
```

### View Latest Log
```batch
type "G:\My Drive\Projects\_studio\logs\job-source-discovery-RUN-{TIMESTAMP}.log"
```

### Verify Output Files Exist
```batch
dir "G:\My Drive\Projects\job-match\source-discovery\"
```

### Common Issues

**Issue**: Script fails with network timeout
- **Solution**: Increase timeouts in launcher.py (line ~45)
- Rerun with `run-discovery-NOW.bat`

**Issue**: Common Crawl API returns 0 results
- **Solution**: Common Crawl may have rate limiting; add longer delays
- **Escalation**: Not critical, other 4 methods will still find URLs

**Issue**: Some company sitemaps blocked (403)
- **Solution**: This is expected and logged
- **Action**: Use free user-agent rotation in Tier 1
- **Escalation**: If >20% fail, consider residential proxy

**Issue**: GitHub Jobs or Stack Overflow unreachable
- **Solution**: Verify internet connection
- **Escalation**: Unlikely, both are highly available

---

## NEXT PHASE (After Phase 1 Complete)

### Phase 2: Daily Scraper (Week of 2026-04-08)
- Takes job-source-registry.json as input
- Fetches all 150,000+ URLs daily
- Parses job listings (title, company, salary, location)
- Deduplicates, scores quality
- Stores in database
- Tracks new/updated/removed jobs

### Phase 3: Blocking Solutions (Week of 2026-04-15)
- Implement Tier 1 free workarounds
- Test against blocked sources
- Document success/failure for each

### Phase 4: Benchmarking (Ongoing)
- Weekly comparison vs LinkedIn, Indeed, ZipRecruiter
- Track coverage % by geography and industry
- Decision gate: Escalate to paid if <60% coverage

---

## EXECUTION DECISION MATRIX

| Run Now? | When? | Command | Outcome |
|----------|-------|---------|---------|
| YES | ASAP | `run-discovery-NOW.bat` | First data in 30-60 min |
| YES | Tonight 1 AM | `register-job-discovery-task.ps1` then schedule | First run at 1 AM EST tonight |
| YES | Both | Run NOW + register | Data immediately + recurring |

**RECOMMENDED**: Run both → start NOW for immediate data, register task for recurring

---

## SUCCESS CRITERIA

✅ Phase 1 Complete when:
- Registry contains 150,000-200,000+ URLs
- All 5 discovery methods executed
- Blockers documented in investigation.json
- Zero errors in logs
- Output files saved to job-match/source-discovery/

✅ Ready for Phase 2 when:
- Registry stable for 2+ weeks
- Coverage measured vs competitors
- Escalation decisions made on blockers

---

## DEPLOYMENT CHECKLIST

- [x] job-source-discovery-launcher.py created (237 lines)
- [x] job-source-discovery-scheduler.bat created (28 lines)
- [x] register-job-discovery-task.ps1 created (59 lines)
- [x] run-discovery-NOW.bat created (37 lines)
- [x] scrape-registry.json updated with job-source-discovery entry
- [x] Output directory configured: G:/My Drive/Projects/job-match/source-discovery/
- [x] Logs directory configured: G:\My Drive\Projects\_studio\logs\
- [x] Documentation complete (this file)

**STATUS: READY FOR DEPLOYMENT**
