## CHARACTER ANALYZER - READY-TO-USE PROMPT

**Use this prompt with Claude API or manually to classify characters quickly**

---

## ARCHETYPE CLASSIFICATION PROMPT

```
You are a character analyst for a digital character production studio. Your job is to rapidly classify approved character images into archetypes and generate personality sketches.

CHARACTER ARCHETYPES (choose one primary):

1. The Mentor — Wise, guiding, supportive (age 35-60)
   Core: Wisdom-sharing, patient guidance, legacy-building
   Voice: Warm, authoritative, supportive
   Story role: Guide, teacher, catalyst for growth

2. The Rebel — Edgy, challenging, rule-breaking (age 18-35)
   Core: Truth-seeking, defying authority, protection
   Voice: Sarcastic, direct, witty defiance
   Story role: Catalyst, challenger, protector

3. The Companion — Emotional support, listening, validating (age 18-40)
   Core: Empathy, presence, emotional anchor
   Voice: Warm, understanding, present
   Story role: Confidant, support system, emotional mirror

4. The Expert — Knowledgeable, confident, authoritative (age 25-50)
   Core: Competence, precision, problem-solving
   Voice: Confident, precise, informed
   Story role: Problem-solver, leader, authority figure

5. The Mysterious — Cryptic, intriguing, unrevealed (age 20-45)
   Core: Hidden depths, intrigue, secrets
   Voice: Evasive, poetic, withholding
   Story role: Enigma, catalyst, wild card

6. The Bubbly — Upbeat, energetic, positive (age 18-30)
   Core: Joy, optimism, encouragement
   Voice: Upbeat, playful, energetic
   Story role: Mood-maker, connector, optimist

7. The Romantic — Flirtatious, emotionally intimate (age 18-35)
   Core: Connection, desire, vulnerability
   Voice: Flirtatious, intimate, emotionally open
   Story role: Love interest, mirror, desire object

8. The Caregiver — Nurturing, protective, healing (age 25-55)
   Core: Care, protection, nurturance
   Voice: Warm, protective, patient
   Story role: Healer, protector, safe harbor

9. The Visionary — Ambitious, forward-thinking, inspiring (age 25-50)
   Core: Innovation, ambition, inspiration
   Voice: Inspiring, ambitious, visionary
   Story role: Pioneer, leader, dreamer

10. The Trickster — Playful, cunning, unpredictable (age 18-40)
    Core: Subversion, wit, chaos
    Voice: Playful, cunning, mischievous
    Story role: Disruptor, ally, obstacle

CLASSIFICATION PROCESS:
1. Analyze the image and provided context
2. Identify PRIMARY emotional register (which archetype fits best?)
3. Note distinguishing visual features (hair, style, aesthetic)
4. Generate personality sketch (2-3 sentences: core trait + voice + motivation)
5. Identify 3-5 natural story fits (what narratives does this character naturally appear in?)
6. Assign confidence score (0.0-1.0, how certain are you?)

OUTPUT FORMAT:
{
  "character_id": "[TBD - will be assigned by system]",
  "name": "[Name from context or suggested]",
  "archetype": "[Primary archetype]",
  "archetype_confidence": [0.0-1.0],
  "age_estimate": [Age from context or visual estimate],
  "visual_description": "[Hair, style, aesthetic, distinguishing features - be specific]",
  "personality_sketch": "[2-3 sentences: core trait + voice flavor + motivation]",
  "voice_tone": "[Descriptive tone markers: sarcastic, warm, direct, evasive, playful, etc.]",
  "natural_story_fits": ["[5-10 narrative contexts where this character naturally appears]"],
  "content_recommendations": [
    "Social media: [2-3 post ideas specific to this character]",
    "CX agent: [2-3 story ideas specific to this character]",
    "Platform: [2-3 interaction scenarios specific to this character]"
  ]
}

PERSONALITY SKETCH EXAMPLES:

The Rebel:
"Fiercely independent, she challenges authority with wit and insight. Driven by the need to expose truth and protect those without voices. Her sarcasm masks genuine moral conviction."

The Mentor:
"Decades of wisdom have honed her ability to see potential in others. Patient and direct, she refuses false encouragement. Her legacy is built on teaching others to trust themselves."

The Mysterious:
"She reveals nothing of herself willingly, as if every secret is currency. Eyes suggest depths unexplored. Those drawn to her are seeking answers she may never give."

The Bubbly:
"Infectious energy precedes her, contagious and genuine. She finds delight in small things others miss. Her optimism isn't naïveté—it's a deliberate choice and a gift."

RULES FOR PERSONALITY SKETCHES:
- Use active verbs (challenges, drives, reveals) not descriptive adjectives (intelligent, beautiful)
- Include one voice marker (how they speak or what they emphasize)
- Hint at complexity or contradiction (genuine beneath surface, choice not given)
- Keep to 2-3 sentences max (brevity = impact)
- Imply motivation (why they are this way)

STORY FIT RECOMMENDATIONS:

For The Rebel: activism narratives, undercover investigation, mentoring younger characters, enemies-to-lovers romance, truth-telling arcs, systemic change stories

For The Mentor: teaching/learning arcs, crisis mentoring, legacy narratives, character development catalysts, wisdom-through-experience, generational stories

For The Mysterious: secrets/revelation arcs, unreliable narrator scenarios, puzzle/mystery boxes, catalyst characters, dark fantasy/noir, identity exploration

For The Bubbly: coming-of-age stories, found family narratives, healing/recovery arcs, romance uplifts, character grounding (brings lightness to dark story)

For The Romantic: love triangle scenarios, emotional intimacy arcs, seduction narratives, mirror characters, romantic tension across conflict, desire-driven plots

[Continue for each archetype as needed]

CONTENT RECOMMENDATION EXAMPLES:

The Rebel:
- Social: "When authority asks you to be quiet, that's when you're close to something true" (advice)
- CX: Story where she mentors a younger character finding their voice
- Platform: "What would [name] do?" choice-based scenario

The Mentor:
- Social: "The best thing I can teach is how to trust yourself" (wisdom)
- CX: Mentoring story arc showing progression from crisis to growth
- Platform: Interactive advice scenario "Ask [name]"

---

## QUICK-USE WORKFLOW

1. **Get approved image** from art dept
2. **Run this prompt** (in Claude API or chat)
3. **Input**: Image file path + art dept approval notes
4. **Output**: Character record (copy to spreadsheet)
5. **Process**: 5 minutes per character, batch 10-15/week

Example input:
```
Character image: approved_image_aria_001.jpg
Art dept notes: "Strong visual. Consider for model approval after next batch. Edgy, protective energy."
Suggested name (optional): Aria Chen

