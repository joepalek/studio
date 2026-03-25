import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import AudioAsset, BandStyleCard, CharacterAvatar, MusicVideo, VirtualGigOffer
from internal_asset_flow_agent import InternalAssetIdeaFlowAgent


class VirtualPerformanceAgent:
    """Music video production, 3D performance asset preparation, and virtual gig pitching."""

    def __init__(self, agent_id: str = "Virtual_Perf_001"):
        self.agent_id = agent_id
        self.band_roster: Dict[str, Any] = {}
        self.virtual_venues: Dict[str, Any] = {}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Virtual Perf Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def register_band_for_performance(self, band_id: str, band_style_card: BandStyleCard,
                                       character_avatars: List[CharacterAvatar]):
        self.band_roster[band_id] = {
            "style_card": band_style_card,
            "character_avatars": {avatar.id: avatar for avatar in character_avatars},
            "status": "REGISTERED",
        }
        self._log(f"Band '{band_id}' registered with {len(character_avatars)} avatars.")

    def produce_music_video(self, audio_asset: AudioAsset, band_id: str,
                             visual_style_prompt: str, character_seeds: List[str]) -> MusicVideo:
        band_data = self.band_roster.get(band_id)
        if not band_data:
            self._log(f"Error: Band '{band_id}' not registered.", level="ERROR")
            raise ValueError(f"Band {band_id} not registered.")
        self._log(f"Producing music video for '{audio_asset.title}' by '{band_id}'...")
        video_id = f"MV_{audio_asset.id}"
        generated_video_path = f"generated/music_videos/{video_id}.mp4"
        new_music_video = MusicVideo(
            id=video_id,
            audio_asset_id=audio_asset.id,
            band_id=band_id,
            path=generated_video_path,
            status="DRAFT",
            visual_style_prompt=visual_style_prompt,
        )
        self._send_to_inbox(
            new_music_video.id,
            f"Draft music video '{new_music_video.id}' for '{band_id}' ready for review.",
            "REVIEW_MUSIC_VIDEO_AND_APPROVE",
        )
        return new_music_video

    def prepare_3d_performance_assets(self, band_id: str) -> List[Dict[str, Any]]:
        band_data = self.band_roster.get(band_id)
        if not band_data:
            self._log(f"Error: Band '{band_id}' not registered.", level="ERROR")
            return []
        self._log(f"Preparing 3D performance assets for '{band_id}'...")
        prepared_assets = []
        for avatar_id, avatar in band_data["character_avatars"].items():
            prepared_assets.append({
                "character_id": avatar_id,
                "model_format": "glTF",
                "model_path": f"prepared_assets/{avatar_id}.gltf",
                "motion_data_path": f"prepared_assets/{avatar_id}_motion.json",
                "vfx_specs": "NotchLC_compatible_specs.json",
            })
        self._log(f"Prepared {len(prepared_assets)} 3D assets for '{band_id}'.")
        return prepared_assets

    def pitch_virtual_gig(self, band_id: str, venue_name: str,
                           prepared_assets: List[Dict[str, Any]]) -> VirtualGigOffer:
        band_data = self.band_roster.get(band_id)
        if not band_data:
            self._log(f"Error: Band '{band_id}' not registered.", level="ERROR")
            raise ValueError(f"Band {band_id} not registered.")
        pitch_id = f"PITCH_{band_id}_{venue_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        gig_offer = VirtualGigOffer(
            id=pitch_id,
            band_id=band_id,
            venue_name=venue_name,
            offer_details={"date": datetime.date.today() + datetime.timedelta(days=90),
                           "fee": 10000.0, "platform": "Metaverse_Fest"},
            status="OFFERED",
        )
        self._send_to_inbox(
            gig_offer.id,
            f"Virtual gig offer for '{band_id}' at '{venue_name}'. Fee: ${gig_offer.offer_details.get('fee', 0)}",
            "REVIEW_GIG_OFFER_AND_APPROVE",
            urgency="HIGH",
        )
        return gig_offer
