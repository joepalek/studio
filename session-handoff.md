# STUDIO SESSION HANDOFF

This file is maintained by the nightly-rollup agent and the System Tightness Review protocol.
It provides a reliable ground-truth status line for session-to-session continuity.

## Last Known State

System tightness last reviewed: 2026-04-01 — YELLOW (57/100)
Last nightly rollup: not yet run (digest starts 2026-03-26)
Last NIT fire drill: 2026-03-25 — PARTIAL (T05 dismissed, T06 fixed)

## Standing Notes

- claude CLI path: C:\Users\jpalek\AppData\Roaming\npm\claude.cmd
- Task Scheduler: 14 tasks registered under Studio\
- Supervisor inbox panel: dismissed (inbox.json feeds existing flow)
- YouTube Data API key: confirmed working (AIzaSyDGgdr4...)

## Sidebar v2 — COMPLETED 2026-03-30

sidebar-agent.html is fully operational in Opera sidebar panel.
File: G:\My Drive\Projects\_studio\sidebar-agent.html
Tabs: STATUS | INBOX | CHAT | PLAN | ASSETS | DATA | CFG

### Studio Bridge — NEW, needs Task Scheduler registration
- File: G:\My Drive\Projects\_studio\studio_bridge.py
- Port: 11435
- Function: HTTP bridge between sidebar chat and ChromaDB vector store
- Runs session-startup.py query per chat message for targeted context
- Currently running manually — needs elevated registration:
  ACTION REQUIRED: Register \Studio\SidebarBridge in Task Scheduler (needs elevation)
  Script ready at: G:\My Drive\register_bridge.ps1

### Key fixes applied this session
- INJECTED data block moved to line 239 (before window.onload at 572) — was causing all data to be undefined
- OLLAMA_ORIGINS=* set in user registry — Ollama now accepts browser fetch requests
- inject_sidebar_data.py updated with ensure_ascii=True and correct insertion position
- Vector store force-reindexed (595 chunks) after studio-context.md regenerated at 117KB
- Studio bridge context budget increased to 2500 chars for project-specific queries

### Daily inject pipeline
inject_sidebar_data.py runs at 6 AM via \Studio\SidebarInject
Also calls update_asset_usage.py for real usage counts before injecting
