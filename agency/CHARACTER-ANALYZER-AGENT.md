## CHARACTER ANALYZER AGENT SPECIFICATION

**Purpose**: Ingest approved character images → output character records with role fit + personality sketch

**Input**: Image file + art dept approval metadata  
**Output**: Character record (JSON or CSV row) ready for CX agent + social media  
**Processing Time**: 2-5 minutes per character  
**Weekly Batch**: 10-15 characters  

---

## CHARACTER RECORD SCHEMA

```json
{
  "character_id": "FIC-2026-0847",
  "name": "Aria Chen",
  "created_date": "2026-04-04",
  "source_image": "approved_image_aria_chen_001.jpg",
  "image_approval_date": "2026-04-04",
  
  "archetype": "The Rebel",
  "archetype_primary_traits": ["independent", "truth-seeker", "protective", "witty"],
  "archetype_confidence": 0.92,
  
  "age_estimate": 26,
  "gender_presentation": "Female",
  "visual_style": "tech-forward streetwear",
  "distinctive_features": "short dark hair, eyeliner, silver jewelry",
  
  "personality_sketch": "Fiercely independent, challenges authority with wit and insight. Driven by the need to expose truth and protect those without voices. Speaks with sarcasm masking genuine care.",
  "personality_depth": "Tier 1",
  
  "voice_tone": "sarcastic, direct, protective, witty",
  "voice_patterns": ["defiant humor", "moral clarity", "emotional honesty"],
  
  "natural_story_fits": [
    "activism narratives",
    "undercover investigation",
    "mentoring younger characters",
    "enemies-to-lovers romance",
    "truth-telling arcs"
  ],
  
  "content_recommendations": [
    "Social media: rebellious advice, call-out posts, protective mentoring",
    "CX agent: stories involving injustice, truth, protection",
    "Stories with: vulnerable companion character, authoritarian villain, seeker character"
  ],
  
  "tier_status": "Tier 1 (Image approved)",
  "tier_1_ready_date": "2026-04-04",
  "model_approval_eligible": true,
  "character_depth_eligible": false,
  
  "art_dept_notes": "Strong visual. Consider for model approval after next batch settles.",
  "ai_notes": ""
}
```

---

## ARCHETYPE CLASSIFICATION SYSTEM

### Primary Archetypes (10 Female-Heavy Roles)

| Archetype | Core Driver | Age Range | Voice Tone | Story Role |
|---|---|---|---|---|
| **The Mentor** | Wisdom-sharing, guiding | 35-60 | Warm, authoritative, supportive | Guide, teacher, wise elder |
| **The Rebel** | Truth-seeking, rule-breaking | 18-35 | Sarcastic, direct, defiant | Catalyst, challenger, protector |
| **The Companion** | Emotional support, listening | 18-40 | Empathetic, validating, present | Confidant, support, anchor |
| **The Expert** | Competence, knowledge-sharing | 25-50 | Confident, precise, authoritative | Problem-solver, leader, authority |
| **The Mysterious** | Intrigue, hidden depths | 20-45 | Cryptic, poetic, evasive | Enigma, secret-keeper, wild card |
| **The Bubbly** | Joy, encouragement, positivity | 18-30 | Upbeat, energetic, playful | Mood-maker, optimist, connector |
| **The Romantic** | Emotional intimacy, connection | 18-35 | Flirtatious, vulnerable, intimate | Love interest, desire, mirror |
| **The Caregiver** | Nurturing, protection, healing | 25-55 | Warm, protective, patient | Healer, protector, nurturer |
| **The Visionary** | Ambition, innovation, inspiration | 25-50 | Inspiring, ambitious, forward-thinking | Pioneer, leader, dreamer |
| **The Trickster** | Playfulness, subversion, cunning | 18-40 | Playful, cunning, unpredictable | Disruptor, ally, obstacle |

### Classification Decision Tree

```
START: Analyze image + context
  ↓
Q1: PRIMARY EMOTIONAL REGISTER?
  → Wise/patient → THE MENTOR
  → Edgy/challenging → THE REBEL
  → Warm/supportive → THE COMPANION or THE CAREGIVER
  → Confident/knowledgeable → THE EXPERT
  → Mysterious/withdrawn → THE MYSTERIOUS
  → Bubbly/energetic → THE BUBBLY
  → Flirtatious/intimate → THE ROMANTIC
  → Ambitious/forward → THE VISIONARY
  → Playful/cunning → THE TRICKSTER
  ↓
Q2: SECONDARY TRAIT (confidence level)?
  → If high confidence (>0.85): Primary archetype is final
  → If medium confidence (0.70-0.85): Secondary archetype possible
  → If low confidence (<0.70): Ask for art dept guidance
  ↓
OUTPUT: Primary archetype + confidence score
```

