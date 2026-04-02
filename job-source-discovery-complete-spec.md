# Job Source Discovery + Daily Scraper System
## Architecture Specification

**Version**: 1.0  
**Date**: 2026-04-01  
**Goal**: Most jobs scraped anywhere, in organized fashion  
**Philosophy**: Free tools first, escalate to paid only when blocking justifies ROI

---

## PHASE 1: EXHAUSTIVE URL DISCOVERY (Find ALL Job Posting Surfaces)

### Discovery Method 1: Common Crawl Index (Exhaustive URL Patterns)

**What**: Query Wayback Machine's Common Crawl index for all URLs matching job-related patterns  
**Coverage**: 50,000-500,000+ unique job posting URLs  
**Cost**: FREE  
**Time**: 6-12 hours (respectful rate limiting, 2-5 sec delay between queries)

**Implementation**:
```python
# Query patterns to search (start with core, expand to 50+)
job_patterns = [
    '*/careers', '*/careers/*', '*/jobs', '*/jobs/*',
    '*/hiring', '*/hiring/*', '*/employment', '*/employment/*',
    '*/job-openings', '*/apply', '*/work-with-us', '*/join-us',
    '*/join-our-team', '*/open-positions', '*/current-openings',
    '*/vacancies', '*/job-listing', '*/positions', '*/recruit',
    '*/recruitment', '*/career-opportunities', '*/job-opportunities',
    # ... expand to 50+ patterns covering variations
]

# For each pattern:
# - Query Common Crawl Index
# - Filter HTTP 200 responses
# - Extract base domain + full URL
# - Deduplicate by domain
# - Store in discovery registry
```

**Output**: `cc-discovered-urls.json`  
**Blocks**: None anticipated (Common Crawl is public, respectful rate limiting honored)

---

### Discovery Method 2: Company Sitemaps (Direct Corporate Career Pages)

**What**: Fetch sitemaps from 5,000+ companies, filter for career/job paths  
**Coverage**: 10,000-50,000 direct career page URLs  
**Cost**: FREE  
**Time**: 4-8 hours

**Implementation**:
```python
# Company lists:
# - Fortune 500 (top 500 US companies)
# - Tech companies (50-100)
# - Healthcare (50-100)
# - Finance (50-100)
# - Retail (50-100)
# - Manufacturing (50-100)
# - Government agencies (100+)
# - Regional/local businesses (1000+)

# For each company domain:
# - Fetch robots.txt (check /sitemap.xml reference)
# - Fetch sitemap.xml
# - Filter for career-related paths:
#   /career*, /job*, /hiring*, /recruit*, /apply*
# - Extract and store URLs
```

**Output**: `company-sitemap-urls.json`  
**Blocks**: 
- Some companies block by User-Agent → Rotate user agents
- Some block by rate → Add 2-5 sec delays
- Some return 403 → Log and skip, mark for potential paid proxy investment

**Blocked Domains Log**: `blocked-sitemaps.json`
```json
{
  "domain": "company.com",
  "status_code": 403,
  "reason": "Access Denied",
  "last_attempt": "2026-04-01T12:00:00Z",
  "solution_tier": "free (user-agent rotation) → medium (proxy) → high (paid residential IPs)"
}
```

---

### Discovery Method 3: Government Job APIs (Federal + State + Local)

**What**: Query government job posting APIs (free, no auth required)  
**Coverage**: 50,000-500,000 government jobs  
**Cost**: FREE  
**Time**: 2-4 hours

**Implementation**:
```python
# USAJOBS API (federal)
# - Endpoint: https://data.usajobs.gov/api/search
# - No auth required
# - Free tier: unlimited
# - Coverage: All federal job postings

# State job boards (50 states)
# - Most have APIs or public RSS feeds
# - Example: ca.gov, ny.gov, tx.gov
# - Coverage: 5,000-50,000 per state

# County/municipal sites
# - Manual discovery of public job posting URLs
# - Coverage: 10,000-50,000 local government

# Military/Defense
# - USAJobs covers this
# - MilitaryJobs.com (free access)
```

**Output**: `government-jobs-urls.json`  
**Blocks**: 
- Rate limiting on some state APIs → Add delays
- Some states have no API → Mark for manual discovery
- Coverage gaps → Document and prioritize by population

**Uncovered States Log**: `government-coverage-gaps.json`

