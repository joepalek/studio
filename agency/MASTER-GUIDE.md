## MULTI-REFERENCE STORYTELLING SYSTEM — MASTER GUIDE

**Location**: `_studio/agency/references/`

### SYSTEM OVERVIEW

This reference system grades and organizes storytelling inputs into 6 weighted layers that feed narrative generation for your historical figures character platform.

**Goal**: Generate authentic, accurate, emotionally compelling narratives about Tesla and da Vinci through a **curated reference stack** rather than raw AI hallucination.

---

## FILE STRUCTURE & QUICK REFERENCE

```
references/
├── books-grading.csv                          ← MASTER BOOK TRACKER
├── ssid-patterns.md                           ← NARRATIVE STRUCTURE REFERENCE (5-beat arc)
├── character-profiles/
│   ├── tesla-voice.md                         ← TESLA: Language patterns, obsessions, voice
│   └── davinci-voice.md                       ← DA VINCI: Polymathic patterns, aesthetic principles
├── coast-to-coast/
│   └── episode-grades.csv                     ← C2CAM: Accuracy grades (GREEN/YELLOW/RED)
└── temporal/
    └── language-reference.md                  ← ERA-SPECIFIC VOCAB: 1450s-1920s
```

### WHAT EACH FILE DOES

| File | Purpose | Used By | Update Frequency |
|---|---|---|---|
| **books-grading.csv** | Rate books A+/A/B/C/D. Tags which reference layers they feed. | AI agents, narrative engine | Weekly (as you read) |
| **ssid-patterns.md** | 5-beat narrative arc structure + 4 variance templates | Narrative generation agents | Static (reference) |
| **tesla-voice.md** | Documented voice patterns, obsessions, authentic samples | Character override layer | Static (reference) |
| **davinci-voice.md** | Polymathic thinking, aesthetic obsession, authentic samples | Character override layer | Static (reference) |
| **episode-grades.csv** | Coast to Coast AM episode accuracy + usability rating | Intrigue layer, accuracy gate | As you watch/analyze |
| **language-reference.md** | Temporal vocab checker (1450s, 1880s, etc.) | Temporal layer, accuracy gate | Static (reference) |

---

## THE 6-LAYER PRIORITY SYSTEM

When generating narrative, your agents weight references in this order:

### LAYER 1: STRUCTURE (SSID) — 10% weight
**File**: `ssid-patterns.md`  
**Input**: 5-frame Gaussian Splatting visual sequence  
**Output**: 5-beat narrative arc (discovery → obsession → challenge → insight → legacy)  
**Rules**:
- Exactly 1 sentence per frame
- Tone progressions: invitational → intense → tense → wise → transcendent
- 70–102 words total per 5-frame post

**When it applies**: Always (every social post starts with SSID structure)

---

### LAYER 2: VOICE (Ghostwriting Books) — 20% weight
**File**: `books-grading.csv` → `accepted-A-grade/` folder  
**Input**: Books graded A+ or A  
**Output**: Professional tone patterns, narrative credibility, word choice

**Which books feed this layer**:
- ✓ Tesla: Inventor (Seifer, A+) — extract obsessive precision language
- ✓ The Electrical Age (Freeberg, A) — extract era language and technical terminology
- ✓ My Inventions (Tesla, A+) — extract direct voice patterns

**Rules**:
- Only A/A+ sources (higher grades = safer for tone)
- Extract 5–10 sentence patterns from each book
- Test: Does the agent's output "sound like" the book's prose style?

**When it applies**: All posts (tone consistency)

---

### LAYER 3: INTRIGUE (Coast to Coast AM) — 15% weight
**File**: `coast-to-coast/episode-grades.csv`  
**Input**: Episodes graded GREEN or YELLOW (not RED)  
**Output**: Mystery framing, wonder, credible speculation