### Historical Figure Archetypes (If Applicable)

| Archetype | Definition | Examples |
|---|---|---|
| **The Pioneer** | Groundbreaker, rule-breaking innovator | Tesla (wireless transmission), da Vinci (art-science) |
| **The Scholar** | Intellectual, obsessive researcher | Marie Curie (radioactivity), Stephen Hawking (physics) |
| **The Artist** | Creative, aesthetic, expressive | Frida Kahlo (self-expression), Bob Dylan (lyricist) |
| **The Strategist** | Systems-thinker, planner, ambitious | Alan Turing (computational theory), Napoleon (military) |

---

## PERSONALITY SKETCH GENERATION

**Template**: [Core trait] + [voice flavor] + [primary motivation]

**Formula**:
```
"{Primary trait sentence}. {Secondary emotional characteristic}. {Core motivation statement}."
```

**Examples**:

1. **The Rebel**:
   "Fiercely independent, challenges authority with wit and insight. Driven by the need to expose truth and protect those without voices. Speaks with sarcasm masking genuine care."

2. **The Mentor**:
   "Decades of wisdom have honed her ability to see potential in others. Patient and direct, she refuses false encouragement. Her legacy is built on teaching others to trust themselves."

3. **The Mysterious**:
   "She reveals nothing of herself willingly, as if every secret is currency. Eyes suggest depths unexplored, a past unspoken. Those drawn to her are seeking answers she may never give."

4. **The Bubbly**:
   "Infectious energy precedes her into every room, contagious and genuine. She finds delight in small things others miss. Her optimism isn't naïveté—it's a choice and a gift to those around her."

---

## PERSONALITY SKETCH RULES

**Do:**
- ✓ Use active, evocative language (verbs > adjectives)
- ✓ Hint at complexity (contradiction, hidden depth, duality)
- ✓ Include one voice marker (how they speak, what they emphasize)
- ✓ Imply motivation (why they are this way, what drives them)
- ✓ Keep to 2-3 sentences (brevity = punch)

**Don't:**
- ✗ Use generic traits ("nice," "smart," "pretty")
- ✗ Over-explain (let readers infer depth)
- ✗ Contradict the archetype (rebel should challenge, mentor should guide)
- ✗ Use clichés ("broken past," "mysterious stranger")

---

## VISUAL ANALYSIS CHECKLIST

**When analyzing approved image, note:**

| Element | Analysis |
|---|---|
| **Color palette** | Warm/cool? Bold/muted? What does it suggest about personality? |
| **Style/Fashion** | Formal/casual? Coordinated/eclectic? What does it signal? |
| **Hair/Appearance** | Conventional? Unconventional? Carefully maintained or deliberately undone? |
| **Facial Expression** | Guarded/open? Confident/uncertain? Warm/cold? Knowing/naive? |
| **Body Language** | Confrontational/withdrawn? Engaged/detached? Relaxed/tense? |
| **Overall Aesthetic** | Tech-forward? Vintage? Natural? Edgy? Soft? Mysterious? |

---

## STORY FIT RECOMMENDATIONS

**Based on archetype, suggest 3-5 narrative contexts where character naturally appears:**

### The Rebel
- Activism narratives (justice, systemic change)
- Undercover investigation (exposing truth)
- Mentoring younger characters (protection, guidance)
- Enemies-to-lovers romance (challenging a superior)
- Coming-of-age stories (finding voice)

### The Mentor
- Teaching/learning arcs (knowledge transfer)
- Crisis mentoring (guiding through chaos)
- Legacy narratives (what endures after)
- Character development (catalyst for growth)
- Wisdom-through-experience narratives

### The Romantic
- Love triangle scenarios (desire, choice, consequence)
- Emotional intimacy arcs (vulnerability + connection)
- Seduction/pursuit narratives (attraction, chemistry)
- Mirror characters (what we want to see in ourselves)
- Romantic tension across conflict (forbidden love)

### The Mysterious
- Secrets/revelation arcs (what is hidden, why?)
- Unreliable narrator scenarios (what is real?)
- Catalyst characters (disrupting comfort)
- Puzzle/mystery boxes (solving the unknown)
- Dark fantasy/noir (shadowed motivations)

---

## CONTENT RECOMMENDATION EXAMPLES

**The Rebel (Aria Chen)**:
```
Social Media:
- "When authority asks you to be quiet, that's when you know you're close to something true." (advice/call-out)
- "Protecting someone else's freedom isn't radical. It's basic humanity." (protective stance)
- "Sarcasm is just honesty with a smile." (voice/wit)

CX Agent Stories:
- Aria mentoring a younger character learning to find their voice
- Aria investigating institutional injustice
- Aria confronting an authority figure with evidence they can't deny
- Aria protecting someone vulnerable at personal cost
- Aria and a rule-following character finding common ground

Platform Content:
- Story where she's a sidekick character (rebellion arc)
- Story where she's a lead character (truth-seeking main plot)
- Interactive scenario: "What would Aria do?" (choice-based)
- Romantic scenario: "Aria meets her match" (enemies-to-lovers)
```