---

### Discovery Method 4: Social/Community Job Boards (Emerging Opportunities)

**What**: Aggregate job postings from Reddit, Facebook groups, Discord, Telegram  
**Coverage**: 5,000-20,000 active community job boards  
**Cost**: FREE (plus optional $5-20/month for dedicated Discord/Telegram bots)  
**Time**: 2-3 hours setup, ongoing crawl

**Implementation**:
```python
# Reddit
# - Query r/jobs, r/[industry], r/forhire
# - Use PRAW (Python Reddit API Wrapper) - free
# - Extract post URLs, job descriptions, apply links

# Facebook
# - Manually identify job-posting groups (100+)
# - Query via Facebook Graph API (requires app, free tier)
# - Extract post URLs, job descriptions

# Discord
# - Identify job-posting servers (100+)
# - Use discord.py bot (free)
# - Crawl #jobs, #hiring, #opportunities channels

# Telegram
# - Identify job-posting channels (50+)
# - Use Telegram Bot API (free)
# - Subscribe to channels, extract job posts
```

**Output**: `community-job-urls.json`  
**Blocks**: 
- Reddit: No blocking, PRAW is official
- Facebook: API rate limits → Cache results, 1 query per 10 min
- Discord: Self-bot detection risk → Use official bot framework
- Telegram: Public channels only, no auth needed

**Blocking Risk Log**: `community-api-risks.json`
```json
{
  "platform": "Discord",
  "risk": "self-bot detection",
  "mitigation": "use official bot framework with rate limiting",
  "cost_if_blocked": "free (alternative)",
  "escalation": "none needed"
}
```

---

### Discovery Method 5: Job Board & Aggregator Mining (Scraped or API)

**What**: Extract job posting URLs from major job boards  
**Coverage**: 100,000-500,000+ job posting URLs  
**Cost**: FREE (with workarounds for blocked sites)  
**Time**: 4-6 hours initial, ongoing daily

**Free Tier Sources**:
- GitHub Jobs (API)
- Stack Overflow Jobs (API)
- HackerNews "Who's Hiring" (scrape)
- AngelList (API)
- Dribbble Jobs (API)
- Behance Jobs (API)
- ProductHunt Jobs (scrape)
- Indie Hackers Jobs (scrape)
- Niche job boards (100+ via sitemap mining)

**Blocked Sources** (Requires Paid Solutions):
- LinkedIn (blocks scrapers, has paid API)
- Indeed (blocks scrapers, has paid API)
- Glassdoor (blocks scrapers, has paid API)
- ZipRecruiter (blocks scrapers)

**Output**: `job-board-urls.json`  
**Blocks Log**: `blocked-job-boards.json`
```json
{
  "board": "LinkedIn",
  "status": "BLOCKED",
  "reason": "IP ban + Cloudflare protection",
  "free_workaround": "none available",
  "paid_solution": "LinkedIn Recruiter API ($$$) or Bright Data residential proxies ($50-200/mo)",
  "estimated_jobs_lost": "10,000-50,000/day",
  "escalation_criteria": "if 20%+ of target market uses LinkedIn, escalate to paid",
  "investigation_status": "pending"
}
```

---

## MASTER REGISTRY OUTPUT (End of Phase 1)

**File**: `job-source-registry.json`
```json
{
  "generated": "2026-04-01T18:00:00Z",
  "summary": {
    "total_sources": 150000,
    "by_category": {
      "common_crawl_patterns": 50000,
      "company_sitemaps": 20000,
      "government_apis": 100000,
      "community_boards": 5000,
      "job_boards_free": 10000,
      "niche_aggregators": 5000,
      "other": 10000
    },
    "coverage_by_geography": {
      "us_federal": 50000,
      "us_state": 40000,
      "us_local": 10000,
      "remote": 20000,
      "international": 30000
    },
    "blocked_sources": {
      "total_identified": 15,
      "free_workarounds_available": 8,
      "requires_paid": 7,
      "total_jobs_potentially_lost": "50000-100000/day"
    }
  },
  "sources": [
    {
      "id": "cc-pattern-careers",
      "source_type": "common_crawl_pattern",
      "pattern": "*/careers",
      "urls_found": 5000,
      "status": "ACTIVE",
      "last_scan": "2026-04-01T12:00:00Z"
    },
    {
      "id": "sitemap-amazon",
      "source_type": "company_sitemap",
      "company": "amazon.com",
      "urls_found": 150,
      "status": "ACTIVE",
      "last_scan": "2026-04-01T14:00:00Z"
    },
    // ... 150,000 entries total
  ],
  "blocked_sources": [
    {
      "id": "linkedin-blocked",
      "platform": "LinkedIn",
      "reason": "IP ban + Cloudflare protection",
      "free_workarounds": [],
      "paid_solutions": ["LinkedIn Recruiter API ($$$)", "Bright Data Residential ($50-200/mo)"],
      "estimated_jobs_missed": "20000-50000/day",
      "investigation_date": "2026-04-01",
      "next_review": "2026-04-15"
    }
  ]
}
```