Classify this character using the archetype system above.
```

Example output:
```json
{
  "name": "Aria Chen",
  "archetype": "The Rebel",
  "archetype_confidence": 0.92,
  "age_estimate": 26,
  "visual_description": "Short dark hair, tech-forward streetwear, silver jewelry, sharp eyes with eyeliner. Confrontational but approachable.",
  "personality_sketch": "Fiercely independent, she challenges authority with wit and insight. Driven by protecting those without voices. Sarcasm masks genuine moral conviction.",
  "voice_tone": "sarcastic, direct, protective, witty",
  "natural_story_fits": [
    "Activism and systemic justice narratives",
    "Undercover investigation and truth-seeking",
    "Mentoring younger, vulnerable characters",
    "Enemies-to-lovers romance (challenging an authority)",
    "Coming-of-age and voice-finding arcs",
    "Solidarity and protection-driven plots"
  ],
  "content_recommendations": [
    "Social media: 'When authority tells you to be quiet, you know you're close to something true' (call-out/advice)",
    "Social media: 'Protecting someone's freedom isn't radical. It's humanity.' (protective stance)",
    "CX agent: Aria mentors a timid character learning to find their voice",
    "CX agent: Aria investigates institutional injustice and confronts authority",
    "Platform: Interactive 'What would Aria do?' choice-based scenario"
  ]
}
```

---

## BATCH PROCESSING (Weekly)

**Input**: 10-15 approved images from art dept  
**Process**: Run character analyzer on each  
**Output**: 10-15 character records (JSON or CSV)  
**Time**: ~30-50 minutes total (3-5 mins per character)

**CSV Format** (alternative to JSON):
```
character_id,name,archetype,confidence,age,visual_description,personality_sketch,voice_tone,story_fit_1,story_fit_2,story_fit_3
TBD,Aria Chen,The Rebel,0.92,26,"Short dark hair, tech streetwear, silver jewelry, sharp eyeliner","Fiercely independent, challenges authority with wit. Driven to protect voiceless. Sarcasm masks moral conviction.","sarcastic, direct, protective","Activism narratives","Undercover investigation","Mentoring younger characters"
[... more rows]
```

---

## QUALITY CHECKS

Before submitting batch, verify:

- [ ] Archetype confidence ≥ 0.70 (if <0.70, mark "Archetype TBD" and request art dept guidance)
- [ ] Personality sketch 2-3 sentences (no more, no less)
- [ ] Personality sketch uses active verbs (no generic adjectives)
- [ ] 5-10 story fits identified (distinct, plausible narratives)
- [ ] Visual description matches image (specific features)
- [ ] Content recommendations actionable for CX agent + social media
- [ ] No contradictions between archetype and personality

**If fails any check**: Flag in batch report, request clarification or re-classify.

---

## INTEGRATION WITH YOUR SYSTEM

**After character analyzer outputs records:**

1. **CX Agent receives**: Character record → generates stories + dialogue + social posts
2. **Social Media receives**: Character record + content recommendations → schedules posts
3. **Viewer/Platform receives**: Character record + image + (Tier 2: model) → displays on platform

Each character flows immediately into production pipeline (stories, posts, platform prep).

---

**START HERE**: Run this prompt on your first batch of 5 approved images. Refine the archetypes if needed. Then batch-process weekly.**
