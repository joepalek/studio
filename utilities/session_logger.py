"""
session_logger.py -- Append to session-log.md and update status.json.

All file I/O uses unicode_safe helpers to avoid cp1252 encoding crashes on Windows.

Usage:
    import sys
    sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
    from session_logger import log_action, update_status, complete_task

    log_action(
        action='Ghost Book Pass 2 complete',
        result='142 viable candidates, 89 public domain -> validated.json',
        next_step='Run Pass 3 concatenation',
    )

    complete_task(
        task_name='Ghost Book Pass 2',
        result_summary='142 viable candidates saved',
        add_pending=['Ghost Book Pass 3 -- concatenation opportunities'],
        next_recommended='Review top picks, run Pass 3',
    )
"""
import os
import sys
from datetime import datetime

# Ensure utilities/ is on path for unicode_safe import
_UTIL_DIR = os.path.dirname(os.path.abspath(__file__))
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from unicode_safe import safe_json_load, safe_json_dump, safe_str

STUDIO       = 'G:/My Drive/Projects/_studio'
LOG_PATH     = STUDIO + '/session-log.md'
STATUS_PATH  = STUDIO + '/status.json'
ROTATE_BYTES = 50 * 1024  # 50kb


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime('%H:%M')


def _today() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def _iso() -> str:
    return datetime.now().isoformat()[:19]


def _rotate_if_needed():
    """Rename session-log.md to archive file if over 50kb, then start fresh."""
    if not os.path.exists(LOG_PATH):
        return
    if os.path.getsize(LOG_PATH) < ROTATE_BYTES:
        return

    date_str = datetime.now().strftime('%Y-%m-%d')
    archive  = STUDIO + f'/session-log-archive-{date_str}.md'
    counter  = 1
    while os.path.exists(archive):
        archive = STUDIO + f'/session-log-archive-{date_str}-{counter}.md'
        counter += 1

    os.rename(LOG_PATH, archive)

    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('# Studio Session Log\n\n')
        f.write('Append-only. Rotates to session-log-archive-[date].md at 50kb.\n')
        f.write('Updated by Claude Code after every major action.\n\n---\n\n')

    print(f'[session_logger] Log rotated -> {os.path.basename(archive)}')


# ─── Public API ───────────────────────────────────────────────────────────────

def log_action(action: str, result: str, next_step: str = ''):
    """
    Append one timestamped entry to session-log.md.

    Args:
        action:    What was done (imperative, brief)
        result:    What happened — counts, filenames, key outcomes
        next_step: What comes next (optional)
    """
    _rotate_if_needed()

    today     = _today()
    timestamp = _now()

    existing = ''
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding='utf-8') as f:
            existing = f.read()

    # Sanitize all text for safe storage (data stays utf-8, just ensure no null bytes)
    action    = safe_str(action)
    result    = safe_str(result)
    next_step = safe_str(next_step)

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
    Update fields in status.json. All parameters are optional.

    Args:
        current_task:     What is running right now ('' to clear)
        add_completed:    Strings to append to completed_today
        add_pending:      Strings to append to pending
        remove_pending:   Substrings — removes any pending item containing these
        add_blockers:     Strings to append to blockers
        remove_blockers:  Substrings — removes any blocker item containing these
        next_recommended: Overwrite the next_recommended field
    """
    default = {
        'last_updated':    '',
        'current_task':    '',
        'completed_today': [],
        'pending':         [],
        'blockers':        [],
        'next_recommended': '',
    }

    try:
        status = safe_json_load(STATUS_PATH) if os.path.exists(STATUS_PATH) else default
    except Exception:
        status = default

    status['last_updated'] = _iso()

    if current_task is not None:
        status['current_task'] = current_task

    if add_completed:
        for item in add_completed:
            if item not in status.setdefault('completed_today', []):
                status['completed_today'].append(item)

    if add_pending:
        for item in add_pending:
            if item not in status.setdefault('pending', []):
                status['pending'].append(item)

    if remove_pending:
        for term in remove_pending:
            status['pending'] = [
                p for p in status.get('pending', [])
                if term.lower() not in p.lower()
            ]

    if add_blockers:
        for item in add_blockers:
            if item not in status.setdefault('blockers', []):
                status['blockers'].append(item)

    if remove_blockers:
        for term in remove_blockers:
            status['blockers'] = [
                b for b in status.get('blockers', [])
                if term.lower() not in b.lower()
            ]

    if next_recommended is not None:
        status['next_recommended'] = next_recommended

    safe_json_dump(status, STATUS_PATH)


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

    Marks task as complete, removes it from pending, optionally adds new
    pending items and updates next_recommended.

    Args:
        task_name:            Short name for the completed task
        result_summary:       What was produced (used in log + completed list)
        add_pending:          New tasks to add to pending list
        remove_pending_terms: Terms to match+remove from pending (defaults to task_name)
        next_recommended:     Update the next_recommended field
        log_next_step:        next_step text for session-log entry
    """
    completed_str = task_name
    if result_summary:
        completed_str = f'{task_name} -- {result_summary}'

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