---

## PHASE 2: DAILY SCRAPER (Feed from Phase 1 Registry)

### Architecture

```
INPUT: job-source-registry.json (150,000+ URLs)

DAILY WORKFLOW (runs 12:00 AM UTC):
1. Load registry of 150,000+ job posting URLs
2. For each URL:
   a. Fetch page (Puppeteer if JS required, retry logic)
   b. Parse job listings (title, company, description, salary, location, etc.)
   c. Extract structured data (schema.org JobPosting if available, else heuristic)
   d. Compare to yesterday's snapshot
   e. Classify: NEW | UPDATED | REMOVED | DUPLICATE | SPAM
   f. Homogenize fields (standardize titles, companies, locations)
   g. Score quality (flag suspicious, incomplete, stale)
   h. Insert into master database

OUTPUT:
- new-jobs-{date}.json (10,000-100,000 new jobs)
- updated-jobs-{date}.json (5,000-50,000 updated jobs)
- removed-jobs-{date}.json (2,000-20,000 removed jobs)
- duplicates-merged-{date}.json (statistics on deduplication)
- quality-flags-{date}.json (suspicious/low-quality jobs flagged)
- coverage-report-{date}.json (benchmarking vs competitors)
```

### Job Parsing & Homogenization

```python
# Raw job data → normalized fields
normalized_job = {
    "job_id": "hash(company + title + location)",
    "title": "Software Engineer",  # normalized via taxonomy
    "title_normalized": "SWE",
    "company": "Amazon",  # deduplicated (Amazon, Inc., AMZN, etc.)
    "company_id": "amzn",
    "location": {
        "city": "Seattle",
        "state": "WA",
        "country": "US",
        "remote": false,
        "coordinates": [47.6, -122.3]
    },
    "salary": {
        "min": 120000,
        "max": 180000,
        "currency": "USD",
        "frequency": "annually"
    },
    "description": "full job description text",
    "requirements": ["Python", "AWS", "5+ years"],
    "job_type": "full_time",  # full_time | part_time | contract | intern
    "posted_date": "2026-03-28",
    "source_url": "url",
    "source_type": "company_sitemap",
    "source_domain": "amazon.com",
    "scraped_at": "2026-04-01T12:30:00Z"
}
```

### Deduplication Logic

```python
# Hash on (company + title + location)
# If hash matches yesterday's job:
#   - If salary/description changed: UPDATED
#   - If identical: DUPLICATE (keep highest-quality version)
#   - If gone from source: REMOVED

# Quality preference order:
# 1. Job with salary range
# 2. Job with full description
# 3. Job with requirements listed
# 4. Job with posted date
```

### Quality Scoring & Flagging

```
SPAM FLAGS (auto-remove or flag):
- Missing title or company: INCOMPLETE
- All caps title: SUSPICIOUS
- Keywords: "work from home" + "$50/hr" + "no experience": SPAM
- Same job on 100 sources same day: DUPLICATE
- Posted 90+ days ago, no update: STALE
- URL returns 404: DEAD_LINK

QUALITY SCORE (1-10):
- 10 = salary + full description + requirements + recent
- 7 = title + company + location + basic description
- 4 = minimal info (title, company only)
- 1 = spam or nearly empty
```

### Daily Scraper Configuration