**Which episodes feed this layer**:
- 🟢 GREEN: "The Renaissance Mind Revisited" (da Vinci) — factual mystery framing, all claims verified
- 🟡 YELLOW: "Lost Transmissions: Tesla's Wireless Power" — genuine unknowns (Wardenclyffe purpose), no false claims
- 🔴 RED: Skip entirely from historical track (e.g., "Suppressed Innovations," "Ancient Aliens and Leonardo")

**Rules**:
- GREEN episodes: Use framing directly ("Recent historians debate...")
- YELLOW episodes: Use with hedging ("Some suggest...", "Alternative interpretations propose...")
- RED episodes: Move to fictional character track only (never historical)

**When it applies**: Posts with mystery or intrigue angle (optional layer)

---

### LAYER 4: TEMPORAL (Era-Specific Language) — 25% weight
**File**: `temporal/language-reference.md`  
**Input**: Character + decade they're being described in  
**Output**: Era-authentic vocabulary, anachronism prevention, tone calibration

**Temporal Zones**:
- **Leonardo**: 1450s–1500s (use: dissection, proportion, mechanics, natural philosophy)
- **Tesla**: 1880s–1920s (use: electricity, wireless, oscillation, frequency, invention)

**Rules**:
- Before posting: Run narrative through **Temporal Gate checklist**
- Mark percentage of sentences using era vocabulary (should be 10–15%)
- Reject if anachronisms detected (e.g., Tesla using "quantum")

**When it applies**: All posts with historical anchoring (timestamps, era references)

---

### LAYER 5: CHARACTER (Personality Fingerprint) — 30% weight — HIGHEST PRIORITY
**Files**: `tesla-voice.md`, `davinci-voice.md`  
**Input**: Character's documented language patterns, obsessions, authentic voice samples  
**Output**: Personality authenticity that overrides all other layers

**Tesla personality checklist**:
- [ ] Language contains precision/exactness markers
- [ ] Tone is visionary but grounded in theory (not fantasy)
- [ ] No emotional vulnerability or commercial motivation
- [ ] Obsession with resonance/frequency evident
- [ ] Third-person authority or formal tone
- [ ] Grandiose aspiration framed as "benefit to mankind"

**da Vinci personality checklist**:
- [ ] Statement connects TWO disciplines (not isolated expertise)
- [ ] Aesthetic observation reveals underlying principle
- [ ] Precision in visual/technical detail evident
- [ ] Wonder or curiosity tone present
- [ ] No frustration with incompletion (frame as deepening inquiry)
- [ ] Polymathic synthesis explicit

**Rules**:
- Character voice always wins when it conflicts with other layers
- If a narrative reads "correct" structurally but sounds wrong for the character → reject and regenerate
- Use authentic voice samples from .md files as guardrails

**When it applies**: All posts (identity integrity)

---

### LAYER 6: ACCURACY GATE (Fact-check) — Applied LAST
**Files**: `books-grading.csv`, `coast-to-coast/episode-grades.csv`, `temporal/language-reference.md`  
**Input**: Final narrative before posting  
**Output**: Fact-check pass/fail, accuracy tags

**Gate process**:
1. **Identify every factual claim** in the narrative
2. **Tag each claim**:
   - ✓ **Verified fact** (in A/A+ biography, primary source, scholarly consensus)
   - ? **Ambiguous/debated** (multiple interpretations exist, must flag explicitly in post: "Some historians suggest...")
   - ✗ **Unverified** (not in reference sources, reject for historical track or move to fiction track)
3. **Apply rules**:
   - Historical figures track: ✗ claims not permitted (0 tolerance)
   - Fictional character track: ✗ claims permitted (label as fiction)

**Example accuracy tags**:
```
Narrative: "Tesla investigated wireless transmission of energy through the earth's electrical field."
Claim 1: "wireless transmission" = ✓ VERIFIED (documented in biographies, patents, My Inventions)
Claim 2: "through the earth's electrical field" = ? AMBIGUOUS (Tesla theorized this; not verified)
Claim 3: "electrical field" = ✓ VERIFIED (supported by contemporary physics)
→ Result: PASS (no ✗ unverified claims)

---

Narrative: "Tesla made contact with Martian radio signals."
Claim: "contact with Martian signals" = ✗ UNVERIFIED (no evidence, contradicted by biographies)
→ Result: FAIL (historical track). PASS (fictional track with explicit fiction label)
```

