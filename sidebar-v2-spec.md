# Sidebar Agent V2 — Updated Feature Spec
Updated: 2026-03-26 morning session

---

## TAB: STATUS

### 1. Time / Date Display + Timestamps
- Show current date AND time at top, Central Time zone
- Greet based on time of day: "Good morning", "Good afternoon", "Good evening"
- All log entries show timestamps in Central Time
- Chat messages show time sent
- Helps AI understand time elapsed between messages

### 2. Project Launch Buttons
- One button per ACTIVE project that has a deliverable to open
- Deliverable = something that can be sent to Opera (URL) or run on desktop (app/script)
- If a project has no launchable deliverable yet, NO button — wait until one exists
- Projects without deliverables are tracked in completion list (#5) but not here
- Source: state.json per project — check for "deliverable_url" or "launch_path" fields
- Add those fields to state.json spec if missing

### 3. Agent/Task Run Buttons — WITH DYNAMIC LOOKUP
- Buttons for all agents and tasks that have run scripts
- ADD: "Add New" button that opens a lookup panel showing:
  * All agents in run-agent.py AGENT_MAP
  * All .bat files in scheduler/ folder
  * Any NOT already showing as buttons get listed as "Add to sidebar"
  * User clicks to add — button appears in sidebar permanently
- This way sidebar auto-updates when new agents are created
- Writes selected task to task-queue.json for Claude Code to pick up

### 4. Resource/Asset Tracking Panel — REDESIGN
- Track ALL resources/APIs/tools actively used by the system
- Source: new asset-log.json file (to be created)
- Only track assets used in the last 30 days — drop anything older
- For each tracked asset show:
  * Service name
  * Last used date
  * Usage this month (calls, tokens, generations, etc.)
  * Limits if known (free tier cap, monthly limit)
  * Status: GREEN (plenty left) / YELLOW (75%+ used) / RED (near limit)
- Asset types to track: APIs (Anthropic, Gemini, OpenRouter, YouTube, eBay, Supabase),
  image gen tools, video gen tools, any new resource Joe adds
- Updates automatically when new resources are used
- Joe mentions a new project coming that will add significant resources —
  add new assets to asset-log.json as they appear
- Panel refreshes on STATUS tab load

### 5. Project Completion Tracker
- List all projects with completion % at bottom of STATUS tab
- Sourced from state.json files
- Visual indicator: progress bar or percentage
- Sorted by: most recently active first

---

## TAB: CHAT

### 1. Formatting — DONE ✓

### 2. Deliverable Tray
- Tray above input shows downloadable files/code blocks from AI responses
- Click to download without hunting through history

### 3. Attach Button — EXPANDED
- Attach ANY file type: JSON, MD, TXT, HTML, PY, JS, PNG, JPG, MP4, MP3, PDF
- Images: display thumbnail in chat, send as base64 to AI vision models
- Video/audio: send filename + metadata as context (full files too large for most APIs)
- Allows returning outputs back to AI for review or iteration

### 4. Unified Context / Awareness System — CRITICAL
Goal: sidebar, Claude.ai (Opera), and Claude Code all feel like ONE entity
that knows the system, its vitals, history, projects, and goals.

Current problem: each session starts fresh, no shared memory.

Proposed solution — "Mirofish Test" approach:
- Send multiple AI agent configurations out to test this problem
- Each agent tries a different approach to shared context
- They stress-test each configuration, try to break it
- Rate and report back with findings
- Round 2: take best configurations, test again with combined feedback
- Final: implement winning configuration as the standard

Configurations to test:
A) studio-context.md injection at session start (current approach)
B) Structured CLAUDE.md with decision log + handoff file
C) Supabase as shared state DB all three interfaces read from
D) Git-based context (all three read from _studio repo)
E) Hybrid: CLAUDE.md rules + session-handoff.md + Supabase for live data

Each config rated on:
- Does it survive a session gap? (close Opera, reopen next day)
- Does Claude Code know what Opera discussed yesterday?
- Does the sidebar reflect current system state?
- How many tokens does maintaining context cost?
- How stale does it get?

Document findings in context-test-results.md
Implement winning config as standing system architecture.

