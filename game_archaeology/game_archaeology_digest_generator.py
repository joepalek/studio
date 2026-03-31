"""
Game Archaeology Digest Generator
Creates weekly email digest with game candidates and legal assessments.
Generates HTML email + decision form.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import sys

sys.path.insert(0, 'G:/My Drive/Projects/_studio')
from studio_core.logger import Logger
from studio_core.agent_inbox import AgentInbox


class DigestGenerator:
    """
    Takes output from crawler + legal agent.
    Generates: HTML email digest + decision checklist.
    """

    def __init__(self, agent_id: str = "GameArchaeology_Digest_001"):
        self.agent_id = agent_id
        self.logger = Logger(agent_id)
        self.inbox = AgentInbox()

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def generate_html_digest(
        self,
        games_data: List[Dict[str, Any]],
        legal_assessments: List[Dict[str, Any]],
        output_path: str = "game_archaeology_digest.html"
    ) -> str:
        """
        Generate HTML email digest.
        Groups by risk level (GREEN/YELLOW/RED).
        """
        self._log("Generating HTML digest...", level="INFO")

        # Group by risk level
        green_games = [a for a in legal_assessments if a['risk_level'] == 'GREEN']
        yellow_games = [a for a in legal_assessments if a['risk_level'] == 'YELLOW']
        red_games = [a for a in legal_assessments if a['risk_level'] == 'RED']

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #222; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 30px 0; }}
        .game-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .green {{ border-left: 4px solid #28a745; }}
        .yellow {{ border-left: 4px solid #ffc107; }}
        .red {{ border-left: 4px solid #dc3545; }}
        .risk-badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
        .risk-green {{ background: #d4edda; color: #155724; }}
        .risk-yellow {{ background: #fff3cd; color: #856404; }}
        .risk-red {{ background: #f8d7da; color: #721c24; }}
        .checkbox {{ margin: 20px 0; }}
        input[type="checkbox"] {{ margin-right: 10px; }}
        .tier {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Game Archaeology Weekly Digest</h1>
        <p>Date: {datetime.now().strftime('%Y-%m-%d')}</p>
        <p>New Finds: {len(legal_assessments)} | Safe: {len(green_games)} | Caution: {len(yellow_games)} | Skip: {len(red_games)}</p>
    </div>

    <div class="section">
        <h2>GREEN (Safe to Convert)</h2>
        <p>{len(green_games)} games approved for immediate conversion</p>
"""

        for i, game in enumerate(green_games, 1):
            html += f"""
        <div class="game-card green">
            <h3>{i}. {game['game_title']}</h3>
            <p><span class="risk-badge risk-green">GREEN</span> 
               <span class="tier">Confidence: {game['confidence']:.0%}</span></p>
            <p><strong>Status:</strong> {game['notes_for_user']}</p>
            <p><strong>Method:</strong> <span class="tier">{game['tier_recommendation']}</span></p>
            <p><strong>Reasoning:</strong> {game['reasoning']}</p>
            <div class="checkbox">
                <input type="checkbox" id="game_{i}" name="approve_{i}" value="true">
                <label for="game_{i}">Queue for conversion</label>
            </div>
        </div>
"""

        html += f"""
    </div>

    <div class="section">
        <h2>YELLOW (Needs Your Decision)</h2>
        <p>{len(yellow_games)} games that can be converted with caution</p>
"""

        for i, game in enumerate(yellow_games, len(green_games) + 1):
            html += f"""
        <div class="game-card yellow">
            <h3>{i}. {game['game_title']}</h3>
            <p><span class="risk-badge risk-yellow">YELLOW</span></p>
            <p><strong>Risk:</strong> {game['notes_for_user']}</p>
            <p><strong>Reasoning:</strong> {game['reasoning']}</p>
            <div class="checkbox">
                <input type="radio" name="yellow_{i}" value="approve" id="approve_{i}">
                <label for="approve_{i}">Approve & queue</label><br>
                <input type="radio" name="yellow_{i}" value="skip" id="skip_{i}">
                <label for="skip_{i}">Skip this game</label>
            </div>
        </div>
"""

        html += f"""
    </div>

    <div class="section">
        <h2>RED (Skip These)</h2>
        <p>{len(red_games)} games too risky to convert</p>
"""

        for game in red_games:
            html += f"""
        <div class="game-card red">
            <h3>X {game['game_title']}</h3>
            <p><span class="risk-badge risk-red">RED</span></p>
            <p><strong>Reason:</strong> {game['reasoning']}</p>
        </div>
"""

        html += """
    </div>

    <div class="section" style="background: #f0f0f0; padding: 20px; border-radius: 5px;">
        <h2>Next Steps</h2>
        <p>Review the games above and make your decisions:</p>
        <ol>
            <li>Approve GREEN games for immediate conversion</li>
            <li>Decide on YELLOW games (convert with caution or skip)</li>
            <li>RED games are auto-skipped</li>
        </ol>
        <p style="margin-top: 30px; text-align: center;">
            <button onclick="submitDecisions()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                SUBMIT DECISIONS
            </button>
        </p>
    </div>

    <script>
        function submitDecisions() {{
            const decisions = {{}};
            document.querySelectorAll('[type="checkbox"]:checked, input[type="radio"]:checked').forEach(el => {{
                decisions[el.id] = el.value;
            }});
            console.log('Decisions:', decisions);
            alert('Decisions recorded. Conversions will be queued.');
        }}
    </script>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        self._log(f"Generated HTML digest: {output_path}", level="INFO")

        green_count = len([a for a in legal_assessments if a.get('risk_level') == 'GREEN'])
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id="GameArchaeology",
            question=f"Digest generated: {len(legal_assessments)} games assessed, {green_count} GREEN",
            required_action="Review digest",
            urgency="LOW"
        )

        return html
    def generate_plain_text_digest(
        self,
        legal_assessments: List[Dict[str, Any]],
        output_path: str = "game_archaeology_digest.txt"
    ) -> str:
        """Generate plain text version for email."""
        self._log("Generating text digest...", level="INFO")

        # Group by risk level
        green_games = [a for a in legal_assessments if a['risk_level'] == 'GREEN']
        yellow_games = [a for a in legal_assessments if a['risk_level'] == 'YELLOW']
        red_games = [a for a in legal_assessments if a['risk_level'] == 'RED']

        text = f"""
