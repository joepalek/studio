"""
Tamper-proof logging using hash chains.
Each entry includes hash of previous entry, making tampering detectable.

Option C Panel Architecture v3.0 - Security Hardening
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any


def compute_entry_hash(entry: dict, prev_hash: str) -> str:
    """Compute SHA-256 hash of entry + previous hash."""
    # Remove hash field if present for computation
    entry_copy = {k: v for k, v in entry.items() if k != 'hash'}
    canonical = json.dumps(entry_copy, sort_keys=True, separators=(',', ':'))
    combined = f"{prev_hash}:{canonical}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


def append_to_chain(log_path: str, entry: dict) -> dict:
    """
    Append entry to hash-chained log.
    Returns entry with hash and prev_hash fields added.
    """
    # Get previous hash
    prev_hash = "GENESIS"
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                try:
                    last_entry = json.loads(lines[-1].strip())
                    prev_hash = last_entry.get('hash', 'GENESIS')
                except json.JSONDecodeError:
                    pass  # Corrupted last line, start new chain
    
    # Add metadata
    entry['timestamp'] = datetime.now().isoformat()
    entry['prev_hash'] = prev_hash
    entry['hash'] = compute_entry_hash(entry, prev_hash)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Append
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    
    return entry


def verify_chain(log_path: str) -> dict:
    """
    Verify integrity of hash chain.
    Returns {valid: bool, entries_checked: int, first_invalid: Optional[int], reason: str}
    """
    if not os.path.exists(log_path):
        return {'valid': True, 'entries_checked': 0, 'first_invalid': None}
    
    prev_hash = "GENESIS"
    entries_checked = 0
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
                
            try:
                entry = json.loads(line)
                
                # Verify prev_hash chain
                if entry.get('prev_hash') != prev_hash:
                    return {
                        'valid': False,
                        'entries_checked': entries_checked,
                        'first_invalid': i,
                        'reason': f'prev_hash mismatch at line {i}: expected {prev_hash[:16]}..., got {entry.get("prev_hash", "MISSING")[:16]}...'
                    }
                
                # Verify hash
                stored_hash = entry.get('hash')
                if not stored_hash:
                    return {
                        'valid': False,
                        'entries_checked': entries_checked,
                        'first_invalid': i,
                        'reason': f'missing hash at line {i}'
                    }
                
                computed_hash = compute_entry_hash(entry, prev_hash)
                
                if stored_hash != computed_hash:
                    return {
                        'valid': False,
                        'entries_checked': entries_checked,
                        'first_invalid': i,
                        'reason': f'hash mismatch at line {i} - entry tampered'
                    }
                
                prev_hash = stored_hash
                entries_checked += 1
                
            except json.JSONDecodeError as e:
                return {
                    'valid': False,
                    'entries_checked': entries_checked,
                    'first_invalid': i,
                    'reason': f'malformed JSON at line {i}: {e}'
                }
    
    return {
        'valid': True,
        'entries_checked': entries_checked,
        'first_invalid': None,
        'reason': 'chain intact'
    }


def get_chain_stats(log_path: str) -> dict:
    """Get statistics about a hash chain."""
    if not os.path.exists(log_path):
        return {
            'exists': False,
            'entries': 0,
            'first_entry': None,
            'last_entry': None,
            'file_size_bytes': 0
        }
    
    entries = 0
    first_entry = None
    last_entry = None
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries += 1
                if first_entry is None:
                    first_entry = entry.get('timestamp')
                last_entry = entry.get('timestamp')
            except:
                pass
    
    return {
        'exists': True,
        'entries': entries,
        'first_entry': first_entry,
        'last_entry': last_entry,
        'file_size_bytes': os.path.getsize(log_path)
    }


def read_chain(log_path: str, limit: int = 100, reverse: bool = True) -> list:
    """
    Read entries from hash chain.
    
    Args:
        log_path: Path to chain file
        limit: Maximum entries to return
        reverse: If True, return most recent first
    
    Returns:
        List of entries
    """
    if not os.path.exists(log_path):
        return []
    
    entries = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except:
                pass
    
    if reverse:
        entries = entries[::-1]
    
    return entries[:limit]


class ChainedLogger:
    """
    Convenience class for hash-chained logging.
    
    Usage:
        logger = ChainedLogger("G:/My Drive/Projects/_studio/logs/challenge_log.jsonl")
        logger.log({"event": "challenge", "agent_id": "game_archaeology", "reason": "..."})
        result = logger.verify()
    """
    
    def __init__(self, log_path: str):
        self.log_path = log_path
    
    def log(self, entry: dict) -> dict:
        """Append entry to chain, returns entry with hash."""
        return append_to_chain(self.log_path, entry)
    
    def verify(self) -> dict:
        """Verify chain integrity."""
        return verify_chain(self.log_path)
    
    def stats(self) -> dict:
        """Get chain statistics."""
        return get_chain_stats(self.log_path)
    
    def read(self, limit: int = 100, reverse: bool = True) -> list:
        """Read entries from chain."""
        return read_chain(self.log_path, limit, reverse)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python tamper_proof_log.py verify <log_path>")
        print("  python tamper_proof_log.py stats <log_path>")
        print("  python tamper_proof_log.py read <log_path> [limit]")
        print("  python tamper_proof_log.py test <log_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    log_path = sys.argv[2]
    
    if command == "verify":
        result = verify_chain(log_path)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['valid'] else 1)
    
    elif command == "stats":
        result = get_chain_stats(log_path)
        print(json.dumps(result, indent=2))
    
    elif command == "read":
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        entries = read_chain(log_path, limit)
        for entry in entries:
            print(json.dumps(entry))
    
    elif command == "test":
        # Test the chain with sample entries
        print(f"Testing chain at {log_path}")
        
        logger = ChainedLogger(log_path)
        
        # Add test entries
        for i in range(3):
            entry = logger.log({
                "event": "test",
                "sequence": i,
                "message": f"Test entry {i}"
            })
            print(f"Added entry {i}: {entry['hash'][:16]}...")
        
        # Verify
        result = logger.verify()
        print(f"\nVerification: {json.dumps(result, indent=2)}")
        
        # Stats
        stats = logger.stats()
        print(f"\nStats: {json.dumps(stats, indent=2)}")
