"""
Game Archaeology: Supabase Integration Module
Reads credentials from studio-config.json
"""

import json
import os
import sys
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Run: pip install supabase")


def load_studio_config(config_path: str = "G:/My Drive/Projects/_studio/studio-config.json") -> dict:
    """Load Supabase credentials from studio-config.json"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"ERROR: studio-config.json not found at {config_path}")
        return {}
    except json.JSONDecodeError:
        print(f"ERROR: studio-config.json is not valid JSON")
        return {}


def get_supabase_client(use_service_role: bool = False):
    """
    Get authenticated Supabase client from studio-config.json credentials.
    
    Args:
        use_service_role: If True, uses service role key (higher privileges).
                         If False, uses anon key (RLS enforced).
    
    Returns:
        Supabase client or None if not configured.
    """
    if not SUPABASE_AVAILABLE:
        print("ERROR: supabase-py not installed. Run: pip install supabase")
        return None
    
    # Load credentials from studio-config.json
    config = load_studio_config()
    
    if not config:
        print("ERROR: Could not load studio-config.json")
        return None
    
    # Get Supabase credentials from config
    supabase_url = config.get("supabase_url")
    supabase_key = config.get("supabase_anon_key") if not use_service_role else config.get("supabase_service_role_key")
    
    if not supabase_url:
        print("ERROR: 'supabase_url' not found in studio-config.json")
        return None
    
    if not supabase_key:
        key_name = "supabase_service_role_key" if use_service_role else "supabase_anon_key"
        print(f"ERROR: '{key_name}' not found in studio-config.json")
        return None
    
    try:
        client = create_client(supabase_url, supabase_key)
        print(f"✓ Supabase client initialized")
        print(f"  URL: {supabase_url}")
        return client
    except Exception as e:
        print(f"ERROR: Failed to create Supabase client: {e}")
        return None


# ============================================================
# USAGE IN ORCHESTRATOR
# ============================================================

"""
In game_archaeology_orchestrator_updated.py:

from supabase_config import get_supabase_client

supabase = get_supabase_client()
if not supabase:
    raise RuntimeError("Supabase not configured in studio-config.json")

orchestrator = GameArchaeologyOrchestrator(supabase)
result = orchestrator.run_daily_cycle()
"""


if __name__ == "__main__":
    # Test connection
    print("Testing Supabase connection...\n")
    client = get_supabase_client()
    
    if client:
        try:
            # Simple test query
            result = client.table("game_candidates").select("id").limit(1).execute()
            print(f"✓ Connection successful")
            print(f"  Query returned: {len(result.data) if result.data else 0} rows")
            
            # Check if tables exist
            tables = ["game_candidates", "game_assessments", "cx_queue", "cx_completions"]
            print(f"\nChecking tables:")
            for table_name in tables:
                try:
                    client.table(table_name).select("COUNT(*)").limit(1).execute()
                    print(f"  ✓ {table_name}")
                except Exception as e:
                    print(f"  ✗ {table_name}: {str(e)[:50]}")
            
        except Exception as e:
            print(f"✗ Query test failed: {e}")
    else:
        print("✗ Client not initialized")