---

## TAB: QUEUE (REDESIGN — unchanged from original spec)

Remove task creation form entirely.

### Section 1 — Pending Build Items
- Read from supervisor-inbox.json + state.json decision queues
- Shows: item name, project, priority, status
- Read-only table
- Auto-refresh on tab open

### Section 2 — Whiteboard
- Read from whiteboard.json
- Sorted by score (highest first)
- Shows: score, title, type, status
- Read-only
- Auto-refresh on tab open

### Bottom — Queue Task Input
- Single line input: "Add task for Claude Code"
- Writes to task-queue.json on submit
- Small, unobtrusive — not the main focus of the tab

---

## TAB: FILES
- Already built ✓
- NOTE: May overlap with Chat attach button
- Resolution: FILES tab is for browsing/managing Drive files
  Chat attach is for quickly adding context to a specific message
  Keep both — different use cases

---

## TAB: CONFIG — REDESIGN

### API Key Management
- Do NOT allow pasting keys directly into sidebar
- Instead: reference studio-config.json for all keys
- Sidebar reads keys FROM the JSON file, never stores them itself
- Show key status (SET / MISSING) not the key values

### Smart Model Router
- New project Joe is working on will help with this
- Goal: sidebar automatically selects best AI model for each task type
- Config tab shows current routing rules
- Example: "Complex reasoning → Claude Sonnet", "Quick lookups → Gemini Flash",
  "Image analysis → Claude vision", "Bulk processing → Gemini free tier"
- Routing rules stored in model-router.json (to be created)
- User can view and edit routing rules from CONFIG tab

---

## TAB: AGENT INBOX — NEW TAB (was missing from original spec)

This was discussed but not implemented. Critical missing piece.

### What it does:
- Consolidates ALL inbox messages across the system into one view
- Sources:
  * supervisor-inbox.json
  * mobile-inbox.json  
  * Any other *-inbox.json files in _studio
- Shows each item as a card: source, timestamp, message, urgency
- Actions per item: Mark Resolved / Escalate / Snooze
- Resolved items are removed from source JSON
- Count badge on tab showing unresolved items

### Why this matters:
- The studio.html was tracking 32+ pending decisions
- Mobile inbox was getting out of sync
- Multiple inbox files existed with no unified view
- An agent was made to handle this but the count was consistently off
- This tab IS the unified inbox — replaces the need to check multiple files

### Relationship to studio.html and mobile:
- studio.html (VS Code visual reference) — keep as-is, read-only dashboard
- mobile-studio.html — full screen mobile version of THIS sidebar
- Opera sidebar — this file (sidebar-agent.html)
- All three read from the SAME inbox sources
- Only one place to resolve items: sidebar AGENT INBOX tab
- Mobile and studio.html show the count but route to sidebar for resolution

---

## DEPLOYMENT TARGETS

### Opera Sidebar (primary)
- sidebar-agent.html
- Runs via serve-sidebar.bat on localhost:8765
- Full feature set

### Mobile (secondary)
- mobile-studio.html on GitHub Pages
- Same tabs, touch-optimized
- Links open in Safari/Chrome
- Build AFTER sidebar is correct — mobile is just a responsive copy

### VS Code / studio.html (reference only)
- Read-only dashboard
- Shows system health, project status, inbox count
- Does NOT resolve items — points to sidebar for that
- Keep current, don't rebuild

---

## PRIORITY BUILD ORDER

1. AGENT INBOX tab — most critical missing piece
2. QUEUE tab redesign — remove form, add whiteboard + pending items
3. STATUS tab additions:
   a. Central time display with greeting
   b. Dynamic agent/task buttons with "Add New" lookup
   c. Asset tracking panel (needs asset-log.json created first)
   d. Project launch buttons (only projects with deliverables)
4. CHAT tab additions:
   a. Expanded attach (images, video, any file type)
   b. Deliverable tray
5. CONFIG tab redesign:
   a. Reference studio-config.json instead of storing keys
   b. Model router display
6. Context/awareness Mirofish test — run after sidebar is stable
7. Mobile version — build last, after sidebar is verified correct
