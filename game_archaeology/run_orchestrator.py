"""
Task Scheduler Entry Point: Game Archaeology Daily Cycle
Called at 2:00 AM UTC daily via Windows Task Scheduler

Usage:
  python G:\My Drive\Projects\_studio\game_archaeology\run_orchestrator.py
"""

import sys
import os
from datetime import datetime

# Add studio to path
sys.path.insert(0, 'G:/My Drive/Projects/_studio')
sys.path.insert(0, 'G:/My Drive/Projects/_studio/game_archaeology')

from supabase_config import get_supabase_client
from game_archaeology_orchestrator_updated import GameArchaeologyOrchestrator


def main():
    print(f"\n{'='*70}")
    print(f"Game Archaeology Daily Cycle")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")
    
    # Get Supabase client from studio-config.json
    supabase = get_supabase_client()
    if not supabase:
        print("ERROR: Supabase not configured in studio-config.json")
        return 1
    
    # Run orchestrator
    try:
        orchestrator = GameArchaeologyOrchestrator(supabase)
        result = orchestrator.run_daily_cycle()
        
        # Summary
        print(f"\n{'='*70}")
        print(f"EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"Status: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"  Games found: {result['games_found']}")
        print(f"  Games inserted: {result['games_inserted']}")
        print(f"  Games assessed: {result['games_assessed']}")
        print(f"  Duration: {result['duration_seconds']:.1f}s")
        
        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors'][:5]:
                print(f"  - {error[:100]}")
        
        print(f"{'='*70}\n")
        
        return 0 if result['success'] else 1
        
    except Exception as e:
        print(f"ERROR: Orchestrator failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