---

## WORKFLOW: HOW A POST GETS CREATED

### STEP 1: Visual Generation
Your **image generation agent** creates a 5-frame Gaussian Splatting sequence of the character in a specific moment.

**Example**: Tesla in his lab working on the oscillating circuit (5 frames showing his progression through investigation)

### STEP 2: Narrative Layer 1 (Structure)
Narrative agent reads `ssid-patterns.md` and generates the 5-beat arc skeleton:

```
DISCOVERY: [Context sentence about Tesla in lab]
OBSESSION: [Intensity of investigation sentence]
CHALLENGE: [Obstacle or realization sentence]
INSIGHT: [What he discovers sentence]
LEGACY: [How this matters to us sentence]
```

→ Output: Bare 5-beat structure (no character voice, no era language yet)

### STEP 3: Narrative Layer 2 (Voice)
Agent reads `tesla-voice.md` and infuses the 5-beat structure with Tesla's voice patterns.

**Before**: "He worked on the oscillator for a long time, trying to find the right frequency."  
**After**: "For years, he refined the oscillating circuit with an exactness that bordered on obsession, seeking the precise frequency that would unlock the earth's electrical properties."

→ Output: 5-beat arc + Tesla voice layer

### STEP 4: Narrative Layer 3 (Optional Intrigue)
If the post is about a mysterious aspect of Tesla's work, agent reads `coast-to-coast/episode-grades.csv` and considers adding mystery framing.

**Example**: If post is about Wardenclyffe project (genuine historical unknown):
- Check episode grades: "Lost Transmissions: Tesla's Wireless Power" = YELLOW
- Add hedging: "Recent historians debate the true purpose of Tesla's Wardenclyffe tower..."
- Use the framing from episode (verified against A+ sources first)

→ Output: 5-beat arc + voice + optional intrigue layer

### STEP 5: Narrative Layer 4 (Temporal Anchoring)
Agent reads `temporal/language-reference.md` for the era being depicted and runs **Temporal Gate checklist**.

