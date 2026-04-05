## CHARACTER FACTORY OPERATIONS — TASK BREAKDOWN

**Goal**: 261 characters by end Q2 2026 → $500 revenue

**Constraint**: Art dept image production capacity

---

## TASK ASSIGNMENTS

### JOE (Director)

**Immediate (This Week)**:
1. ✓ Quantify art dept capacity
   - X images/day production rate?
   - Approval timeline per image?
   - Model creation timeline?
   - Can it run in parallel with image generation?
   - **Owner**: Joe (ask art dept)

2. ✓ Confirm image go-by acquisition is ongoing
   - Is art dept acquiring go-bys daily? Weekly?
   - Reference materials quality/quantity?
   - **Owner**: Joe (confirm with art dept)

3. ✓ Decide: Model creation priority
   - Every image → model? Or selective (Tier 2 only)?
   - Who does model creation? (Art dept? Third party?)
   - Timeline?
   - **Owner**: Joe (with art dept)

**Ongoing**:
- [ ] Weekly approval checkpoint (Tier 1 images) — 15-30 min/week
- [ ] Monthly revenue tracking + platform performance review
- [ ] Quarterly target assessment ($500 by end Q2)

---

### ART DEPT (Image + Model Production)

**Current State**: Image acquisition + generation ongoing

**Responsibilities**:
- [ ] Generate X images/day from go-by references
- [ ] Approve/reject generated images (art direction)
- [ ] Track image approval dates + notes
- [ ] Queue approved images for Tier 2 model creation
- [ ] Generate 3D models (Gaussian Splatting or comparable)
- [ ] Approve/direct models before Tier 2 completion
- [ ] Report weekly: images generated, approved, in model queue

**Output Metrics** (Track weekly):
- Images generated: X/week
- Images approved: X/week
- Models generated: X/week
- Models approved: X/week
- Bottleneck status: Clear/Constrained

**Constraint**: This is the system bottleneck. Everything else waits on art dept throughput.

---

### CHARACTER ANALYZER AGENT (AI Process)

**Owner**: Claude (builds + operates)

**Responsibilities**:
- [ ] Weekly batch processing (10-15 approved images)
- [ ] Archetype classification (role fit analysis)
- [ ] Personality sketch generation
- [ ] Story fit recommendations
- [ ] Character record assembly (JSON/CSV)
- [ ] Output to CX agent + social media

**Input**: Approved images + art dept metadata  
**Output**: Character records ready for CX agent + social media  
**Processing**: 2-5 mins per character, 10-15 characters/week  
**Timeline**: Ready by April 15, 2026

**Deliverables**:
- Character record template (JSON schema)
- Weekly batch process (automated or semi-automated)
- Archetype classification system (10 female archetypes + backup)
- Personality sketch library (examples + generation templates)
- Story fit recommendations (mapping archetypes to narratives)

---

### CX AGENT (Story Generation)

**Current State**: Ready to receive character records

**Responsibilities**:
- [ ] Receive weekly character batches (Tier 1 records)
- [ ] Generate stories featuring each character (3-5 sentences)
- [ ] Generate character dialogue samples (1-3 exchanges)
- [ ] Generate social media post variant (character-focused)
- [ ] Output story recommendations (what narratives fit this character)

**Input**: Character record (from analyzer)  
**Output**: Story + dialogue + social post (per character)  
**Processing**: ~30 mins per character, batched weekly  
**Timeline**: Already operational, ready for batches starting April 15

**Integration**:
- Character analyzer → CX agent input format
- CX agent output → Social media posting calendar
- CX agent output → Story casting pool (for story selection)

---

### SOCIAL MEDIA TEAM

**Responsibility #1: Platform Deployment Analysis** (ASAP, due May 1)

Task: Analyze + recommend deployment platform
- [ ] Competitor analysis: janitor.ai vs. crushon.ai vs. character.ai
  - Monetization model per platform
  - Audience size/demographics per platform
  - Character format requirements per platform
  - Integration difficulty (API, data format)
  - Revenue per 1000 chats (estimate)
  - Time-to-revenue per platform
  - **Deliverable**: Recommendation document + timeline

- [ ] Your personal viewer feasibility
  - Tech requirements (host, storage, interaction engine)
  - Design/UX (character display, interaction model)
  - Monetization options (freemium, subscriptions, tips, licensing)
  - Development timeline estimate
  - Revenue potential (conservative estimate)
  - **Deliverable**: Feasibility report + recommendation

- [ ] SEO/social media optimization strategy
  - What platforms work best for character promotion? (TikTok? Instagram? Twitter?)
  - Posting cadence per platform
  - Content format per platform (short clips? character quotes? story teasers?)
  - Hashtag strategy (character branding)
  - Cross-platform strategy (viewer ↔ social ↔ platform distribution)
  - **Deliverable**: Social media marketing plan + calendar template

- [ ] Domain/platform name capture
  - What's available? (davinci.ai? tesla.ai? curie.ai?)
  - What should be registered first? (brand protection)
  - Social handles per character? (per platform strategy)
  - **Deliverable**: Domain/handle recommendation + registration priority list

**Responsibility #2: Social Media Posting Calendar** (Ongoing, starting April 15)

- [ ] Receive weekly CX agent outputs (story + social post variants)
- [ ] Schedule 60 character posts/month (2 posts/day average)
- [ ] Maintain character diversity in posting (rotate through pool)
- [ ] Track engagement metrics (likes, comments, shares, click-through)
- [ ] Adapt posting based on performance (what characters/stories engage?)
- [ ] Report weekly: posts scheduled, engagement metrics, top performers

**Responsibility #3: Platform Monetization** (Once deployment platform chosen)

