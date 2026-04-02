# TASK SCHEDULER SETUP — MANUAL GUIDE

If the PowerShell script doesn't work, follow these manual steps.

---

## SETUP OVERVIEW

3 daily tasks to add to Windows Task Scheduler:

| Task | Time | Script | Purpose |
|------|------|--------|---------|
| **Agency-CX-Agent-2AM** | 2:00 AM | cx-agent-main.py | Process specs → create characters |
| **Agency-ImageGen-4AM** | 4:00 AM | image-generation-agent.py | Generate 50 images per character |
| **Agency-SocialMedia-6AM-TrainingWheels** | 6:00 AM | social-media-agent.py | Posts (awaits your approval) |

---

## STEP 1: OPEN TASK SCHEDULER

1. Press `Windows Key + R`
2. Type: `taskschd.msc`
3. Press Enter

Or: Control Panel → Administrative Tools → Task Scheduler

---

## STEP 2: CREATE TASK 1 — CX AGENT (2:00 AM)

### Action: Create Basic Task

1. **Right-click** Task Scheduler Library → **New Folder**
   - Name: `Agency`

2. **Right-click** Agency folder → **Create Basic Task**

3. **General Tab:**
   - Name: `Agency-CX-Agent-2AM`
   - Description: `Process character specs and create characters`
   - ✓ Check: "Run with highest privileges"

4. **Triggers Tab:**
   - Click **New**
   - Begin the task: `On a schedule`
   - Daily
   - Start: `2:00 AM`
   - Repeat every: `1 day`
   - Click **OK**

5. **Actions Tab:**
   - Click **New**
   - Program/script: `python`
   - Add arguments: `"G:\My Drive\Projects\_studio\agency\cx-agent-main.py"`
   - Start in: `G:\My Drive\Projects\_studio\agency`
   - Click **OK**

6. **Conditions Tab:**
   - ✓ "Wake the computer to run this task"
   - Uncheck "Stop if the computer switches to battery power"

7. **Settings Tab:**
   - ✓ "Run task as soon as possible after a scheduled start is missed"
   - ✓ "Allow task to be run on demand"
   - Set timeout: `12 hours` (in case it runs long)

8. Click **OK** → You may need to enter your Windows password

---

## STEP 3: CREATE TASK 2 — IMAGE GENERATION (4:00 AM)

Repeat same process as Task 1, but:

- **Name:** `Agency-ImageGen-4AM`
- **Description:** `Generate 50 images per trained character`
- **Trigger:** 4:00 AM daily
- **Program:** `python`
- **Arguments:** `"G:\My Drive\Projects\_studio\agency\image-generation-agent.py"`
- **Start in:** `G:\My Drive\Projects\_studio\agency`

---

## STEP 4: CREATE TASK 3 — SOCIAL MEDIA WITH TRAINING WHEELS (6:00 AM)

Repeat same process as Task 1, but:

- **Name:** `Agency-SocialMedia-6AM-TrainingWheels`
- **Description:** `Post to social media (training wheels - awaits approval)`
- **Trigger:** 6:00 AM daily
- **Program:** `python`
- **Arguments:** `"G:\My Drive\Projects\_studio\agency\social-media-agent.py"`
- **Start in:** `G:\My Drive\Projects\_studio\agency`
- **Settings Tab:**
  - Set timeout: `2 hours` (allows time for you to approve posts)
  - ✓ "Stop the task if it runs longer than: 2 hours"

⚠️ **IMPORTANT:** This task will wait for your input each morning at 6:00 AM

---

## TESTING

Before adding to scheduler, test each script manually:

```powershell
cd "G:\My Drive\Projects\_studio\agency"

# Test 1: Demo mode (non-interactive)
python agency-pipeline-demo.py

# Test 2: Full workflow (interactive - press Ctrl+C to exit)
python cx-agent-main.py
```

---

## MONITORING TASKS

To view your created tasks:

1. Open Task Scheduler
2. Go to: Task Scheduler Library → Agency
3. You should see 3 tasks listed:
   - Agency-CX-Agent-2AM
   - Agency-ImageGen-4AM
   - Agency-SocialMedia-6AM-TrainingWheels

To run a task manually:
- **Right-click** task → **Run**

To view task history:
- **Double-click** task → **History** tab

---

## TROUBLESHOOTING

### Task doesn't run at scheduled time

**Solutions:**
1. Make sure computer is on at 2 AM, 4 AM, 6 AM
2. Or enable: Task Scheduler → Right-click task → Properties → Conditions → ✓ "Wake the computer to run this task"
3. Check task's Status column shows "Ready"
4. Check Event Viewer → Windows Logs → System for errors

### Script runs but doesn't show output

**Expected behavior:**
- Scripts run in background
- No window opens (unless they have errors)
- Check logs in agency folder for output

### Training Wheels task doesn't wait for input

**If 6 AM task runs but you don't see approval prompt:**
1. You may need to run it **manually** in PowerShell to approve/reject posts
2. Or schedule it to run with **highest privileges** so it can display UI

**Manual testing:**
```powershell
cd "G:\My Drive\Projects\_studio\agency"
python social-media-agent.py
# This will show the approval prompt
```

---

## NEXT STEPS

Once tasks are created and working:

1. **Monitor first day:** Make sure 2 AM, 4 AM, 6 AM tasks run
2. **Approve posts:** At 6:00 AM, respond to approval prompts
3. **Check logs:** Review `character-asset-log.json` for status
4. **Scale up:** Once 24 posts approved per character, social media switches to auto-post mode
5. **Monitor performance:** Track engagement metrics daily

---

## QUICK REFERENCE

**File locations:**
```
Scripts: G:\My Drive\Projects\_studio\agency\
Config: G:\My Drive\Projects\_studio\agency\cx-agent-asset-types.json
Logs: G:\My Drive\Projects\_studio\agency\characters\[character-name]\logs\
```

**Daily schedule:**
```
2:00 AM → CX Agent processes character specs
4:00 AM → Image Generation creates images
6:00 AM → Social Media Agent awaits your approval
```

**Test commands:**
```powershell
cd "G:\My Drive\Projects\_studio\agency"
python agency-pipeline-demo.py              # Non-interactive demo
python cx-agent-main.py                     # Full workflow
python image-generation-agent.py            # Image generation
python social-media-agent.py                # Training wheels mode
```