**File**: `daily-scraper-config.json`
```json
{
  "schedule": "0 0 * * *",  // 12:00 AM UTC daily
  "timeout_per_url": 30,     // seconds
  "max_retries": 3,
  "retry_delay": 5,          // seconds
  "concurrent_requests": 10,
  "user_agents": ["rotate from pool of 50+"],
  "proxy_config": {
    "use_proxy": false,
    "escalate_to_proxy_after_failures": 10,
    "proxy_provider": "none",
    "cost_per_month": 0
  },
  "browser_rendering": {
    "use_puppeteer": true,
    "headless": true,
    "timeout": 20
  },
  "deduplication": {
    "enabled": true,
    "hash_fields": ["company", "title", "location"]
  },
  "quality_filtering": {
    "min_score": 4,
    "flag_spam": true,
    "remove_stale_after_days": 90
  },
  "output": {
    "database": "job_postings_master.db",
    "backup": "daily_backups/",
    "logs": "logs/daily-scraper-{date}.log"
  }
}
```

---

## BLOCKING SOLUTIONS & ESCALATION FRAMEWORK

### Tier 1: FREE SOLUTIONS (Start Here)

| Blocker | Free Solution | Implementation |
|---------|---------------|-----------------|
| User-Agent blocks | Rotate user agents (50+ strings) | List maintained in code, random selection |
| Basic rate limiting | Add delays (2-5 sec between requests) | Use exponential backoff |
| Cloudflare basic | cloudscraper Python library | `pip install cloudscraper` |
| IP blocks (soft) | Random delays, spread requests over time | Distribute to multiple days |
| JavaScript rendering | Puppeteer (headless Chrome) | `npm install puppeteer` |
| Simple bot detection | Add Accept headers, Referer, etc. | Mimic browser headers |
| Session auth required | Store cookies from successful requests | Cookie jar management |

**Cost**: $0  
**Coverage**: 70-80% of job sources  
**Implementation Time**: 2-3 weeks

### Tier 2: MEDIUM SOLUTIONS (If Free Insufficient)

| Blocker | Medium Solution | Cost | When to Escalate |
|---------|-----------------|------|------------------|
| Consistent IP bans | Free proxy rotation (less reliable) | $0 (slow) or $20-50/mo (residential) | If >30% of sources blocked |
| Cloudflare + bot detection | Apify, ScrapingBee with handling | $20-50/mo free tier | If Tier 1 fails on 5+ sources |
| Rate limiting (strict) | Distributed scraping across time | $0 | If <5 sources affected |
| OAuth/login required | Maintain authenticated session pool | $0 (time intensive) | If critical for revenue |

**Cost**: $20-100/mo  
**Coverage**: 80-90% of job sources  
**ROI Calculation**: (jobs unlocked × revenue_per_job) vs cost

### Tier 3: PAID SOLUTIONS (Only If ROI Justifies)

| Blocker | Paid Solution | Cost | When to Escalate |
|---------|---------------|------|------------------|
| LinkedIn, Indeed, Glassdoor blocks | Residential proxies (Bright Data, Oxylabs) | $50-200/mo | If missing 50,000+ jobs/day AND revenue justifies |
| Advanced Cloudflare | Bright Data residential + browser rendering | $100-300/mo | If >10% of high-value jobs blocked |
| API access to major boards | LinkedIn Recruiter API, Indeed API | $500-5000/mo | Only if proprietary data needed |
| Dedicated infrastructure | Cloud scraping service (Apify, ScrapingBee premium) | $100-500/mo | If scaling to 1M+ jobs/day |

**Cost**: $100-5000/mo  
**Coverage**: 95%+ of job sources (including LinkedIn, Indeed)  
**Decision Trigger**: "If blocking = losing >20% of addressable market, invest"

---

## BLOCKING INVESTIGATION & LOGGING

**File**: `blocking-investigation.json`
```json
{
  "status": "ongoing",
  "last_updated": "2026-04-01T18:00:00Z",
  "total_sources_tested": 150000,
  "blockers_identified": 15,
  "investigation_log": [
    {
      "date": "2026-04-01",
      "source": "linkedin.com/jobs",
      "access_attempt": "GET https://linkedin.com/jobs?search=engineer",
      "status_code": 403,
      "response": "Access Denied",
      "blocking_type": "IP Ban + Cloudflare",
      "free_workarounds": [
        "Residential proxy rotation",
        "API alternative (paid)"
      ],
      "recommended_action": "SKIP for now, reassess if coverage gap >20%",
      "escalation_status": "PENDING_DECISION"
    },
    {
      "date": "2026-04-01",
      "source": "indeed.com/resumes",
      "access_attempt": "GET https://indeed.com/...",
      "status_code": 429,
      "response": "Too Many Requests",
      "blocking_type": "Rate Limiting",
      "free_workarounds": [
        "Exponential backoff",
        "Distribute scraping over 24hr"
      ],
      "recommended_action": "Implement backoff, retry",
      "escalation_status": "RESOLVED"
    }
  ],
  "blocked_sources_summary": {
    "linkedin": {
      "blocked": true,
      "jobs_estimated": "50000/day",
      "importance": "HIGH",
      "revenue_impact": "unknown_until_measured",
      "decision": "PENDING"
    },
    "indeed": {
      "blocked": false,
      "jobs_estimated": "100000/day",
      "importance": "CRITICAL",
      "workaround": "exponential_backoff",
      "status": "WORKING"
    }
  }
}
```

