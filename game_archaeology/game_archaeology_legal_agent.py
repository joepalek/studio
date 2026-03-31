"""
Game Archaeology Legal Agent
Specialized legal review for old game IP, copyright, fair use, and licensing.
Runs weekly, analyzes ~20 games for safe conversion.
"""

import datetime
import json
from typing import Dict, Any, List, Literal, Optional
from dataclasses import dataclass, field

# Import from studio_core
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio')
from studio_core.logger import Logger
from studio_core.agent_inbox import AgentInbox


@dataclass
class GameCandidate:
    """Represents an old game found in archives."""
    title: str
    original_creator: Optional[str]
    release_date: Optional[str]
    source_url: str
    has_source_code: bool
    game_type: str  # Flash, HTML5, Python, etc.
    ip_status: str  # Original, Fan game, Adaptation, etc.


@dataclass
class LegalAssessment:
    """Output of legal review for a game."""
    game_title: str
    risk_level: Literal["GREEN", "YELLOW", "RED"]
    confidence: float  # 0.0-1.0
    reasoning: str
    transformation_requirements: Dict[str, Any]
    tier_recommendation: str  # TIER_1_RECORDING, TIER_2_SALVAGE, TIER_1_PLUS_2
    notes_for_user: str


class GameArchaeologyLegalAgent:
    """
    Reviews old games for copyright/licensing considerations.
    Determines safe transformation thresholds.
    
    Runs weekly via Windows Task Scheduler.
    Outputs: Supabase table + daily digest via email.
    """

    def __init__(self, agent_id: str = "GameArchaeology_Legal_001"):
        self.agent_id = agent_id
        self.logger = Logger(agent_id)
        self.inbox = AgentInbox()
        self.assessments: List[LegalAssessment] = []
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def assess_game(self, game: GameCandidate) -> LegalAssessment:
        """
        Assess a single game for legal safety.
        Returns: GREEN (safe), YELLOW (caution), or RED (skip).
        """
        self._log(f"Assessing: {game.title} ({game.release_date})", level="DEBUG")

        # Rule 1: Very old games are safer (20+ years old)
        try:
            year = int(game.release_date[:4])
            age = 2026 - year
        except:
            age = 0

        # Rule 2: Unknown creators = safer (likely abandoned)
        is_abandoned = not game.original_creator or "unknown" in str(game.original_creator).lower()

        # Rule 3: Source code availability
        has_source = game.has_source_code

        # Default assessment
        risk_level = "GREEN"
        confidence = 0.72
        reasoning = ""
        tier = "TIER_1_RECORDING"
        visual_redesign_pct = 30

        # Logic: Games 15+ years old with unknown creators are very safe
        if age >= 15 and is_abandoned:
            risk_level = "GREEN"
            confidence = 0.88
            reasoning = (
                f"{game.title} is {age} years old from unknown/inactive creator. "
                "Fair use applies if you transform visuals significantly. "
                "No active IP holder to enforce."
            )
            visual_redesign_pct = 30
            tier = "TIER_1_RECORDING"

        # Games 10-14 years old need more caution
        elif age >= 10 and is_abandoned:
            risk_level = "YELLOW"
            confidence = 0.68
            reasoning = (
                f"{game.title} is {age} years old. Creator status unclear. "
                "Fair use applies, but recommend 50%+ visual redesign to be safe."
            )
            visual_redesign_pct = 50
            tier = "TIER_1_RECORDING"

        # Games with active creators or known IP = RED
        elif game.original_creator and "unknown" not in str(game.original_creator).lower():
            risk_level = "RED"
            confidence = 0.85
            reasoning = (
                f"Original creator '{game.original_creator}' is known/potentially active. "
                "High risk of DMCA. Recommend skipping unless you have explicit permission."
            )
            tier = "SKIP"

        # Games that are obvious derivatives (clones, mods)
        elif any(word in game.title.lower() for word in ["clone", "mod", "remake", "tribute"]):
            if age < 10:
                risk_level = "RED"
                confidence = 0.80
                reasoning = (
                    "Game is a clear derivative work (contains 'clone', 'mod', etc.). "
                    "High legal risk unless original property owner has abandoned it."
                )
                tier = "SKIP"
            else:
                risk_level = "YELLOW"
                confidence = 0.65
                tier = "TIER_1_RECORDING"

        # If source code is available, TIER_2 is an option
        if has_source:
            if tier != "SKIP":
                tier = "TIER_1_PLUS_2"

        assessment = LegalAssessment(
            game_title=game.title,
            risk_level=risk_level,
            confidence=confidence,
            reasoning=reasoning,
            transformation_requirements={
                "visual_redesign_percent": visual_redesign_pct,
                "mechanic_changes_required": (
                    "Core loop can stay same, enemy behavior/AI can change"
                    if risk_level != "RED"
                    else "Cannot use without permission"
                ),
                "layout_flexibility": "Can keep room structure" if risk_level != "RED" else "N/A",
                "attribution_needed": risk_level != "RED",
            },
            tier_recommendation=tier,
            notes_for_user=(
                f"Safe to convert. {visual_redesign_pct}% visual redesign recommended."
                if risk_level == "GREEN"
                else (
                    f"Convertible with caution. Recommend {visual_redesign_pct}% visual redesign."
                    if risk_level == "YELLOW"
                    else "Too risky. Skip this game."
                )
            ),
        )

        return assessment

    def assess_batch(self, games: List[GameCandidate]) -> List[LegalAssessment]:
        """Assess multiple games. Used for weekly batch runs."""
        self._log(f"Assessing batch of {len(games)} games...", level="INFO")
        assessments = []

        for game in games:
            try:
                assessment = self.assess_game(game)
                assessments.append(assessment)
                self._log(
                    f"  {game.title} → {assessment.risk_level} "
                    f"(confidence: {assessment.confidence:.2f})",
                    level="INFO"
                )
            except Exception as e:
                self._log(f"  Error assessing {game.title}: {e}", level="ERROR")

        self.assessments = assessments
        self._log(f"Batch assessment complete: {len(assessments)} games reviewed", level="INFO")
        return assessments

    def export_assessment_json(self, output_path: str = "game_archaeology_legal_results.json"):
        """Export assessments to JSON for Supabase ingestion."""
        results = []
        for assessment in self.assessments:
            results.append({
                "game_title": assessment.game_title,
                "risk_level": assessment.risk_level,
                "confidence": assessment.confidence,
                "reasoning": assessment.reasoning,
                "transformation_requirements": assessment.transformation_requirements,
                "tier_recommendation": assessment.tier_recommendation,
                "notes_for_user": assessment.notes_for_user,
                "assessed_at": datetime.datetime.now().isoformat(),
            })

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        self._log(f"Exported {len(results)} assessments to {output_path}", level="INFO")
        return results

    def send_to_inbox(self, game_title: str, risk_level: str, notes: str):
        """Send notable findings to agent inbox."""
        urgency = "HIGH" if risk_level == "RED" else "MEDIUM" if risk_level == "YELLOW" else "LOW"
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id="GameArchaeology",
            question=f"Legal review: {game_title}",
            required_action=f"Game classified as {risk_level}. {notes}",
            urgency=urgency,
        )


# Example usage / testing
if __name__ == "__main__":
    agent = GameArchaeologyLegalAgent()

    # Test games
    test_games = [
        GameCandidate(
            title="Hellmaze",
            original_creator="Unknown",
            release_date="2010-01-01",
            source_url="https://archive.org/...",
            has_source_code=False,
            game_type="Flash",
            ip_status="Original",
        ),
        GameCandidate(
            title="Flappy Bird Clone v3",
            original_creator="Unknown",
            release_date="2014-01-01",
            source_url="https://itch.io/...",
            has_source_code=True,
            game_type="JavaScript",
            ip_status="Fan Game",
        ),
        GameCandidate(
            title="Mario Remake 2023",
            original_creator="Nintendo",
            release_date="2023-01-01",
            source_url="https://github.com/...",
            has_source_code=True,
            game_type="Python",
            ip_status="Adaptation",
        ),
    ]

    assessments = agent.assess_batch(test_games)
    agent.export_assessment_json()

    print("\n=== LEGAL ASSESSMENT SUMMARY ===")
    for a in assessments:
        print(f"{a.game_title}: {a.risk_level} (confidence: {a.confidence:.2f})")
