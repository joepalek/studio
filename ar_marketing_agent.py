import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import AudioAsset, MusicRelease, MarketingCampaign, MiroFishReport


class ARMarketingAgent:
    """A&R and marketing agent for AI music releases. Integrates MiroFish simulation."""

    def __init__(self, agent_id: str = "AR_Marketing_001"):
        self.agent_id = agent_id
        self.artist_roster: Dict[str, Any] = {}
        self.release_pipeline: List[MusicRelease] = []
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.mirofish_enabled: bool = False
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"A&R/Marketing Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def enable_mirofish_integration(self):
        self.mirofish_enabled = True
        self._log("Mirofish integration ENABLED.")

    def submit_track_for_ar_review(self, audio_asset: AudioAsset, band_id: str):
        self._log(f"Submitting track '{audio_asset.title}' for A&R review for {band_id}.")
        if not self.mirofish_enabled:
            self._log("Mirofish not enabled. Manual review required.", level="WARNING")
            self._send_to_inbox(audio_asset.id, f"Track '{audio_asset.title}' needs manual A&R review.", "MANUAL_AR_REVIEW_AND_DECISION")
            return
        sim_report = MiroFishReport(
            track_id=audio_asset.id,
            metrics_data={"viral_score": 0.88, "engagement_rate": 0.07, "emotional_resonance": 0.75},
            summary="Mirofish predicts high viral potential.",
        )
        self._process_mirofish_results(audio_asset, band_id, sim_report)

    def _process_mirofish_results(self, audio_asset: AudioAsset, band_id: str, sim_report: MiroFishReport):
        self._log(f"Processing Mirofish results for track '{audio_asset.title}'.")
        if (sim_report.metrics_data.get("viral_score", 0) > 0.8
                and sim_report.metrics_data.get("emotional_resonance", 0) > 0.7):
            self._send_to_inbox(
                audio_asset.id,
                f"Track '{audio_asset.title}' shows high A&R potential. Recommend as lead single.",
                "APPROVE_LEAD_SINGLE_AND_INITIATE_MV_PRODUCTION",
                urgency="HIGH",
            )
        else:
            self._send_to_inbox(
                audio_asset.id,
                f"Track '{audio_asset.title}' did not meet A&R targets. Recommend album deep cut.",
                "REVIEW_TRACK_FOR_ALBUM_OR_REVISION",
            )

    def plan_release_strategy(self, band_id: str, tracks_for_release: List[AudioAsset],
                               release_type: Literal["SINGLE", "ALBUM"], target_date: datetime.date):
        release_id = f"REL_{band_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_release = MusicRelease(
            id=release_id, band_id=band_id, tracks=[a.id for a in tracks_for_release],
            release_type=release_type, target_date=target_date, status="PLANNED",
        )
        self.release_pipeline.append(new_release)
        self._send_to_inbox(release_id, f"{release_type} release for '{band_id}' drafted.", "APPROVE_RELEASE_PLAN_AND_MARKETING")