**If post is set in 1893 (Tesla's Polyphase era)**:
- Check: Is "oscillating circuit" the right term? (Yes, documented for that era)
- Check: No anachronisms like "quantum"? (Correct)
- Verify: 10–15% of sentences use era-specific language? (Adjust if needed)

→ Output: 5-beat arc + voice + intrigue + temporal authenticity

### STEP 6: Narrative Layer 5 (Character Override)
Agent verifies final narrative against character checklists in `tesla-voice.md`.

**Checklist**:
- ✓ Precision/exactness language?
- ✓ Visionary but grounded?
- ✓ No emotional vulnerability?
- ✓ Obsession apparent?
- ✓ Grandiose aspiration as "benefit to mankind"?

If any fail → Regenerate sentence

→ Output: Complete 5-beat narrative with full character authenticity

### STEP 7: Accuracy Gate (Final Pass)
Agent reads final narrative and tags every factual claim against reference sources:

**Each claim gets a tag**:
- ✓ **Verified** (in books-grading.csv A+ sources, primary source, scholarly consensus)
- ? **Ambiguous** (in C2CAM GREEN/YELLOW, multiple interpretations documented)
- ✗ **Unverified** (not in references, contradicted by sources)

**Decision**:
- Historical figures track: All claims must be ✓ or ? (with hedging)
- Reject if any ✗ claims appear

→ Output: Final narrative + accuracy tags

### STEP 8: Generate 4 Variants
Repeat steps 1–7 four times with **different narrative emphasis** (using `ssid-patterns.md` variance templates):
- **Variant A**: Obsession-focused
- **Variant B**: Discovery-focused
- **Variant C**: Sacrifice-focused
- **Variant D**: Wonder-focused

All 4 variants maintain character voice, temporal authenticity, and accuracy.

### STEP 9: Joe's Approval Checkpoint #2
Joe sees:
- Visual batch (5-frame renders)
- 4 narrative variants (each with reference layer breakdown)
- Accuracy tags on each variant

**Joe selects**: One variant to schedule

→ Output: Approved social post ready for scheduling

---

## QUICK-START: WHAT YOU NEED TO DO NOW

### Week 1: Populate Reference Files

**Task 1: Grade books you're reading**
- Open `books-grading.csv`
- Add each book you've read (or plan to read)
- Grade A+/A/B/C/D
- Tag which layers it feeds (tone? accuracy? character voice?)
- **Estimate: 30 min for 5 books**

**Task 2: Analyze Coast to Coast AM**
- Open `coast-to-coast/episode-grades.csv`
- Watch 3–5 C2CAM episodes relevant to Tesla or da Vinci
- Grade each: GREEN / YELLOW / RED
- Note usable framing for YELLOW episodes
- **Estimate: 2 hours for 5 episodes**

**Task 3: Verify character voice files**
- Read through `tesla-voice.md` and `davinci-voice.md`
- Highlight sections that feel off or incomplete
- Add any personal observations about each character's voice
- **Estimate: 45 min**

### Week 2–3: Test the System

**Task 4: Generate 1 test narrative**
- Pick 1 character (Tesla or da Vinci)
- Pick 1 historical moment
- Run through all 6 layers manually (use this guide as checklist)
- Generate 4 variants
- Give Joe the 4 options for approval

**This tests whether the reference stack is working before you automate it.**

---

## INTEGRATION WITH YOUR AGENCIES

### CX Agent
- Reads character-profiles/*.md for tone consistency
- Applies ghostwriting layer (professional credibility)

### Social Media Agent
- Reads ssid-patterns.md for 5-beat structure
- Reads coast-to-coast/episode-grades.csv for intrigue options
- Reads temporal/language-reference.md for era accuracy
- Reads character-profiles/*.md for personality override

### Image Generation Agent
- No direct reference reads (generates visuals)
- Outputs 5-frame sequence for narrative agents to ingest

### Narrative Engine (New)
- Orchestrates all 6 layers in priority order
- Applies accuracy gate
- Generates 4 variants
- Hands to Joe at Checkpoint #2

---

## MAINTENANCE & UPDATES

**Monthly**:
- Review new books read → Update books-grading.csv
- Review new C2CAM episodes → Update episode-grades.csv

**As needed**:
- Character profile discoveries → Update tesla-voice.md or davinci-voice.md
- Temporal language questions → Add examples to temporal/language-reference.md
- SSID pattern learnings → Update ssid-patterns.md

**Never**:
- Change character files retroactively (consistency matters)
- Add RED-graded sources to historical narratives
- Ignore temporal gate failures

---

## TROUBLESHOOTING

**Problem**: Narrative sounds stiff or overly formal
**Solution**: Increase SSID emphasis (layer 1) — the 5-beat structure should feel dynamic, not robotic

**Problem**: Narrative lacks character authenticity
**Solution**: Check character checklist in character-profiles/*.md — likely missing obsession theme or personality fingerprint

**Problem**: Accuracy gate fails (✗ unverified claims appear)
**Solution**: Check books-grading.csv — likely sourced from D-graded or ungraded book. Rebuild narrative using only A/A+ sources

**Problem**: Narrative sounds anachronistic (1893 Tesla using 1950s language)
**Solution**: Run Temporal Gate checklist in temporal/language-reference.md — adjust vocabulary

**Problem**: Multiple variants feel too similar
**Solution**: Use ssid-patterns.md variance templates more explicitly — emphasize different beats (obsession vs. discovery vs. sacrifice vs. wonder)

---

**System Status**: ✓ INSTALLED AND READY

Next step: Let's talk about your characters in detail and how these layers apply to each one.
