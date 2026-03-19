"""
session_logger.py -- Append to session-log.md and update session-status.json.

Used by Claude Code after every major action. Handles log rotation at 50kb.

Usage:
    import sys
    sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
    from session_logger import log_action, update_status, complete_task

    log_action(
        action='Ghost Book Pass 2 complete',
        result='142 viable candidates, 89 public domain. Saved validated.json.',
        next_step='Run Pass 3 concatenation',
    )

    complete_task(
        task_name='Ghost Book Pass 2',
        add_pending=['Ghost Book Pass 3 — find concatenation opportunities'],
        next_recommended='Review top 10 viable candidates, run Pass 3',
    )
"""
import json, os
from datetime import datetime

STUDIO          = 'G:/My Drive/Projects/_studio'
LOG_PATH        = STUDIO + '/session-log.md'
STATUS_PATH     = STUDIO + '/session-status.json'
ROTATE_BYTES    = 50 * 1024  # 50kb


def _now() -> str:
    return datetime.now().strftime('%H:%M')


def _today() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def _iso() -> str:
    return datetime.now().isoformat()[:19]


def _rotate_if_needed():
    """Rename session-log.md to archive if over 50kb, start fresh."""
    if not os.path.exists(LOG_PATH):
        return
    if os.path.getsize(LOG_PATH) < ROTATE_BYTES:
        return
    date_str = datetime.now().strftime('%Y-%m-%d')
    archive  = STUDIO + f'/session-log-archive-{date_str}.md'
    # If archive already exists for today, add a counter
    counter = 1
    while os.path.exists(archive):
        archive = STUDIO + f'/session-log-archive-{date_str}-{counter}.md'
        counter += 1
    os.rename(LOG_PATH, archive)
    # Start fresh
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('# Studio Session Log\n\n')
        f.write('Append-only. Rotates to session-log-archive-[date].md at 50kb.\n')
        f.write('Updated by Claude Code after every major action.\n\n---\n\n')
    print(f'[session_logger] Log rotated -> {os.path.basename(archive)}')


def log_action(action: str, result: str, next_step: str = '', section: str = None):
    """
    Append one entry to session-log.md.

    Args:
        action:    What was done (imperative, brief)
        result:    What happened (counts, file names, key outcomes)
        next_step: What comes next (optional)
        section:   Override date section header (default: today's date)
    """
    _rotate_if_needed()

    today     = section or _today()
    timestamp = _now()

    # Check if today's section already exists
    existing  = ''
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding='utf-8') as f:
            existing = f.read()

    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        if f'## {today}' not in existing:
            f.write(f'\n## {today}\n\n')
        f.write(f'### {timestamp} | {action}\n')
        f.write(f'- **Action:** {action}\n')
        f.write(f'- **Result:** {result}\n')
        if next_step:
            f.write(f'- **Next:** {next_step}\n')
        f.write('\n')


def update_status(
    current_task: str = None,
    add_completed: list = None,
    add_pending: list = None,
    remove_pending: list = None,
    add_blockers: list = None,
    remove_blockers: list = None,
    next_recommended: str = None,
):
    """
    Update session-status.json fields.

    All parameters are optional — only provided fields are changed.

    Args:
        current_task:     What's running right now
        add_completed:    Strings to append to completed_today list
        add_pending:      Strings to append to pending list
        remove_pending:   Strings to remove from pending (partial match)
        add_blockers:     Strings to append to blockers
        remove_blockers:  Strings to remove from blockers (partial match)
        next_recommended: Override the next_recommended field
    """
    status = {
        'last_updated': '',
        'current_task': '',
        'completed_today': [],
        'pending': [],
        'blockers': [],
        'next_recommended': '',
    }
    if os.path.exists(STATUS_PATH):
        try:
            with open(STATUS_PATH, encoding='utf-8') as f:
                status = json.load(f)
        except Exception:
            pass

    status['last_updated'] = _iso()

    if current_task is not None:
        status['current_task'] = current_task

    if add_completed:
        for item in add_completed:
            if item not in status.get('completed_today', []):
                status.setdefault('completed_today', []).append(item)

    if add_pending:
        for item in add_pending:
            if item not in status.get('pending', []):
                status.setdefault('pending', []).append(item)

    if remove_pending:
        for term in remove_pending:
            status['pending'] = [p for p in status.get('pending', [])
                                  if term.lower() not in p.lower()]

    if add_blockers:
        for item in add_blockers:
            if item not in status.get('blockers', []):
                status.setdefault('blockers', []).append(item)

    if remove_blockers:
        for term in remove_blockers:
            status['blockers'] = [b for b in status.get('blockers', [])
                                   if term.lower() not in b.lower()]

    if next_recommended is not None:
        status['next_recommended'] = next_recommended

    with open(STATUS_PATH, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)


def complete_task(
    task_name: str,
    result_summary: str = '',
    add_pending: list = None,
    remove_pending_terms: list = None,
    next_recommended: str = None,
    log_next_step: str = '',
):
    """
    Convenience: log completion + update status in one call.

    Appends to completed_today, removes matching pending items,
    optionally adds new pending items and updates next_recommended.

    Args:
        task_name:            Short name for the completed task
        result_summary:       What was produced (for log + completed list)
        add_pending:          New tasks to add to pending
        remove_pending_terms: Terms to match+remove from pending list
        next_recommended:     Update the next_recommended field
        log_next_step:        next_step text for session-log.md entry
    """
    completed_str = task_name
    if result_summary:
        completed_str += f' — {result_summary}'

    log_action(
        action=f'{task_name} complete',
        result=result_summary or task_name,
        next_step=log_next_step or (next_recommended or ''),
    )

    update_status(
        current_task='',
        add_completed=[completed_str],
        add_pending=add_pending or [],
        remove_pending=remove_pending_terms or [task_name],
        next_recommended=next_recommended,
    )