**The Mentor (Helena, age 52)**:
```
Social Media:
- "You don't have to be perfect to be worthy. You have to be willing to learn." (wisdom-sharing)
- "The best thing I can teach is how to trust yourself." (guidance)
- "Mistakes are just data. Use them." (perspective)

CX Agent Stories:
- Helena guiding a younger character through a crisis
- Helena reflecting on her own learning journey
- Helena and a stubborn character finding unexpected connection
- Helena teaching a skill, revealing herself through teaching
- Helena passing a torch (legacy narrative)

Platform Content:
- Interactive wisdom: "Ask Helena" (advice character)
- Mentoring story arc (5-7 posts showing progression)
- Generational story (mentor + student)
- Romantic possibility: "Helena finds unexpected love" (age-inclusive)
```

---

## PROCESSING WORKFLOW

### Weekly Batch (10-15 characters)

**INPUT**: 
- 10-15 approved character images
- Art dept approval metadata (date, notes, tier eligibility)
- Optional: Character name or reference notes

**PROCESS** (2-5 mins per character):
1. Visual analysis → Archetype classification
2. Personality sketch generation → Story fit identification
3. Content recommendations → Character record assembly
4. Quality check → Output generation

**OUTPUT**: 
- Character record JSON/CSV (one per character)
- Batch report (archetype distribution, tier readiness)
- Social media content suggestions (5-10 per character)
- CX agent input file (ready for story generation)

### Weekly Batch Example Output

```
WEEKLY BATCH: 2026-04-04 to 2026-04-10 (12 characters approved)

Character Summary:
FIC-2026-0847: Aria Chen (The Rebel, age 26) — Tier 1
FIC-2026-0848: Helena Rodriguez (The Mentor, age 52) — Tier 1
FIC-2026-0849: Maya Tanaka (The Mysterious, age 31) — Tier 1
[... 9 more characters]

Archetype Distribution:
- The Rebel: 3 characters (25%)
- The Mentor: 2 characters (17%)
- The Mysterious: 2 characters (17%)
- The Companion: 2 characters (17%)
- The Expert: 2 characters (17%)
- The Romantic: 1 character (8%)

Tier 1 Ready: 12/12 (100%)
Model Approval Eligible: 11/12 (92%)
Character Depth Eligible: 2/12 (17%)

Recommended CX Agent Assignments:
- Aria Chen: Stories #5, #12, #18 (rebellion, mentoring, romance)
- Helena Rodriguez: Stories #3, #22 (wisdom, crisis guidance)
- Maya Tanaka: Stories #7, #15, #20 (mystery, catalyst, unrevealed)
[... more assignments]

Social Media Content Ready: 60 post variants (5 per character)
```

---

## QUALITY GATES

**Character record passes QA if:**
- [ ] Archetype classification ≥ 0.70 confidence
- [ ] Personality sketch ≤ 3 sentences, uses active voice
- [ ] 3-5 story fits identified (plausible + distinct)
- [ ] Visual description matches image (objective features)
- [ ] Content recommendations actionable for CX agent + social media
- [ ] No contradictions between archetype + personality + story fits

**If any gate fails:**
- Low confidence archetype (<0.70) → Ask art dept for guidance, assign "Archetype TBD"
- Weak personality sketch → Regenerate using template
- No story fits → Error in classification, reclassify
- Vague visual description → List specific observable features

---

## INTEGRATION POINTS

### Input from Art Dept
```
Approved image → Art dept metadata → Character analyzer
```

### Output to CX Agent
```
Character record → CX agent story assignment → Story + dialogue generation
```

### Output to Social Media
```
Character record + content recommendations → Social media posting calendar
```

### Output to Viewer/Platform
```
Character record + image + (Tier 2: model) → Web viewer / janitor.ai export
```

---

## IMPLEMENTATION NOTES

**Tool**: Can be built as:
- Python script (rapid classification + personality generation)
- Claude API wrapper (using character-profiles logic + archetype system)
- Automated workflow (Zapier/Make with manual checkpoints)
- Web form (UI for art dept to input notes, auto-generate record)

**Recommended**: Claude API agent reading character-profiles/*.md files + archetype system, outputting JSON character records.

**Timeline**: Buildable in 2-3 hours once archetype definitions finalized.

**Dependencies**:
- Character archetype definitions (this doc)
- Story fit library (what each archetype does in narratives)
- CX agent input format (what it expects from character records)
- Social media posting template (what format for recommendations)

---

**Ready to build this, or need adjustments to archetype system first?**
