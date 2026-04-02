# Scrape Definition Template

**Use this template for EACH scrape to define scope, output, and CX integration**

---

## SCRAPE 1: [SCRAPE_ID]

### Identification
- **Scrape ID**: unique_scrape_name
- **Agent Owner**: Which agent runs this?
- **Type**: Category (Wayback CDX | HTTP Scrape | API Query | Sitemap Mining | etc.)

### Scope & Target
- **What is being harvested**: [specific description]
- **Target URL/source**: [exact target]
- **Date range** (if applicable): [start_date to end_date]
- **Geographic scope**: [if applicable]
- **Language/encoding**: [if applicable]

### Schedule & Frequency
- **Frequency**: daily | weekly | monthly | manual | triggered
- **Run time**: [HH:MM UTC]
- **Time zone**: UTC
- **Expected interval between runs**: [hours]
- **Backfill needed**: Yes/No — if yes, describe range

### Output
- **Output file location**: G:/My Drive/Projects/...
- **File format**: json | csv | txt | other
- **Output schema** (list each field):
  ```
  field_1: type (description)
  field_2: type (description)
  ...
  ```
- **Expected record count**: approximate number per run
- **Output size**: approximate MB per run

### Downstream Usage
- **Projects that consume this**:
  - Project 1: [how it's used]
  - Project 2: [how it's used]
  - ...
- **CX Agent workflows that use it**: [which ones]
- **Assets created from it**: [what gets published/created downstream]

### Provider & Quota
- **Service/API used**: [name]
- **Cost tier**: FREE | PAID | HYBRID
- **Quota consumed**: [units per run]
- **Daily quota limit**: [units]
- **Rate limits**: [requests/sec, etc.]
- **Authentication**: [if needed]

### Quality & Validation
- **Success criteria**:
  - Minimum records retrieved: [number]
  - Schema validation**: [pass/fail checks]
  - Recency requirement**: [e.g., "data not older than 24h"]
- **Error handling**: [what to do if scrape fails]
- **Duplicate handling**: [merge strategy, if applicable]

### Known Issues & Optimization
- **Current issues**: [list any known problems]
- **Scaling blockers**: [limitations if any]
- **Optimization opportunities**: [suggested improvements]
- **Dependencies**: [other scrapes or systems this depends on]

---

## MASTER SCRAPE DEFINITION LIST (To Fill Out)

### Known Scrapes (Status: Needs Definition)

**SCRAPE 1: wayback-c2c**
- Agent: AI_Intel_Agent
- Type: Wayback CDX query
- [ ] Definition started — see below

**SCRAPE 2: wayback-tech-forums**
- Agent: AI_Intel_Agent
- Type: Wayback CDX query
- [ ] Definition started

**SCRAPE 3: job-source-discovery**
- Agent: Job_Match_Agent
- Type: Common Crawl + Sitemap mining
- [ ] Definition started

**SCRAPE 4: job-scrape-daily**
- Agent: Job_Match_Agent
- Type: HTTP scrape (active job postings)
- [ ] Definition started

**SCRAPE 5: ai-intel-layer2**
- Agent: AI_Intel_Agent
- Type: Multiple feeds (Tavily, YouTube, sitemaps, GitHub)
- [ ] Definition started

**SCRAPE 6: foreign-ministry-japanese**
- Agent: Foreign_Ministry_Agent
- Type: 2ch scrape
- [ ] Definition started

**SCRAPE 7: foreign-ministry-german**
- Agent: Foreign_Ministry_Agent
- Type: CCC/Heise scrape
- [ ] Definition started

**SCRAPE 8: foreign-ministry-russian**
- Agent: Foreign_Ministry_Agent
- Type: Habr scrape
- [ ] Definition started

**SCRAPE 9: ghost-book-validation**
- Agent: Ghost_Book_Agent
- Type: Wayback CDX (copyright validation)
- [ ] Definition started

**SCRAPE 10: game-archaeology**
- Agent: Game_Archaeology_Agent (PENDING BUILD)
- Type: Wayback CDX + content fetch
- [ ] Definition started

**SCRAPE 11: ebay-agent**
- Agent: eBay_Agent
- Type: eBay API
- [ ] Definition started

**SCRAPE 12: market-scout**
- Agent: Market_Scout_Agent
- Type: HTTP + eBay API
- [ ] Definition started

**+ Additional scrapes not yet identified?**
- [ ] TBD

---

## Filled Definition Example (Reference)

### SCRAPE: job-source-discovery

**Identification**
- Scrape ID: `job-source-discovery`
- Agent Owner: `Job_Match_Agent`
- Type: `Common Crawl API + Sitemap mining`

**Scope & Target**
- What is being harvested: Job posting URLs from company career pages and job boards worldwide
- Target URL/source: Common Crawl index + company sitemaps (Fortune 500, staffing agencies, gov, niche boards)
- Date range: Current/rolling window
- Geographic scope: Global (US priority, EU secondary)
- Language/encoding: English primary, others as found

**Schedule & Frequency**
- Frequency: `daily`
- Run time: `02:00 UTC`
- Expected interval: `24 hours`
- Backfill needed: No

**Output**
- Output file location: `G:/My Drive/Projects/job-match/source-discovery/job-source-registry.json`
- File format: `json`
- Output schema:
  ```
  id: string (unique identifier)
  source: string (e.g., "LinkedIn", "company-name.com", "Government")
  url: string (direct URL to jobs page)
  category: string (job_board | company | staffing | gov | niche)
  verified_active: boolean (HTTP status 200 within last 7 days)
  last_verified: ISO8601 timestamp
  ```
- Expected record count: 500-2000 per run
- Output size: 2-5 MB

**Downstream Usage**
- Projects that consume this:
  - Job_Match: Primary feed for daily job scraper
  - Talent_Insight_Engine: Source registry for ATS optimization
- CX Agent workflows: Job_Posting_Validator (formats + publishes)
- Assets created: Job postings published to Job_Match app, exported to CSV

**Provider & Quota**
- Service: Common Crawl (free) + Sitemap parser (local)
- Cost tier: FREE
- Quota: Unlimited
- Rate limits: None (local processing)
- Authentication: None

**Quality & Validation**
- Success criteria:
  - Minimum records: 300
  - Schema validation: All required fields present
  - Recency: Registry updated daily
- Error handling: If <300 records, retry once; if still fails, skip day and alert
- Duplicate handling: Deduplicate by URL; keep highest-confidence entry

---

## Submission Instructions

**For each scrape, fill out the template above and provide**:

1. **Identification** (agent, type)
2. **Scope** (what, target, range)
3. **Schedule** (frequency, time)
4. **Output** (file, schema, format)
5. **Downstream** (who uses it, what CX creates)
6. **Provider** (API, quota, cost)
7. **Validation** (success criteria)

Then we'll:
1. Add all definitions to `scrape-registry.json`
2. Build Coordinator Phase 1
3. Deploy to Task Scheduler
4. Start collecting audits
