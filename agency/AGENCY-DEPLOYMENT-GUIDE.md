# AGENCY PIPELINE — DEPLOYMENT GUIDE

## Status: ✅ OPERATIONAL

All components validated, tested, and ready for deployment.

---

## FILES TO DEPLOY

Copy these 5 files to: `G:\My Drive\Projects\_studio\agency\`

```
cx-agent-asset-types.json
cx-agent-main.py
digital-double-trainer.py
image-generation-agent.py
social-media-agent.py
agency-pipeline-demo.py
```

---

## WORKFLOW ARCHITECTURE

```
CHARACTER SPEC GENERATOR (daily, 300 specs)
  ↓
MIROFISH AUTO-GRADING (8+ pass)
  ↓
CX AGENT (Traffic Cop)
  ├─ Validate spec
  ├─ Create asset log
  ├─ Queue Digital Double Trainer
  │
  ├─ ⏸ CHECKPOINT 1 (USER)
  │   "Select visual (1-5) + voice (1-5)"
  │   → Blocks until approval
  │
  ├─ Train LoRA + voice models (~60 min)
  ├─ Queue Image Generation
  ├─ Generate 50 images
  │
  ├─ ⏸ CHECKPOINT 2 (USER)
  │   "Review first batch, approve or reject"
  │   → Blocks until approval
  │
  └─ Route to Social Media Agent
       ↓
SOCIAL MEDIA AGENT
  ├─ Generate captions (character voice)
  ├─ Post to: Instagram, TikTok, Twitter, Discord, YouTube, Email
  ├─ Log interactions to character-interaction-log.json
  └─ Daily engagement tracking
```

---

## APPROVAL CHECKPOINTS

### Checkpoint 1: Visual + Voice Selection
- **When:** After Digital Double Trainer generates 5 visual + 5 voice options
- **Your Action:** Select 1 visual option (1-5) and 1 voice option (1-5)
- **Blocks:** Model training until approved
- **Expected Duration:** 5-10 minutes

### Checkpoint 2: First Batch Review
- **When:** After Image Generation Agent completes 50-image batch
- **Your Action:** Review sample images (5-10 shown), approve/reject/request variations
- **Blocks:** Social media posting until approved
- **Expected Duration:** 10-15 minutes

---

## RUNNING THE PIPELINE

### Option 1: Full Interactive Mode (Recommended)
```bash
python cx-agent-main.py
```

This will:
1. Load passing specs from `spec-queue/passing-specs.json`
2. Process each spec through full workflow
3. Pause at each checkpoint for your approval
4. Continue automatically once approved

### Option 2: Demo Mode (Testing)
```bash
python agency-pipeline-demo.py
```

Shows complete workflow without requiring input.

---

## DAILY OPERATION

### Task Scheduler Setup

**Task 1: Process Daily Character Specs**
- **Trigger:** Daily at 2:00 AM
- **Command:** `python G:\My Drive\Projects\_studio\agency\cx-agent-main.py`
- **Action:** Processes passing specs through full workflow

**Task 2: Generate Daily Images** (after training completes)
- **Trigger:** Daily at 4:00 AM
- **Command:** `python G:\My Drive\Projects\_studio\agency\image-generation-agent.py`
- **Action:** Generates 50 images per trained character

**Task 3: Daily Social Media Review & Posting** (TRAINING WHEELS MODE)
- **Trigger:** Daily at 6:00 AM
- **Command:** `python G:\My Drive\Projects\_studio\agency\social-media-agent.py`
- **Action:** 
  - First 24 posts: Shows you posts, awaits approval (✓/✗)
  - After 24 approved: Auto-posts without approval needed
  - All interactions logged to engagement database

---

## DATA STRUCTURES

### Asset Type: Character

**Input:**
- Character spec (from Mirofish grading, 8+ score)
- Personality traits, voice, visual description, backstory

**Output:**
- Trained LoRA model (visual consistency)
- Trained voice model (audio consistency)
- 50+ generated images per character
- Daily social media posts across 6 platforms
- Interaction logs tracking engagement

**Lifecycle:**
```
Spec → Validated → Options Generated → User Selection → Training → 
Images Generated → User Review → Social Media Posting → Tracking
```

### Logging

Each character has:
- `character-media-log.json` — all generated images with metadata
- `character-interaction-log.json` — social media engagement across all platforms
- `character-asset-log.json` — full lifecycle tracking

---

## QUALITY GATES

### Validation (Automated)
- Personality traits: ≥4 defined
- Voice: Clear description
- Visual: Clear visual hint
- Backstory: Character background
- Universe: Project assignment

### Approval Checkpoints (Manual)
- Checkpoint 1: Visual + voice selection
- Checkpoint 2: First batch image review

### Performance Tracking (Automated)
- Engagement metrics per platform
- Top performers flagged to Whiteboard
- Daily performance summaries

---

## TROUBLESHOOTING

### Issue: "passing-specs.json not found"
**Solution:** Run Character Spec Generator and Mirofish grading first
```bash
python character-spec-generator.py
python mirofish-grading-interface.py
```

### Issue: Checkpoint stuck waiting for input
**Solution:** 
- Interactive mode: provide selection (1-5 for visual/voice)
- Non-interactive: script will timeout after 30 seconds, use default

### Issue: Image generation fails
**Solution:** 
- Ensure trained models exist in `trained-models/[character_name]/`
- Check that training completed successfully
- Verify directory permissions

### Issue: Social media posting not working
**Solution:**
- Verify platform API credentials in `studio-config.json`
- Check that character has approved images
- Review social media agent logs

---

## TRAINING WHEELS MODE (Social Media Agent)

**First 24 posts per character require YOUR approval before posting.**

### How It Works:

1. **Post Generated** — Agent generates 6 captions (Instagram, TikTok, Twitter, Discord, YouTube, Email)

2. **You Review** — See sample captions with platform details

3. **You Approve/Reject:**
   - ✓ **Approve** — Posts queued and ready, counter increments
   - ✗ **Reject** — Posts regenerated with your feedback
   - ? **Review** — See additional variations
   - Q **Quit** — Cancel batch

4. **After 24 Approved:**
   - Training wheels removed
   - Character flagged as "trusted"
   - Auto-posts every day without approval needed
   - Engagement still logged and monitored

### Running Training Wheels:

```bash
python social-media-agent.py
```

Output:
```
========================================================================
SOCIAL MEDIA AGENT — DAILY PUBLISHING
========================================================================

