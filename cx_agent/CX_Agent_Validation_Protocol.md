# CX Agent Validation & Distribution Protocol

## Role Definition
**CX Agent** is the quality gate and traffic cop for ALL agent-created assets. Its job:
1. Receive assets from creator agents
2. Grade them (format, quality, brand alignment)
3. Route to final destinations
4. Monitor usage and performance
5. Feed high-performing assets to social media for amplification

---

## Intake Process

### Input from Creator Agents
CX Agent monitors these inputs:
- **eBay_Listing_Agent** → JSON listing objects
- **CTW_Agent** → project outputs (apps, scripts, images, character files)
- **Ghost_Book_Agent** → story content (drafts, finalized scripts)
- **Jobs_Agent** → job postings and metadata

**Protocol:** Each creator agent emits structured JSON with:
```json
{
  "asset_id": "unique_id",
  "creator_agent": "agent_name",
  "asset_type": "string",
  "content": "...",
  "metadata": { "project": "...", "destination_hint": "..." }
}
```

---

## Validation Rubric

### 1. Format Check (Pass/Fail)
Does the asset match its expected schema?
- Listings: Required fields (title, price, condition, images)
- Characters: Required fields (name, description, visual_assets, metadata)
- Books: Required fields (title, chapter_structure, word_count, status)
- Jobs: Required fields (title, description, location, salary_range)

**Gate:** Fail format → escalate to whiteboard for manual review.

---

### 2. Quality Score (1-10 Scale)

#### 8-10: Production Ready
- No typos or grammatical errors
- Imagery is clear and professional
- Metadata complete and accurate
- Compelling description or narrative
- Aligns with project vision

#### 6-7: Review Needed
- Minor issues (typos, unclear descriptions)
- Some metadata gaps
- Visual quality acceptable but not polished
- Needs creator agent feedback

#### 5 and Below: Reject
- Major errors (broken schema, missing content)
- Unprofessional presentation
- Misaligned with brand
- Requires restart

**Scoring Guidance:**
- **Listings:** Clarity of title, image quality, accuracy of condition/price, completeness
- **Characters:** Visual consistency, compelling backstory, market appeal, technical correctness
- **Books:** Writing quality, narrative structure, completeness, marketability
- **Jobs:** Description clarity, realistic requirements, timezone/salary accuracy

---

### 3. Brand Alignment Check (Pass/Fail)

**Commonwealth Picker / Solvik Brand Values:**
- Authenticity (honest, no overselling)
- Systems thinking (clear logic, process-driven)
- Directness (clear language, no fluff)
- Accountability (facts over vibes)
- Quality craftsmanship

**For Each Asset Type:**

**Listings:**
- ✓ Accurate condition descriptions (not hyped)
- ✓ Fair pricing logic (cost + margin, market-aware)
- ✓ Clear sourcing context if relevant
- ✓ Professional photography

**Characters (CTW):**
- ✓ Consistent personality and behavior across assets
- ✓ Visually distinctive (recognizable)
- ✓ Backstory aligns with intended use (animation, games, etc.)
- ✓ No contradictions with existing character canon

**Books/Scripts (Ghost Book):**
- ✓ Voice/tone consistent with Commonwealth Picker brand
- ✓ Story logic is sound (no plot holes)
- ✓ Content aligns with market positioning (vintage, narrative-driven)
- ✓ Ready for professional release or video adaptation

**Jobs:**
- ✓ Realistic job descriptions (not bait-and-switch)
- ✓ Accurate about role expectations
- ✓ Aligns with Solvik's talent positioning (systems-thinking roles)

**Gate:** Fail alignment → send back to creator agent with specific feedback.

---

## Routing Decision Tree

```
Asset received by CX Agent
  ↓
Format check
  ├─ FAIL → Escalate to Whiteboard (manual review)
  └─ PASS → Quality Score (1-10)
           ├─ 8+ → Brand Alignment check
           │       ├─ PASS → Route to destination
           │       └─ FAIL → Send to creator for revision
           └─ 5-7 → Flag for manual review (Whiteboard staging)
           └─ <5 → Reject, require restart
```

---

## Destination Routing Logic

