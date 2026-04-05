## PLATFORM PERFORMANCE ANALYSIS FRAMEWORK

**Objective**: One-time competitive intelligence scan of janitor.ai + crushon.ai
→ Extract character/story patterns that perform well
→ Identify underserved niches
→ Generate character/story creation requests

---

## DATA COLLECTION PHASE

### What to Scan (Both Platforms)

**Per character card:**
- Character name
- Archetype/role (inferred from description)
- Visual aesthetic (short description)
- View count
- Favorite/like count
- Comment count (proxy for engagement)
- Message/chat count (if visible)
- Date created (to assess how long it's been active)

**Per story/scenario:**
- Story title
- Character featured
- Story type (romance, adventure, mystery, slice-of-life, etc.)
- View count
- Favorite count
- Comment count
- Times duplicated (exact copies)
- Times modified/inspired (variations on theme)

### Data Structure (Spreadsheet)

```
Platform,Character_Name,Archetype,Visual_Style,Views,Favorites,Comments,Msgs_Chats,Days_Active,Performance_Score
janitor.ai,Aria,The Rebel,streetwear punk,2500,450,120,8000,180,8.2
janitor.ai,Luna,The Mysterious,goth aesthetic,1800,320,85,5200,200,7.1
crushon.ai,Zara,The Romantic,sultry elegance,3200,620,145,12000,120,9.1
[... continue for all characters on both platforms]
```

---

## ANALYSIS PHASE

### 1. Performance Scoring

**Formula**: (Views × 0.1) + (Favorites × 0.3) + (Comments × 0.5) + (Msgs/Chats × 0.1) / 100

**Why these weights?**
- Comments = highest quality engagement (people investing time)
- Favorites = curation signal (people returning)
- Msgs/Chats = monetization signal (where money is)
- Views = volume baseline (awareness)

**Result**: Ranked list of top 20 performers on each platform

### 2. Archetype Performance Analysis

**Question**: Which archetypes perform best?

```
Archetype Analysis (janitor.ai):
The Romantic: avg 8.5 score (6 characters)
The Mysterious: avg 7.8 score (8 characters)
The Rebel: avg 7.2 score (5 characters)
The Companion: avg 6.9 score (7 characters)
The Expert: avg 5.8 score (3 characters)
...
```

**Output**: Ranking of archetypes by performance
→ "Build more Romantic characters" or "Mysterious is underserved on crushon.ai"

### 3. Visual Aesthetic Clustering

**Question**: What visual styles drive engagement?

```
Top Visual Styles (by avg performance score):
- Goth/dark aesthetic: 8.2 avg (12 characters)
- Anime/manga style: 7.9 avg (8 characters)
- Realistic/photogenic: 7.1 avg (14 characters)
- Cyberpunk/tech: 6.8 avg (5 characters)
- Fantasy/magical: 6.3 avg (6 characters)
```

**Output**: Visual direction for art dept
→ "Goth characters outperform 2:1 vs. fantasy"

### 4. Story Type Analysis

**Question**: What stories get repeated, modified, duped?

```
Most Duplicated Stories (janitor.ai):
1. "First Meeting in Coffee Shop" — 47 exact copies, 120+ modifications
2. "Forbidden Love Scenario" — 34 exact copies, 95+ modifications
3. "Enemies to Lovers" — 28 exact copies, 87+ modifications
4. "Mysterious Stranger Arrives" — 22 exact copies, 63+ modifications
5. "Mentor Guidance Arc" — 15 exact copies, 41+ modifications
```

**Output**: Story templates that work
→ "Coffee shop first meeting is the template. Build 20 variations."

### 5. Niche Identification (Underserved)

**Question**: What gaps exist?

```
OVERSERVED (saturated, low growth):
- Traditional romance (500+ characters)
- Generic anime girl (200+ characters)
- Standard mentor (150+ characters)

UNDERSERVED (few competitors, high engagement when present):
- Specific profession + romance (nurse, detective, pilot) — only 8 characters, 8.7 avg score
- LGBTQ+ specific archetypes — only 12 characters, 8.1 avg score
- Age-gap romance with depth — only 6 characters, 8.4 avg score
- Dominant female + submissive male (rare reversal) — only 3 characters, 8.9 avg score
- Neurodivergent character with authentic depth — only 2 characters, 7.8 avg score
```

**Output**: Underserved niches
→ "Build 5 LGBTQ+ characters" / "Create dominant female archetypes"

### 6. Engagement Type Patterns

**Question**: Do certain character types get more comments vs. msgs?

```
Comment-Heavy (Discussion, Community Building):
- The Mysterious (avoids straight answers, generates debate)
- The Expert (people ask questions, share knowledge)
- The Rebel (people discuss ethics, morality)

Message-Heavy (1-on-1 Interaction):
- The Romantic (flirtatious engagement, private)
- The Companion (emotional, intimate conversations)
- The Bubbly (playful, lighthearted back-and-forth)
```

**Output**: Character design strategy
→ "Build Mysterious characters for community platforms, Romantic for private chat"

---

## FINDINGS SYNTHESIS

### The Output Report

**Format**: One-page strategic brief

```
PLATFORM ANALYSIS SUMMARY
Scan Date: [DATE]
Platforms: janitor.ai + crushon.ai
Characters Analyzed: [X total across both]
Stories Analyzed: [Y total across both]

TOP INSIGHTS:

1. ARCHETYPE WINNERS
   • The Romantic outperforms 35% above average (8.5 vs 6.3 baseline)
   • The Mysterious generates 2x more comments than views
   • The Rebel underperforms but has devoted niche (loyalty signal)

2. VISUAL WINNERS
   • Goth aesthetic dominates (8.2 avg score)
   • Photorealistic underperforms despite high view counts (conversion issue)
   • Anime style shows strong favorites-to-views ratio (quality signal)

3. STORY WINNERS
   • Coffee shop first meeting = 167 total versions
   • Forbidden love = 129 total versions
   • Mentor guidance = 56 total versions

4. NICHE OPPORTUNITIES
   • LGBTQ+ specific: 12 characters, 8.1 avg (underserved)
   • Dominant female + sub male: 3 characters, 8.9 avg (rare, high engagement)
   • Neurodivergent authentic: 2 characters, 7.8 avg (growing interest)

5. ENGAGEMENT PATTERNS
   • Comment-heavy = discussion-driving characters (Mysterious, Expert, Rebel)
   • Message-heavy = intimate characters (Romantic, Companion, Bubbly)

RECOMMENDATIONS FOR CHARACTER CREATION:

Tier 1 Priority (High ROI):
□ 5-7 Romantic archetypes (goth aesthetic preferred)
□ 3-5 Mysterious archetypes (anime/manga style)
□ 2-3 LGBTQ+ specific variants (underserved, high engagement)

Tier 2 Priority (Community Building):
□ 2-3 Expert archetypes (authority figures, discussion-drivers)
□ 2-3 Rebel archetypes (moral complexity, devoted following)

Tier 3 Priority (Experimentation):
□ 2-3 Dominant female archetypes (rare reversal, 8.9 score)
□ 1-2 Neurodivergent authentic characters (emerging trend)

STORY TEMPLATE REQUESTS:

Must-Build (Proven Templates):
□ Coffee shop first meeting variations (build 10+ mods)
□ Forbidden love scenarios (build 8+ mods)
□ Enemies to lovers arc (build 6+ mods)

Should-Build (Community Interest):
□ Mentor guidance arcs (build 4+ mods)
□ Mystery/secrets reveal (build 3+ mods)

Experiment (Underserved):
□ Professional romance (nurse/detective/pilot) — build 3 mods
□ Age-gap with depth (build 2 mods)
```

---

## HOW THIS FLOWS BACK TO PRODUCTION

**After analysis complete:**

1. **Art Dept Gets Feedback**:
   - "Build more goth aesthetic characters"
   - "Create 5-7 Romantic archetypes next"
   - "Experiment with dominant female designs"

2. **CX Agent Gets Story Requests**:
   - "Create 10 coffee shop meeting variations"
   - "Build forbidden love scenarios"
   - "Generate LGBTQ+ specific storylines"

3. **Character Analyzer Knows**:
   - What archetypes to prioritize
   - What visual styles to favor
   - What story contexts to emphasize

4. **Social Media Team Knows**:
   - Which characters/stories to push
   - Which platforms to focus on
   - What engagement type each character drives

---

## ONE-TIME EXECUTION

**Timeline**: One 4-6 hour analysis session

**Steps**:
1. Spend 2 hours on janitor.ai — scroll through featured characters, capture data
2. Spend 2 hours on crushon.ai — same scan
3. Spend 1-2 hours analyzing data, identifying patterns
4. Synthesize findings into one-page report
5. Generate character/story creation requests

**Tools**: Spreadsheet (Google Sheets or Excel) + whatever platform lets you browse/screenshot

**Output**: One report + list of "create next" requests fed back to art dept + CX agent

---

## THEN WATCH FLOW

Once you have:
- Art dept creating characters (from "build goth Romantic" feedback)
- CX agent getting test images (character + name + quirks + visuals)
- You approving/iterating (feedback loop)
- Social media team ready to post/track engagement

**You'll see the REAL bottleneck.**

Is it:
- Art dept speed? (can they generate fast enough)
- Approval/feedback loop? (is Joe the choke point)
- CX agent throughput? (can it handle batch size)
- Social media posting? (can they keep up with content)
- Platform engagement? (do characters actually get chats/revenue)

Right now it's invisible. Let it flow, watch where it breaks.

---

**Want me to build the analysis template you can use when you do the scan?**