====================================================
    GAME ARCHAEOLOGY WEEKLY DIGEST
====================================================

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
New Finds: {len(legal_assessments)} | Safe: {len(green_games)} | Caution: {len(yellow_games)} | Skip: {len(red_games)}

----------------------------------------------------
GREEN (Safe to Convert) - {len(green_games)} games
----------------------------------------------------
"""

        for i, game in enumerate(green_games, 1):
            text += f"""
{i}. {game['game_title']}
   Risk: GREEN (Confidence: {game['confidence']:.0%})
   Tier: {game['tier_recommendation']}
   Notes: {game['notes_for_user']}
   [ ] Queue for conversion

"""

        text += f"""
----------------------------------------------------
YELLOW (Decision Needed) - {len(yellow_games)} games
----------------------------------------------------
"""

        for i, game in enumerate(yellow_games, len(green_games) + 1):
            text += f"""
{i}. {game['game_title']}
   Risk: YELLOW (Confidence: {game['confidence']:.0%})
   Caution: {game['notes_for_user']}
   [ ] Approve & queue    [ ] Skip

"""

        text += f"""
----------------------------------------------------
RED (Skip These) - {len(red_games)} games
----------------------------------------------------
"""

        for game in red_games:
            text += f"""
X {game['game_title']}
   Reason: {game['reasoning'][:100]}...

"""

        text += """
====================================================
INSTRUCTIONS:
1. Review games above
2. Check boxes for GREEN games you want to convert
3. Decide on YELLOW games (approve or skip)
4. Submit your decisions
====================================================
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        self._log(f"Generated text digest: {output_path}", level="INFO")
        return text


# Example usage
if __name__ == "__main__":
    # Load sample data (would come from crawler + legal agent in production)
    sample_assessments = [
        {
            'game_title': 'Hellmaze',
            'risk_level': 'GREEN',
            'confidence': 0.88,
            'reasoning': 'Hellmaze is 16 years old from unknown creator.',
            'tier_recommendation': 'TIER_1_RECORDING',
            'notes_for_user': 'Safe to convert. 30% visual redesign recommended.',
        },
        {
            'game_title': 'Zombie Towers',
            'risk_level': 'GREEN',
            'confidence': 0.85,
            'reasoning': 'MIT licensed, source available, old framework.',
            'tier_recommendation': 'TIER_1_PLUS_2',
            'notes_for_user': 'Safe to convert. Code salvage recommended (58% reuse).',
        },
        {
            'game_title': 'Dark Mansion',
            'risk_level': 'YELLOW',
            'confidence': 0.64,
            'reasoning': 'Similar to Resident Evil. Creator unknown. Fair use applies with transformation.',
            'tier_recommendation': 'TIER_1_RECORDING',
            'notes_for_user': 'Convertible with caution. Recommend 70% visual redesign.',
        },
        {
            'game_title': 'Super Mario Clone',
            'risk_level': 'RED',
            'confidence': 0.95,
            'reasoning': 'Clear Nintendo IP derivative. High DMCA risk.',
            'tier_recommendation': 'SKIP',
            'notes_for_user': 'Too risky. Skip this game.',
        },
    ]

    generator = DigestGenerator()
    generator.generate_html_digest([], sample_assessments)
    generator.generate_plain_text_digest(sample_assessments)

    print("Digest generated successfully!")