**Once asset passes validation (format + quality ≥8 + brand alignment pass):**

### eBay_Listing_Agent Output
```
Destination: eBay API (OAuth2 batch upload)
Method: POST to /v1/item/upload
Status Code: 200 = success → log to asset_creation_log.json
Status Code: 4xx/5xx = failure → staging_review (whiteboard)
Usage Monitoring: views, clicks, conversion_rate, seller_feedback
```

### CTW_Agent Output
```
IF output_type IN (app, script, mp4, jpg, excel):
  Destination: project_folder/{project_name}/outputs/
  Example: G:/My Drive/Projects/CTW/character_builder/outputs/
  
IF output_type == character_file:
  Destination: G:/My Drive/Projects/CTW/characters_final/
  Sub-destinations:
    - viewer_access (load into web viewer)
    - mirofish_queries (make available to context lookups)
    - api_endpoints (expose for external integrations)
  
Usage Monitoring: character_loads, adoption_rate, API_query_frequency
```

### Ghost_Book_Agent Output
```
IF status == draft OR newly_created:
  Destination: G:/My Drive/Projects/Ghost_Book/scripts_books_draft/
  Purpose: Available for new creation processes to consume
  Usage: Track which scripts get consumed, by whom, when

IF status == complete AND ready_for_release:
  Destination: G:/My Drive/Projects/Ghost_Book/done_books_scripts/
  Quality Gate: Must score ≥9
  Usage: Track completion metrics, readiness signals

IF status == released OR approved_for_market:
  Destination: G:/My Drive/Projects/Ghost_Book/final_books_scripts/
  Sub-destinations: market_distribution, video_creation_feed
  Usage Monitoring: downloads, reads, video_views, revenue
```

### Jobs_Agent Output
```
Destination: G:/My Drive/Projects/Job_Match/jobs_repository/
Purpose: Central depository for Job_Match app to query
Maintenance: CX Agent culls expired jobs daily (24-hour schedule)
Usage Monitoring: job_impressions, application_rate, fill_time
```

---

## Usage Tracking & Monitoring

Once an asset is routed to its destination:

### What CX Agent Monitors (Per Asset Type)

**eBay Listings:**
- Views, impressions, click-through rate
- Time-to-sale, final selling price
- Buyer feedback score
- Seasonal trends (e.g., holiday items peak Nov-Dec)

**CTW Characters:**
- Viewer loads, frequency of use
- API query frequency (mirofish, integrations)
- Adoption by other projects (CTW narrative uses this character)

**Ghost_Book Content:**
- Downloads, reads (via tracking script)
- Video creation requests (how often does video team use this?)
- Market performance (if released: revenue, royalties)

**Jobs:**
- Impressions (how many times shown to candidates)
- Application rate (quality of incoming applications)
- Position fill time (how fast does role get filled?)
- Note: Expired jobs are culled daily

### Monitoring Cadence
- **Real-time:** Track eBay/API activity (webhooks or polling every 1 hour)
- **Daily:** Refresh all usage metrics, cull expired jobs, flag underperformers
- **Weekly:** Aggregate trends, identify high-performers for social amplification

---

## Social Media Amplification Feed

### What Gets Amplified?

**High Signal = High Performance**

CX Agent identifies assets with strong usage signals and flags them for social media marketing:

**Criteria for Amplification:**
- eBay listings: CTR > 3%, conversion > 1% OR high engagement rate
- CTW characters: frequent viewer loads, high adoption in narratives
- Ghost_Book: high read count, video team is using it actively, good download momentum
- Jobs: high impression count, strong application rate, trending role type

### Output to Social Media Agent

CX Agent generates a daily/weekly feed like:

```json
{
  "amplification_candidates": [
    {
      "asset_id": "ebay_listing_20260329_001",
      "asset_type": "listing",
      "signal_strength": "high",
      "metric": "conversion_rate_3.2%",
      "suggested_channel": "Twitter",
      "suggested_narrative": "Hot drop: 1985 Bears championship poster. CTR 3.2%, trending with collectors.",
      "visual_asset": "listing_image_url"
    },
    {
      "asset_id": "ctw_character_mara",
      "asset_type": "character",
      "signal_strength": "high",
      "metric": "viewer_loads_1200_this_week",
      "suggested_channel": "Instagram",
      "suggested_narrative": "Meet Mara. This week: 1,200+ loads from our viewer. Your favorite character is catching on.",
      "visual_asset": "character_portrait_url"
    }
  ]
}
```

