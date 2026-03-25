import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import VRWorldAsset, ArtistSubmission, TechnicalRequirementsDoc
from internal_asset_flow_agent import InternalAssetIdeaFlowAgent


class VRSceneGeneratorAgent:
    """VR environment generation, artist world curation, and geocaching integration."""

    def __init__(self, agent_id: str = "VR_Scene_Gen_001"):
        self.agent_id = agent_id
        self.curated_worlds: Dict[str, VRWorldAsset] = {}
        self.technical_requirements: Dict[str, Any] = self._load_technical_requirements()
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"VR Scene Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def _load_technical_requirements(self) -> Dict[str, Any]:
        return {
            "polygon_count_max": 200000,
            "texture_resolution_max": "2048x2048",
            "asset_file_formats": ["glTF", "FBX", "USD"],
            "scripting_languages_allowed": ["C#", "Python_for_behaviors"],
            "optimization_score_min": 0.8,
        }

    def generate_vr_environment(self, theme: str, mood: str, architectural_style: str) -> VRWorldAsset:
        self._log(f"Generating VR environment: theme='{theme}', mood='{mood}', style='{architectural_style}'...")
        world_id = f"VRW_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        generated_path = f"generated/vr_worlds/{world_id}.gltf"
        new_world = VRWorldAsset(
            id=world_id,
            name=f"{theme} {architectural_style} World",
            description=f"AI-generated VR environment: {theme}, {mood}.",
            path=generated_path,
            status="DRAFT_AI_GENERATED",
            artist_info={"name": "AI Generated", "link": None},
        )
        self.curated_worlds[world_id] = new_world
        self._send_to_inbox(
            new_world.id,
            f"AI-generated VR world '{new_world.name}' ready for initial review.",
            "REVIEW_AI_GENERATED_VR_WORLD",
        )
        return new_world

    def submit_artist_world_for_curation(self, submission: ArtistSubmission):
        self._log(f"Processing artist submission '{submission.world_name}' by '{submission.artist_name}'...")
        compliance_check = self._run_technical_compliance_check(submission.world_file_metadata)
        if not compliance_check["passed"]:
            self._log(f"Submission '{submission.world_name}' FAILED technical compliance.", level="WARNING")
            self._send_to_inbox(
                submission.id,
                f"Artist submission '{submission.world_name}' failed compliance: {', '.join(compliance_check['issues'])}",
                "REVIEW_ARTIST_SUBMISSION_ISSUES_AND_ADVISE",
            )
            return
        self._log(f"Submission '{submission.world_name}' PASSED technical compliance.")
        world_id = f"VRW_ARTIST_{submission.id}"
        new_world_asset = VRWorldAsset(
            id=world_id,
            name=submission.world_name,
            description=submission.world_description,
            path=submission.world_file_path,
            status="PENDING_CURATION_REVIEW",
            artist_info={"name": submission.artist_name, "link": submission.portfolio_link},
        )
        self.curated_worlds[world_id] = new_world_asset
        self._send_to_inbox(
            new_world_asset.id,
            f"Artist world '{new_world_asset.name}' passed technical check. Requires curation review.",
            "REVIEW_ARTIST_VR_WORLD_FOR_CURATION",
        )

    def _run_technical_compliance_check(self, world_metadata: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        passed = True
        if world_metadata.get("polygon_count", 0) > self.technical_requirements["polygon_count_max"]:
            issues.append(
                f"Polygon count ({world_metadata['polygon_count']}) exceeds max "
                f"({self.technical_requirements['polygon_count_max']})."
            )
            passed = False
        if world_metadata.get("texture_resolution_max", "") != self.technical_requirements["texture_resolution_max"]:
            issues.append(f"Texture resolution ({world_metadata.get('texture_resolution_max')}) non-compliant.")
            passed = False
        return {"passed": passed, "issues": issues}

    def integrate_world_for_geocaching(self, world_id: str, geocaching_logic_config: Dict[str, Any]):
        world = self.curated_worlds.get(world_id)
        if not world or world.status != "APPROVED":
            self._log(f"Error: World {world_id} not found or not approved.", level="ERROR")
            return
        self._log(f"Integrating world '{world.name}' for geocaching...")
        world.status = "INTEGRATED_FOR_GEOCACHING"
        self._log(f"World '{world.name}' successfully integrated for geocaching.")
