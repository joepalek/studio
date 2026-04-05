## CX AGENT → JOE APPROVAL LOOP

**Flow**: CX Agent creates test images + character details → Joe reviews + gives feedback → Loop until approved → Goes to production

---

## WHAT CX AGENT OUTPUTS (Test Phase)

Per character, CX agent creates:

```
Character ID: [Pending approval]
Name: [Generated or suggested]
Archetype: [Classification from analyzer or provided]

VISUAL TEST VARIANTS (2-3 options):
- Image A: [First visual interpretation]
- Image B: [Second visual interpretation]  
- Image C: [Third visual interpretation]

CHARACTER DETAILS:
- Age: [Estimate]
- Personality Sketch: [2-3 sentences]
- Voice Tone: [Descriptive markers]
- Quirks/Backstory: [Key personality hooks]
- Visual Aesthetic: [Description of how they look]

STORY FIT SAMPLES:
- Sample story 1: [3-5 sentence scene featuring character]
- Sample story 2: [Different story context]

SOCIAL MEDIA SAMPLES:
- Post variant 1: [Example social post for this character]
- Post variant 2: [Different tone/context]
```

**Example Output**:

```
Character ID: [PENDING APPROVAL]
Name: Jasmine (suggested) / [Your alternative]
Archetype: The Romantic

VISUAL TEST VARIANTS:
- Image A: Sultry elegance — red dress, dark hair, confident eye contact
- Image B: Soft romantic — flowing pastel dress, gentle aesthetic, vulnerable expression
- Image C: Androgynous elegance — sharp tailoring, ambiguous presentation, mysterious eyes

CHARACTER DETAILS:
Age: 28
Personality: Flirtatious and emotionally open, but with carefully guarded boundaries. She knows what she wants and isn't afraid to pursue it, yet there's depth beneath the charm—a past she hasn't fully processed.
Voice Tone: flirtatious, vulnerable, confident, witty
Quirks: Collects vintage perfume bottles. Writes late-night letters she never sends. Laughs at her own jokes before delivering the punchline.
Visual Aesthetic: High femme, vintage-inspired, confident posture, expressive hands

STORY FIT SAMPLES:
Story 1: "Jasmine walked into the gallery opening knowing exactly what she wanted—or at least, that's what she told herself. The man by the abstract painting looked up. Their eyes met. Three seconds of recognition. She turned away first. Always, she turned away first."

Story 2: "Her best friend asked why she always picked emotionally unavailable people. Jasmine laughed. 'They're not unavailable,' she said. 'They're just scared. I respect that.' What she didn't say: so am I."

SOCIAL MEDIA SAMPLES:
Post 1: "Vulnerability isn't weakness. It's just honesty on display. Some people are brave enough to watch."

Post 2: "They say you can't have it all. I say they weren't trying hard enough."
```

---

## APPROVAL FORM (What Joe Sees)

**Template for Joe to fill out:**

```
CHARACTER APPROVAL FORM

Character Name Options: [A] Jasmine / [B] ___________ / [C] ___________
☐ Name fits character ✓
☐ Need to change name → suggested: ___________

VISUAL AESTHETIC:
☐ Image A appeals most
☐ Image B appeals most  
☐ Image C appeals most
☐ Hybrid feedback: ___________

Visual Cohesion:
☐ Visuals match personality sketch
☐ Visuals feel off, feedback: ___________

Quirks/Backstory:
☐ Quirks feel authentic and interesting
☐ Delete quirk: ___________, because: ___________
☐ Add quirk: ___________, because: ___________
☐ Modify backstory: ___________

Archetype Fit:
☐ Archetype matches character
☐ This is more like: ___________ archetype
☐ This is a hybrid: ___________ + ___________

Character Ready?:
☐ APPROVE - Send to production image bank
☐ ITERATE - Apply feedback and resubmit
☐ REJECT - Start fresh, reason: ___________

Iteration Feedback (if needed):
[Write specific direction for CX agent to revise]

______________
Joe's sign-off
```

---

## ITERATION LOOP (If Not Approved)

**If Joe says ITERATE:**