**Social Media Agent** then creates:
- Twitter threads about trending listings
- Instagram character spotlights
- YouTube video ideas ("Top 5 Ghost_Book Stories This Month")
- Newsletter features ("What's Trending in Commonwealth Picker This Week")

---

## Daily CX Agent Checklist

### Every 24 Hours:

- [ ] Poll all creator agents for new assets
- [ ] Run format checks on new assets
- [ ] Score quality for new assets
- [ ] Run brand alignment review
- [ ] Route passing assets to destinations
- [ ] Update usage metrics for all active assets
- [ ] Cull expired jobs from Jobs_Agent repository
- [ ] Identify high-performers for social amplification
- [ ] Escalate failures/rejections to Whiteboard
- [ ] Log all activity to `asset_creation_log.json`

### Escalation to Whiteboard (Manual Review):

When an asset fails any gate:
1. Create a whiteboard entry: `[ASSET_REVIEW] {asset_id} - {reason}`
2. Attach: asset content, validation failure reason, CX Agent recommendation
3. Assign: Creator agent (to fix) or human decision-maker
4. Re-route once fixed

---

## Error Handling

### Routing Fails (e.g., eBay API returns 400)
1. Log failure: `routing_status: "failed"` in asset_creation_log
2. Escalate to Whiteboard: `[ROUTING_FAILURE] {asset_id}`
3. Retry: CX Agent retries once after 1 hour
4. If still fails: Manual human review required

### Quality Threshold Ambiguity
- **8-10:** Route automatically
- **6-7:** Log to Whiteboard with "REVIEW_NEEDED" label, human decides
- **≤5:** Auto-reject, require creator agent to revise

### Missing Metadata
- Creator agent didn't specify destination or project
- CX Agent asks for clarification (logs to Whiteboard)
- Hold asset in staging until metadata complete

---

## Integration with Studio System

### Feeds Into:
- **Whiteboard Agent:** Escalations, rejections, manual review items
- **Social Media Agent:** High-performers for amplification
- **Analytics Dashboard:** Performance metrics, trending assets
- **Job Match App:** Jobs repository (curated list)
- **Supervisor Agent:** Status reports on asset flow

### Receives From:
- All 16 creator agents (new assets)
- Storage systems (G: drive, eBay API)
- External integrations (mirofish queries, video team requests)

---

## Configuration

### Scoring Weights (Optional Tuning)
```
Format Check: 30% (pass/fail)
Quality Score: 50% (1-10 → weighted)
Brand Alignment: 20% (pass/fail)
Overall Pass Threshold: 75%
```

### Retry Logic
- Failed routing: 1 retry after 1 hour
- Expired jobs: Delete daily at 2 AM UTC
- Stale assets (no usage for 90 days): Archive automatically

### Monitoring Interval
- Real-time usage: Poll every 1 hour
- Daily summary: Generate 6 AM UTC
- Weekly trends: Generate Mondays 9 AM UTC

---

## Success Metrics

Track CX Agent's own performance:

- **Assets processed per day:** Should increase as creator agents produce more
- **Pass-through rate:** % of assets that pass validation on first try
- **Routing success rate:** % of routed assets that land successfully
- **Time to route:** Minutes from creation to final destination
- **Social amplification impact:** CTR, engagement, conversion from flagged assets

---

## Notes for Implementation

1. **CX Agent logic can run as Python or Node service** (scheduled task via Windows Task Scheduler)
2. **asset_creation_log.json** should live in `studio_logs` folder on G: drive
3. **Whiteboard escalations** auto-create entries in Decisions inbox
4. **Real-time usage monitoring** requires webhooks (eBay) or polling scripts
5. **Creator agents emit JSON**; CX Agent consumes and routes via manifest logic

---

**End of Protocol**

Contact: Joe Palek | Last Updated: 2026-03-29
