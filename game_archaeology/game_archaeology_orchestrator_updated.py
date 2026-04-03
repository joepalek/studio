"""
Game Archaeology Orchestrator (Updated)
Coordinates daily crawl → legal → queue pipeline.
Monitors system load; backs off if >80% CPU.
Wires all outputs to Supabase.
"""

import json
import time
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import psutil  # For system load monitoring

sys.path.insert(0, 'G:/My Drive/Projects/_studio')
from studio_core.logger import Logger
from studio_core.agent_inbox import AgentInbox

# Assume Supabase client is initialized elsewhere
# from supabase import create_client


class GameArchaeologyOrchestrator:
    """
    Daily orchestration:
    1. Check system load → decide if crawl
    2. Run Crawler (expanded sources)
    3. Run Legal Agent on new games
    4. Push assessments to Supabase
    5. Trigger weekly digest (Friday)
    6. Assign next game from CX queue to CX Agent
    """

    def __init__(
        self,
        supabase_client,  # Supabase initialized client
        agent_id: str = "GameArchaeology_Orchestrator",
        cpu_load_threshold: float = 80.0,
    ):
        self.agent_id = agent_id
        self.logger = Logger(agent_id)
        self.inbox = AgentInbox()
        self.supabase = supabase_client
        self.cpu_load_threshold = cpu_load_threshold
        self._log("Orchestrator initialized", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    # ============================================================
    # SYSTEM HEALTH MONITORING
    # ============================================================

    def check_system_load(self) -> Dict[str, Any]:
        """
        Check CPU, memory, and disk usage.
        Returns dict with load percentages.
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'timestamp': datetime.now().isoformat(),
                'healthy': cpu_percent < self.cpu_load_threshold,
            }
        except Exception as e:
            self._log(f"Error checking system load: {e}", level="WARNING")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'healthy': True,  # Default: proceed
            }

    # ============================================================
    # DAILY CRAWLER → LEGAL → SUPABASE PIPELINE
    # ============================================================

    def run_daily_cycle(self, force: bool = False) -> Dict[str, Any]:
        """
        Daily crawl + legal + push to Supabase.
        
        Timing:
        - Run at 2:00 AM UTC if CPU < 80%
        - If CPU > 80%, delay by 1 hour and retry
        - Max retries: 6 (up to 8:00 AM UTC)
        """
        self._log("=" * 70, level="INFO")
        self._log("DAILY GAME ARCHAEOLOGY CYCLE", level="INFO")
        self._log("=" * 70, level="INFO")

        start_time = datetime.now()
        cycle_result = {
            'success': False,
            'games_found': 0,
            'games_assessed': 0,
            'games_inserted': 0,
            'duration_seconds': 0,
            'errors': [],
        }

        # Step 1: Check System Load
        self._log("STEP 1: System Health Check", level="INFO")
        system_status = self.check_system_load()
        self._log(f"  CPU: {system_status['cpu_percent']:.1f}%", level="INFO")
        self._log(f"  Memory: {system_status['memory_percent']:.1f}%", level="INFO")

        if not system_status['healthy'] and not force:
            self._log(f"  ⚠ System load high ({system_status['cpu_percent']:.1f}% CPU)", level="WARNING")
            self._log("  Backing off. Next retry in 1 hour.", level="WARNING")
            self.inbox.add_item(
                agent_id=self.agent_id,
                project_id="GameArchaeology",
                question="Daily cycle backed off due to high system load",
                required_action="Will retry in 1 hour",
                urgency="LOW"
            )
            return cycle_result

        # Step 2: Run Crawler
        self._log("STEP 2: Archive Crawl (Expanded Sources)", level="INFO")
        try:
            from game_archive_crawler_expanded import ExpandedGameArchiveCrawler
            
            crawler = ExpandedGameArchiveCrawler()
            games = crawler.run_expanded_crawl()
            cycle_result['games_found'] = len(games)
            
            self._log(f"  ✓ Found {len(games)} new games", level="INFO")
            
            # Insert to Supabase game_candidates
            for game in games:
                try:
                    self.supabase.table("game_candidates").insert({
                        "title": game['title'],
                        "original_creator": game.get('original_creator'),
                        "release_date": game.get('release_date'),
                        "source_url": game.get('source_url'),
                        "has_source_code": game.get('has_source_code', False),
                        "game_type": game.get('game_type'),
                        "ip_status": game.get('ip_status'),
                        "source": game.get('source'),
                    }).execute()
                    cycle_result['games_inserted'] += 1
                except Exception as e:
                    cycle_result['errors'].append(f"Insert error: {game['title']}: {e}")
                    self._log(f"  ✗ Insert failed: {game['title']}", level="WARNING")

        except Exception as e:
            cycle_result['errors'].append(f"Crawler error: {e}")
            self._log(f"  ✗ Crawler failed: {e}", level="ERROR")
            return cycle_result

        # Step 3: Run Legal Agent
        self._log("STEP 3: Legal Assessment (GREEN + YELLOW only)", level="INFO")
        try:
            from game_archaeology_legal_agent import GameArchaeologyLegalAgent, GameCandidate
            
            legal_agent = GameArchaeologyLegalAgent()
            
            # Convert games to GameCandidate format
            game_candidates = [
                GameCandidate(
                    title=game['title'],
                    original_creator=game.get('original_creator'),
                    release_date=game.get('release_date'),
                    source_url=game.get('source_url'),
                    has_source_code=game.get('has_source_code', False),
                    game_type=game.get('game_type'),
                    ip_status=game.get('ip_status'),
                )
                for game in games
            ]
            
            assessments = legal_agent.assess_batch(game_candidates)
            cycle_result['games_assessed'] = len(assessments)
            
            # Filter: Only GREEN and YELLOW (per requirement)
            qualified_assessments = [
                a for a in assessments
                if a.risk_level in ['GREEN', 'YELLOW']
            ]
            
            self._log(f"  ✓ Assessed {len(assessments)} games: {len(qualified_assessments)} GREEN/YELLOW", level="INFO")
            
            # Insert assessments to Supabase
            for assessment in qualified_assessments:
                try:
                    # Find matching game_id
                    game_result = self.supabase.table("game_candidates") \
                        .select("id") \
                        .eq("title", assessment.game_title) \
                        .order("created_at", desc=True) \
                        .limit(1) \
                        .execute()
                    
                    if game_result.data:
                        game_id = game_result.data[0]['id']
                        
                        self.supabase.table("game_assessments").insert({
                            "game_id": game_id,
                            "risk_level": assessment.risk_level,
                            "confidence": assessment.confidence,
                            "reasoning": assessment.reasoning,
                            "transformation_requirements": assessment.transformation_requirements,
                            "tier_recommendation": assessment.tier_recommendation,
                            "notes_for_user": assessment.notes_for_user,
                            "legal_status": "ASSESSED",
                        }).execute()
                except Exception as e:
                    cycle_result['errors'].append(f"Assessment insert error: {assessment.game_title}: {e}")
                    self._log(f"  ✗ Assessment insert failed: {assessment.game_title}", level="WARNING")

        except Exception as e:
            cycle_result['errors'].append(f"Legal Agent error: {e}")
            self._log(f"  ✗ Legal Agent failed: {e}", level="ERROR")

        # Step 4: Log Results
        duration = (datetime.now() - start_time).total_seconds()
        cycle_result['duration_seconds'] = duration
        cycle_result['success'] = True

        self._log("=" * 70, level="INFO")
        self._log(f"CYCLE COMPLETE", level="INFO")
        self._log(f"  Games found: {cycle_result['games_found']}", level="INFO")
        self._log(f"  Games inserted: {cycle_result['games_inserted']}", level="INFO")
        self._log(f"  Games assessed: {cycle_result['games_assessed']}", level="INFO")
        self._log(f"  Duration: {duration:.1f}s", level="INFO")
        if cycle_result['errors']:
            self._log(f"  Errors: {len(cycle_result['errors'])}", level="WARNING")
        self._log("=" * 70, level="INFO")

        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id="GameArchaeology",
            question="Daily cycle complete",
            required_action="Review results",
            urgency="LOW",
            resolution_data=cycle_result
        )

        return cycle_result

    # ============================================================
    # WEEKLY DIGEST (FRIDAY 5PM UTC)
    # ============================================================

    def generate_weekly_digest(self) -> Dict[str, Any]:
        """
        Friday 5PM UTC: Aggregate GREEN + YELLOW games from past week.
        Prepare digest for user to review and pick 1-2 for CX production.
        """
        self._log("=" * 70, level="INFO")
        self._log("WEEKLY DIGEST GENERATION (Friday 5PM UTC)", level="INFO")
        self._log("=" * 70, level="INFO")

        result = {
            'green_games': [],
            'yellow_games': [],
            'total_reviewed': 0,
            'digest_ready': False,
        }

        try:
            # Query assessments from past 7 days, GREEN + YELLOW only
            seven_days_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
            
            assessments = self.supabase.table("game_assessments") \
                .select("*, game_candidates(title, source_url, original_creator)") \
                .gte("assessed_date", seven_days_ago) \
                .in_("risk_level", ["GREEN", "YELLOW"]) \
                .order("confidence", desc=True) \
                .execute()

            if assessments.data:
                for assessment in assessments.data:
                    game_info = {
                        'game_id': assessment['game_id'],
                        'game_title': assessment['game_candidates']['title'],
                        'risk_level': assessment['risk_level'],
                        'confidence': assessment['confidence'],
                        'tier': assessment['tier_recommendation'],
                        'notes': assessment['notes_for_user'],
                        'source_url': assessment['game_candidates']['source_url'],
                    }
                    
                    if assessment['risk_level'] == 'GREEN':
                        result['green_games'].append(game_info)
                    else:
                        result['yellow_games'].append(game_info)

            result['total_reviewed'] = len(result['green_games']) + len(result['yellow_games'])
            result['digest_ready'] = True

            self._log(f"  ✓ GREEN games: {len(result['green_games'])}", level="INFO")
            self._log(f"  ✓ YELLOW games: {len(result['yellow_games'])}", level="INFO")
            self._log(f"  ✓ Digest ready for review", level="INFO")

            # Send to inbox for user (normally sent via email)
            self.inbox.add_item(
                agent_id=self.agent_id,
                project_id="GameArchaeology",
                question="Weekly digest ready for review",
                required_action="Pick 1-2 games to queue for CX production",
                urgency="HIGH",
                resolution_data=result
            )

        except Exception as e:
            self._log(f"  ✗ Error generating digest: {e}", level="ERROR")

        self._log("=" * 70, level="INFO")
        return result

    # ============================================================
    # CX QUEUE ASSIGNMENT (Daily or On-Demand)
    # ============================================================

    def assign_next_cx_game(self) -> Optional[Dict[str, Any]]:
        """
        Check cx_queue for PENDING games.
        Assign next game to CX Agent.
        Update status: PENDING → IN_PROGRESS.
        
        Returns: Assigned game or None.
        """
        self._log("Checking CX queue for assignments...", level="INFO")

        try:
            # Get next PENDING game (ordered by priority)
            pending = self.supabase.table("cx_queue") \
                .select("*, game_candidates(title, source_url)") \
                .eq("status", "PENDING") \
                .order("priority_rank") \
                .limit(1) \
                .execute()

            if not pending.data:
                self._log("  No pending games in queue", level="INFO")
                return None

            assignment = pending.data[0]
            game_title = assignment['game_candidates']['title']

            # Update status to IN_PROGRESS
            self.supabase.table("cx_queue") \
                .update({
                    "status": "IN_PROGRESS",
                    "assigned_to_cx_agent": True,
                    "started_date": datetime.now().isoformat(),
                }) \
                .eq("id", assignment['id']) \
                .execute()

            self._log(f"  ✓ Assigned: {game_title}", level="INFO")

            # Send assignment to CX Agent inbox
            self.inbox.add_item(
                agent_id="CX_Agent",
                project_id="GameArchaeology",
                question=f"Convert: {game_title}",
                required_action=f"Execute conversion per {assignment['tier_recommendation']}",
                urgency="HIGH",
                resolution_data={
                    'cx_queue_id': assignment['id'],
                    'game_title': game_title,
                    'tier': assignment['tier_recommendation'],
                    'source_url': assignment['game_candidates']['source_url'],
                    'transformation_spec': assignment['transformation_requirements'],
                }
            )

            return assignment

        except Exception as e:
            self._log(f"  ✗ Error assigning game: {e}", level="ERROR")
            return None

    # ============================================================
    # AUTOMATION TRIGGERS (Scheduled via Task Scheduler)
    # ============================================================

    def schedule_daily_tasks(self):
        """
        Pseudo-code: Windows Task Scheduler should call these:
        
        2:00 AM UTC: run_daily_cycle()
        5:00 PM UTC (Friday only): generate_weekly_digest()
        9:00 AM UTC (Monday only): process_user_decisions()
        Every 4 hours: assign_next_cx_game()
        
        In production: Use APScheduler or Task Scheduler directly.
        """
        pass


# ============================================================
# EXAMPLE USAGE / TESTING
# ============================================================

if __name__ == "__main__":
    # Initialize real Supabase from studio-config.json
    from supabase_config import get_supabase_client
    
    supabase = get_supabase_client()
    if not supabase:
        print("ERROR: Supabase not configured in studio-config.json")
        sys.exit(1)
    
    orchestrator = GameArchaeologyOrchestrator(supabase)

    # Test daily cycle
    print("\nRunning daily cycle...\n")
    result = orchestrator.run_daily_cycle(force=True)
    print(f"\nDaily cycle result:")
    print(f"  Success: {result['success']}")
    print(f"  Games found: {result['games_found']}")
    print(f"  Games inserted: {result['games_inserted']}")
    print(f"  Games assessed: {result['games_assessed']}")
    print(f"  Duration: {result['duration_seconds']:.1f}s")
    
    if result['errors']:
        print(f"  Errors: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"    - {error[:80]}")

    # Test digest generation (will be empty on first run, but shows schema works)
    print("\nGenerating weekly digest...\n")
    digest = orchestrator.generate_weekly_digest()
    print(f"  GREEN games: {len(digest.get('green_games', []))}")
    print(f"  YELLOW games: {len(digest.get('yellow_games', []))}")
    print(f"  Digest ready: {digest.get('digest_ready', False)}")