---

## BENCHMARKING vs COMPETITORS

**Weekly Measurement** (Compare coverage to LinkedIn, Indeed, ZipRecruiter, Glassdoor):

```python
# For 100 random job searches (geography + industry combo):
# - "Software Engineer in Nashville"
# - "Nurse in New York"
# - "Accountant in Austin"
# ... 100 searches

# Count unique jobs found in:
# - Your database
# - LinkedIn
# - Indeed
# - ZipRecruiter
# - Glassdoor
# - Local job boards

# Calculate: % coverage vs each competitor
# Target: 70-90% (never 100%, some jobs private)

# Track by:
# - Geography (country, state, city)
# - Industry (tech, healthcare, finance, etc.)
# - Company size (startup, mid-market, enterprise)
# - Job type (full-time, contract, remote, etc.)
```

**Output**: `coverage-benchmark-{date}.json`
```json
{
  "week": "2026-04-01",
  "sample_searches": 100,
  "coverage": {
    "your_database": {
      "total_unique": 45000,
      "coverage_percent": 78.5
    },
    "linkedin": {
      "total_unique": 55000,
      "coverage_percent": 100
    },
    "indeed": {
      "total_unique": 52000,
      "coverage_percent": 94.5
    },
    "ziprecruiter": {
      "total_unique": 48000,
      "coverage_percent": 87.3
    }
  },
  "gaps": {
    "missing_vs_linkedin": 10000,
    "missing_vs_indeed": 7000,
    "unique_to_you": 2000,
    "improvement_target": "Get to 85%+ coverage"
  }
}
```

---

## SUMMARY: EXECUTION ROADMAP

### Week 1: Phase 1 Discovery (Build Registry)
- Common Crawl patterns: 50+ patterns → 50,000 URLs
- Company sitemaps: 5,000 companies → 20,000 URLs
- Government APIs: USAJOBS + state boards → 100,000 URLs
- Community boards: Reddit, Facebook, Discord → 5,000 URLs
- Job boards (free): GitHub, Stack Overflow, etc. → 10,000 URLs
- **Output**: 185,000 URLs in master registry

### Week 2: Phase 2 Daily Scraper
- Build parser (title, company, salary, description, etc.)
- Implement homogenization logic
- Deduplication engine
- Quality scoring
- Schedule daily runs
- **Output**: First 24-48 hours of scraped jobs

### Week 3: Blocking Investigation + Escalation
- Test all 185,000 sources
- Document blockers in investigation.json
- Evaluate Tier 1 free solutions
- Decision: Which free workarounds to implement
- **Output**: Blocking log, escalation decisions

### Week 4+: Benchmarking + Optimization
- Compare coverage to LinkedIn, Indeed, ZipRecruiter
- Identify high-value sources to prioritize
- Implement Tier 1 solutions for top blockers
- **Decision Gate**: If coverage <60%, escalate to Tier 2
- **Ongoing**: Weekly coverage reports, continuous improvement

---

## ESCALATION DECISION FRAMEWORK

**IF coverage drops below 60%**: Evaluate Tier 2 (residential proxies, Apify)  
**IF blocking = losing 50,000+ jobs/day from target market**: Escalate to paid  
**IF revenue per job × jobs_lost > $100/day**: Justify $50-200/mo investment  
**IF LinkedIn/Indeed = >30% of jobs**: Consider paid API access ($500+/mo)

**Decision Gate Metric**: (Est. Monthly Jobs Lost) × (Revenue per Job) > (Monthly Cost of Solution) = GO