CX agent receives feedback and regenerates:

```
ITERATION 1 FEEDBACK FROM JOE:
- Change name to "Vera"
- Combine Image B (visual) + Image A (confidence vibe)
- Delete "writes late-night letters" quirk (too cliché)
- Add: "photographs strangers without permission (ethically gray quirk)"
- This needs more edge, less pure romance

CX AGENT REVISION:
Character ID: [PENDING - ITERATION 1]
Name: Vera (UPDATED)
Archetype: The Romantic (with Rebel edge)

VISUAL TEST (REVISED):
- Image: [B base visual + A confidence posture/eye contact]

CHARACTER DETAILS (REVISED):
Age: 28
Personality: Flirtatious and bold, but with an edge of defiance. She photographs people without permission—capturing the moment they become themselves. Charming on surface, uncompromising underneath.
Voice Tone: flirtatious, defiant, sharp, playful
Quirks: Photographs strangers (her art form). Wears vintage everything. Speaks three languages but refuses to use them "correctly."
Visual Aesthetic: [Combines B softness with A edge]

[Resubmit for approval]
```

**Loop until**: Joe approves → Character goes to production

---

## PRODUCTION HANDOFF (Approved)

Once Joe approves:

```
CHARACTER APPROVED FOR PRODUCTION

Character ID: FIC-2026-0001 (assigned)
Name: Vera
Status: APPROVED

FINAL SPECS:
- Visual: [Approved image + aesthetic notes]
- Personality: [Approved sketch]
- Voice: [Approved tone markers]
- Quirks: [Approved list]
- Archetype: [Approved classification]
- Story fits: [Approved contexts]

NEXT STEPS:
→ Art Dept: Create full image bank from approved visual spec
→ Character Analyzer: Classify officially, generate story fit recommendations
→ CX Agent: Generate production stories + social posts
→ Social Media: Add to posting calendar

CHARACTER READY FOR DEPLOYMENT
(Can be used as actor in scripts, persona interaction, cross-context recall)
```

---

## WORKFLOW SPEED

**Per character iteration cycle:**
- CX generates test (30 mins)
- Joe reviews + feedback (15 mins)
- CX revises (20 mins)
- Joe approves (5 mins)
- **Total: ~1 hour per character** (if approved on first or second iteration)

**If in approved state**: Can move 5-10 characters/day through full cycle

---

## WHERE THE BOTTLENECK REVEALS ITSELF

**Scenario 1: Joe is bottleneck**
- CX submitting 5+ characters/day
- Joe can only approve 2/day
- Backup forms, slower flow
- **Action**: Delegate approval to art dept lead or create clearer approval criteria

**Scenario 2: CX Agent is bottleneck**
- Art dept ready with images
- CX can only process 2/day
- Backlog at CX input
- **Action**: Increase CX batch size or parallel processing

**Scenario 3: Art Dept is bottleneck**
- Joe approving fast
- CX generating fast
- Art dept can't create image bank fast enough
- **Action**: Art dept needs more capacity or focus

**Scenario 4: No bottleneck (sweet spot)**
- Smooth flow through all stages
- Characters approved → produced → posted same week
- **Action**: Increase input (more references from analyzer)

---

## TRACKING THE FLOW

**Weekly Dashboard**:

```
FLOW METRICS (Week of [DATE]):

CX Agent Submissions: 8 characters
Joe Approvals: 6 characters
Joe Rejections: 1 character (restarting)
Joe Iteration Requests: 1 character (round 2)

Approval Rate: 75% (6/8)
Iteration Rate: 12.5% (1/8)
Rejection Rate: 12.5% (1/8)

Average Iteration Cycles: 1.2 per character
Average Time to Approval: 2.1 days
Bottleneck Status: ☐ Smooth ☐ Tightening ☐ Blocked

Next week targets: 10 submissions (scaling up)
```

---

**Once you get flow established:**

The real bottleneck becomes visible. Then you optimize THAT.

Right now, optimize for **getting characters MOVING**, not perfection.

---

**Ready to start test batch? Or do you need this structured differently?**
