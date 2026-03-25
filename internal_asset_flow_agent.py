import datetime
from typing import Dict, Any, List, Literal

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import StudioAsset, Idea, WhiteboardEntry


class InternalAssetIdeaFlowAgent:
    """Asset library and whiteboard idea management with dormancy re-evaluation."""

    def __init__(self, agent_id: str = "Internal_Asset_Flow_001"):
        self.agent_id = agent_id
        self.asset_library: Dict[str, StudioAsset] = {}
        self.whiteboard_ideas: Dict[str, Idea] = {}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Asset Flow Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def register_asset(self, asset: StudioAsset):
        self.asset_library[asset.id] = asset
        self._log(f"Asset {asset.id} (Type: {asset.type}) registered. Status: {asset.status}")
        self._assess_asset_for_flow(asset.id)

    def add_idea_to_whiteboard(self, idea: Idea):
        self.whiteboard_ideas[idea.id] = idea
        self._log(f"Idea {idea.id} (Source: {idea.source}) added. Rating: {idea.rating}")
        self._assess_idea_for_progression(idea.id)

    def _assess_asset_for_flow(self, asset_id: str):
        asset = self.asset_library.get(asset_id)
        if not asset:
            return
        if asset.status == "DORMANT":
            asset.status = "UNDER_RE_EVALUATION"
            self._send_to_inbox(asset.id, f"Dormant asset {asset.id} being re-evaluated.", "MONITOR_RE_EVALUATION")
            return
        if asset.type == "GENERATED_CONTENT" and asset.status == "READY_FOR_QA":
            asset.status = "IN_QA"
        elif asset.type == "AI_BAND_TRACK" and asset.status == "MASTERED_FOR_TESTING":
            asset.status = "IN_A&R_TESTING"

    def _assess_idea_for_progression(self, idea_id: str):
        idea = self.whiteboard_ideas.get(idea_id)
        if not idea:
            return
        if idea.status == "NEW" and idea.rating >= 8:
            idea.status = "FEASIBILITY_STUDY"
            self._send_to_inbox(idea.id, f"High-potential idea '{idea.title}' (Rating: {idea.rating}) for feasibility study.",
                                "REVIEW_FEASIBILITY_AND_APPROVE_PROJECT")
        elif idea.status == "ARCHIVED" and (datetime.datetime.now() - idea.last_re_evaluated_date).days > 30:
            idea.last_re_evaluated_date = datetime.datetime.now()
            idea.status = "UNDER_RE_EVALUATION_ARCHIVE"

    def re_scan_archived_items(self):
        self._log("Re-scanning archived ideas and dormant assets.")
        for idea_id in list(self.whiteboard_ideas):
            if self.whiteboard_ideas[idea_id].status == "ARCHIVED":
                self._assess_idea_for_progression(idea_id)
        for asset_id in list(self.asset_library):
            if self.asset_library[asset_id].status == "DORMANT":
                self._assess_asset_for_flow(asset_id)