- [ ] Set up monetization API (ads, subscriptions, tips, licensing)
- [ ] Implement revenue tracking (which characters generating revenue?)
- [ ] Optimize per-character monetization (bundle? single? tiered?)
- [ ] Report weekly: revenue, chats per character, engagement per platform

---

### HISTORICAL FIGURES TEAM (Separate from fictional track, for now)

**Note**: You said focus on fictional track volume first. Historical figures can run in parallel at slower pace.

**Responsibilities** (Lower priority, existing 2 figures + candidate research):
- [ ] Continue data gathering on Tesla + da Vinci (already underway)
- [ ] Begin data gathering on 2 candidates (Marie Curie + 1)
- [ ] Build character profiles (voice, obsessions, historical training)
- [ ] Monitor for readiness → CX agent handoff (Stage 3)

**Timeline**: Can be monthly/slower pace (not bottleneck for Q2 revenue)

---

## WEEKLY OPERATIONAL RHYTHM

### Monday: Art Dept Snapshot
- Art dept reports: images generated, approved, in model queue
- Bottleneck assessment: on track, constrained, blocked?
- Model approval status: how many Tier 2 ready?

### Tuesday: Character Analyzer Batch
- Character analyzer processes approved images from previous week
- Outputs: character records (JSON), batch report
- Quality gates passed? Any reclassifications needed?

### Wednesday: CX Agent Input
- CX agent receives character records
- Generates stories, dialogue, social posts
- Outputs: story files, social media post variants

### Thursday: Social Media Scheduling
- Social media team receives CX outputs
- Schedules posts across platforms
- Confirms posting calendar for next week

### Friday: Weekly Report + Planning
- Revenue check (platform monetization tracking)
- Engagement metrics (which characters performing?)
- Bottleneck assessment (art dept capacity on track?)
- Planning: next week's target (how many images → characters?)

---

## SUCCESS METRICS (Weekly Tracking)

| Metric | Target/Week | Owner | Tracking |
|---|---|---|---|
| **Images generated** | Art dept capacity (X/week) | Art Dept | Weekly report |
| **Images approved** | ~70/month (17/week) | Joe | Approval log |
| **Character records ready** | 15/week (Tier 1) | Analyzer | Batch report |
| **CX outputs** | 15/week stories + posts | CX Agent | Output log |
| **Social posts scheduled** | 15/week (rotation) | Social Media | Posting calendar |
| **Social engagement** | Growing trajectory | Social Media | Analytics |
| **Revenue** | $X/week (goal: $96/week = $500/month) | Social Media | Platform reporting |

---

## RISK ASSESSMENT

| Risk | Impact | Mitigation |
|---|---|---|
| **Art dept bottleneck** | Production halts | Weekly capacity check, identify blockers early |
| **Archetype overlap** | Character pool becomes homogeneous | Weekly diversity report (archetype distribution) |
| **CX agent backlog** | Characters wait for story generation | Prioritize high-potential characters |
| **Platform not ready** | Revenue delayed | Parallel development, test deployment by May 1 |
| **Low social engagement** | Metrics don't improve | A/B test content types, adjust posting strategy |
| **Character analyzer fails** | Manual classification burden | Quality gates, error handling, feedback loop |

---

## COMMUNICATION STRUCTURE

**Weekly sync (Friday 2 PM, 30 mins)**:
- Joe (director)
- Art dept lead (report capacity)
- Social media lead (report engagement + post schedule)

**Bi-weekly deep dive (2nd & 4th Monday, 1 hour)**:
- Joe
- Art dept lead
- Social media lead
- Analytics review (revenue trajectory)
- Bottleneck assessment
- Next sprint planning

**Monthly all-hands (1st Friday, 1 hour)**:
- Full studio team
- Character factory status report
- Quarterly progress (toward 261 characters + $500 revenue)
- Roadmap adjustments

---

## GO-LIVE TIMELINE

### April 1-15: Setup Phase
- ✓ Art dept assessment complete (capacity quantified)
- ✓ Character analyzer tool built + tested
- ✓ CX agent ready to receive batches
- ✓ Social media calendar template ready

### April 15-30: Month 1 Execution
- ✓ First weekly batch: 15 approved images → character records → CX outputs → social posts
- ✓ Art dept producing images on schedule
- ✓ Social media posts scheduled (15/week)
- ✓ Platform analysis draft (due by April 30)

### May 1-31: Month 2 Acceleration
- ✓ Platform deployment decision finalized
- ✓ Social media content scaled (60 posts/month)
- ✓ Test 5-10 Tier 2 characters on chosen platform
- ✓ Revenue tracking begins (may be low initially, ramp expected)

### June 1-30: Month 3 Optimization
- ✓ 261 total characters in pool
- ✓ 50-60 Tier 2 characters with models
- ✓ Platform monetization live (ads/subscriptions)
- ✓ Target: $500 cumulative revenue

---

## RESOURCE ALLOCATION SUMMARY

```
Art Dept: 100% on image + model production (this is the constraint)
Joe: 10-15% oversight + approval (15-30 mins/week)
Character Analyzer Agent: 5-10 hours upfront (build) + 1-2 hours/week (batches)
CX Agent: ~7.5 hours/week (15 characters × 30 mins each)
Social Media: 10-15 hours/week (posting + analytics + platform setup)
Analyst/Admin: ~5 hours/week (data tracking, reporting)

Total studio load: ~55 hours/week (reasonable for existing team)
```

---

**This is the machine. Volume + velocity. Ready to start?**

**What I need from you immediately:**
1. Art dept capacity numbers (images/day, timeline)
2. Confirmation on ongoing go-by acquisition
3. Model creation workflow (who, timeline, parallel?)
4. Go-live date (April 15 realistic for first batch?)
