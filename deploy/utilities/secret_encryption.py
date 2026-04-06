"""
Windows DPAPI encryption for agent secrets.
Encrypts secrets at rest - only decryptable on the same machine by the same user.

Option C Panel Architecture v3.0 - Security Hardening
"""

import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

# Windows-specific imports
try:
    import win32crypt
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False
    print("[WARN] win32crypt not available - secrets will be stored in plaintext")
    print("[WARN] Install with: pip install pywin32")


def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt a secret using Windows DPAPI.
    Returns base64-encoded ciphertext with DPAPI: prefix.
    Falls back to plaintext if DPAPI unavailable.
    """
    if not DPAPI_AVAILABLE:
        return f"PLAINTEXT:{plaintext}"
    
    try:
        encrypted = win32crypt.CryptProtectData(
            plaintext.encode('utf-8'),
            "AgentSecret",  # Description
            None,           # Optional entropy
            None,           # Reserved
            None,           # Prompt struct
            0               # Flags
        )
        return f"DPAPI:{base64.b64encode(encrypted).decode('ascii')}"
    except Exception as e:
        print(f"[WARN] DPAPI encryption failed: {e}")
        return f"PLAINTEXT:{plaintext}"


def decrypt_secret(ciphertext: str) -> str:
    """
    Decrypt a DPAPI-encrypted secret.
    Handles both DPAPI and plaintext fallback formats.
    """
    if ciphertext.startswith("PLAINTEXT:"):
        return ciphertext[10:]
    
    if not ciphertext.startswith("DPAPI:"):
        raise ValueError(f"Unknown secret format: {ciphertext[:20]}...")
    
    if not DPAPI_AVAILABLE:
        raise RuntimeError("Cannot decrypt DPAPI secret - win32crypt not available")
    
    try:
        encrypted = base64.b64decode(ciphertext[6:])
        decrypted = win32crypt.CryptUnprotectData(
            encrypted,
            None,  # Optional entropy
            None,  # Reserved
            None,  # Prompt struct
            0      # Flags
        )
        return decrypted[1].decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"DPAPI decryption failed: {e}")


def generate_agent_secret() -> str:
    """Generate a new cryptographically secure agent secret."""
    return secrets.token_hex(32)


def rotate_agent_secret(agent_id: str, registry_path: str) -> dict:
    """
    Rotate an agent's secret. Returns new encrypted secret.
    Logs rotation event.
    """
    new_secret = generate_agent_secret()
    encrypted = encrypt_secret(new_secret)
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    if agent_id not in registry:
        raise ValueError(f"Unknown agent: {agent_id}")
    
    # Update secret
    old_rotated_at = registry[agent_id].get('agent_secret_rotated_at')
    registry[agent_id]['agent_secret'] = encrypted
    registry[agent_id]['agent_secret_rotated_at'] = datetime.now().isoformat()
    registry[agent_id]['agent_secret_rotation_count'] = \
        registry[agent_id].get('agent_secret_rotation_count', 0) + 1
    
    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
    
    return {
        'agent_id': agent_id,
        'rotated_at': registry[agent_id]['agent_secret_rotated_at'],
        'previous_rotation': old_rotated_at,
        'rotation_count': registry[agent_id]['agent_secret_rotation_count']
    }


def should_rotate(agent: dict, max_age_days: int = 90) -> bool:
    """Check if agent secret needs rotation."""
    rotated_at = agent.get('agent_secret_rotated_at')
    if not rotated_at:
        return True  # Never rotated
    
    last_rotation = datetime.fromisoformat(rotated_at)
    age = datetime.now() - last_rotation
    return age > timedelta(days=max_age_days)


def encrypt_all_secrets(registry_path: str) -> dict:
    """
    Encrypt all plaintext secrets in the registry.
    Returns summary of what was encrypted.
    """
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    encrypted_count = 0
    already_encrypted = 0
    
    for agent_id, agent in registry.items():
        if not isinstance(agent, dict):
            continue
            
        secret = agent.get('agent_secret', '')
        
        if secret.startswith('DPAPI:'):
            already_encrypted += 1
        elif secret.startswith('PLAINTEXT:') or secret:
            # Encrypt plaintext secret
            plaintext = secret[10:] if secret.startswith('PLAINTEXT:') else secret
            agent['agent_secret'] = encrypt_secret(plaintext)
            if 'agent_secret_rotated_at' not in agent:
                agent['agent_secret_rotated_at'] = datetime.now().isoformat()
            encrypted_count += 1
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
    
    return {
        'encrypted': encrypted_count,
        'already_encrypted': already_encrypted,
        'dpapi_available': DPAPI_AVAILABLE
    }


def check_secrets_health(registry_path: str, max_age_days: int = 90) -> dict:
    """
    Check health of all agent secrets.
    Returns report of secrets needing attention.
    """
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    report = {
        'total_agents': 0,
        'encrypted_dpapi': 0,
        'plaintext': 0,
        'needs_rotation': [],
        'never_rotated': [],
        'healthy': True
    }
    
    for agent_id, agent in registry.items():
        if not isinstance(agent, dict):
            continue
        
        report['total_agents'] += 1
        secret = agent.get('agent_secret', '')
        
        if secret.startswith('DPAPI:'):
            report['encrypted_dpapi'] += 1
        else:
            report['plaintext'] += 1
            report['healthy'] = False
        
        if should_rotate(agent, max_age_days):
            if agent.get('agent_secret_rotated_at'):
                report['needs_rotation'].append(agent_id)
            else:
                report['never_rotated'].append(agent_id)
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python secret_encryption.py encrypt <registry_path>")
        print("  python secret_encryption.py health <registry_path>")
        print("  python secret_encryption.py rotate <agent_id> <registry_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "encrypt":
        registry_path = sys.argv[2]
        result = encrypt_all_secrets(registry_path)
        print(f"Encrypted {result['encrypted']} secrets")
        print(f"Already encrypted: {result['already_encrypted']}")
        print(f"DPAPI available: {result['dpapi_available']}")
    
    elif command == "health":
        registry_path = sys.argv[2]
        result = check_secrets_health(registry_path)
        print(json.dumps(result, indent=2))
    
    elif command == "rotate":
        agent_id = sys.argv[2]
        registry_path = sys.argv[3]
        result = rotate_agent_secret(agent_id, registry_path)
        print(f"Rotated secret for {agent_id}")
        print(json.dumps(result, indent=2))
