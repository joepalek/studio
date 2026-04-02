# JOB SOURCE DISCOVERY - QUICK START
## 30 Second Deployment

**Date**: 2026-04-02  
**Status**: ✅ READY TO GO

---

## START IMMEDIATELY (RIGHT NOW)

```
1. Open Command Prompt or PowerShell
2. Run: G:\My Drive\Projects\_studio\run-discovery-NOW.bat
3. Wait 30-60 minutes
4. Check output: G:\My Drive\Projects\job-match\source-discovery\
```

**Output Files After Completion**:
- ✅ `job-source-registry.json` — All 150,000+ URLs discovered
- ✅ `blocking-investigation.json` — All blockers documented

---

## SCHEDULE FOR NIGHTLY (OPTIONAL)

```
1. Open PowerShell as Administrator
2. Run: powershell -ExecutionPolicy Bypass -File "G:\My Drive\Projects\_studio\register-job-discovery-task.ps1"
3. Task registered: Runs Weekly Wednesday 06:00 UTC (1 AM EST)
4. Logs saved to: G:\My Drive\Projects\_studio\logs\
```

---

## DEPLOYMENT SUMMARY

| Component | Status | File |
|-----------|--------|------|
| Discovery Launcher | ✅ Ready | `job-source-discovery-launcher.py` |
| Scheduler Wrapper | ✅ Ready | `job-source-discovery-scheduler.bat` |
| Task Registration | ✅ Ready | `register-job-discovery-task.ps1` |
| Immediate Launcher | ✅ Ready | `run-discovery-NOW.bat` |
| Registry Updated | ✅ Ready | `scrape-registry.json` |
| Specification Doc | ✅ Ready | `job-source-discovery-complete-spec.md` |
| This Guide | ✅ Ready | `JOB_DISCOVERY_EXECUTION_GUIDE.md` |

---

## WHAT HAPPENS

**Phase 1 Discovery Runs**:
1. Common Crawl patterns → 50,000 URLs
2. Company sitemaps → 20,000 URLs
3. Government APIs → 100,000 URLs
4. Community boards → 5,000 URLs
5. Free job boards → 10,000 URLs

**Total**: 145,000-190,000 job posting surfaces discovered

**Output**: Master registry ready for Phase 2 (Daily Scraper)

---

## MONITORING

Watch logs as it runs:
```
tail -f "G:\My Drive\Projects\job-match\source-discovery\job-source-discovery.log"
```

Check completion:
```
dir "G:\My Drive\Projects\job-match\source-discovery\"
```

---

## NEXT PHASE (After Discovery Complete)

Phase 2: Daily Scraper (starts ~2026-04-08)
- Feeds registry into daily job scraper
- Parses and deduplicates
- Builds master job database

---

✅ **READY: Execute `run-discovery-NOW.bat` to start**
