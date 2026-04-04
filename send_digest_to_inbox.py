
# EXPECTED_RUNTIME_SECONDS: 60
#!/usr/bin/env python3
"""
AI News Digest → Studio Inbox
Takes the generated digest and logs it as an inbox entry
"""

import json
from datetime import datetime
import os

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

def add_to_inbox(digest_text, source="AI_News_Scraper"):
    """Add digest entry to your studio inbox"""
    
    inbox_file = "inbox.json"
    
    # Load existing inbox or create new one
    if os.path.exists(inbox_file):
        with open(inbox_file, 'r', encoding='utf-8') as f:
            inbox = json.load(f)
    else:
        inbox = {"entries": []}
    
    # Create inbox entry
    entry = {
        "id": f"news-{datetime.now().isoformat()}",
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "type": "intelligence_digest",
        "priority": "info",
        "title": f"AI News Digest - {datetime.now().strftime('%Y-%m-%d')}",
        "content": digest_text,
        "status": "pending_review",
        "requires_approval": False,
        "assigned_to": "Joe"
    }
    
    inbox["entries"].append(entry)
    
    # Save back to file
    with open(inbox_file, 'w', encoding='utf-8') as f:
        json.dump(inbox, f, indent=2, ensure_ascii=False)
    
    print(f"[Inbox] Added entry: {entry['title']}")
    return entry['id']

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        digest_file = sys.argv[1]
    else:
        digest_file = "ai_news_digest.md"
    
    if os.path.exists(digest_file):
        with open(digest_file, 'r', encoding='utf-8') as f:
            digest = f.read()
        
        entry_id = add_to_inbox(digest)
        print(f"[Done] Inbox entry created: {entry_id}")
    else:
        print(f"[Error] Digest file not found: {digest_file}")