Character: Marcus
Mode: TRAINING_WHEELS_ACTIVE
Posts approved: 5/24

⏸ TRAINING WHEELS ACTIVE — Posts require your approval

========================================================================
⏸ TRAINING WHEELS MODE — Marcus
========================================================================

Post batch: #6/24
Status: AWAITING YOUR APPROVAL

Generated 6 captions across 6 platforms:

[1] INSTAGRAM
    "Thoughts on Marcus? creative and thoughtful vibes. #character"

[2] TIKTOK
    "Marcus POV: daily thoughts"

[3] TWITTER
    "Hot take: creative and thoughtful is underrated"

...

Your action required:
  ✓ approve  — Looks good, queue these posts
  ✗ reject   — Regenerate with different approach
  ? review   — Show me more variations
  q quit     — Cancel batch

========================================================================

Action (approve/reject/review/quit): ✓

✓ Batch approved!
  Posts queued and ready to go live

✓ Post batch #6 approved and logged
  Progress: 6/24 posts approved
```

### Monitoring Progress:

- **Posts Approved:** 6/24 (visual indicator)
- **Status:** TRAINING_WHEELS_ACTIVE
- **Next Milestone:** Auto-post mode unlocked at 24 approvals

---

## AUTO-POST MODE (After 24 Training Posts)

Once character completes 24 approved posts:

**Auto-posts daily without approval:**
- Posts generated at 6:00 AM
- All platforms posted simultaneously
- Engagement tracked automatically
- You still see performance metrics daily

**To monitor:**
- Check engagement-log.json daily
- Top performers flagged to Whiteboard
- Performance summary in CX Agent dashboard

---

### Daily Checklist

- [ ] Check for pending checkpoints (visual/voice selection)
- [ ] Review first batch images before approval
- [ ] Monitor engagement metrics
- [ ] Flag top performers to Whiteboard
- [ ] Process next batch of specs

### Key Metrics

- Characters processed per day: Target 5-10
- Images generated per day: Target 250-500 (50 per character)
- Posts per day: Target 50+ (multi-platform)
- Approval time: ~15-20 min per character

---

## NEXT PHASES

### Phase 2: Mirofish Expert Panel
- Build expert characters for opportunity grading
- Wire to Market Opportunity Scout
- Auto-grade business opportunities by subject matter expert

### Phase 3: Project Assignment
- Characters auto-assigned to projects (Inmates vs Guards, etc.)
- Mass character generation for large series (150+ characters)
- Gaussian Splatting integration for interactive digital doubles

### Phase 4: Revenue Integration
- Character licensing
- Social media monetization tracking
- Engagement-to-revenue analytics

---

## CONTACT

For issues or feature requests, log to:
- `G:\My Drive\Projects\_studio\agency\agency-issues.json`

For architecture questions, reference:
- `cx-agent-asset-types.json` — Asset type definitions
- `CLAUDE.md` — Studio behavioral constitution

---

**AGENCY PIPELINE STATUS: ✅ FULLY OPERATIONAL**

Last updated: April 1, 2026
All components tested and validated.
