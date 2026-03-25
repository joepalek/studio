import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import AudioAsset, BandStyleCard, TrackGenerationRequest, VoiceModel
from internal_asset_flow_agent import InternalAssetIdeaFlowAgent


class MusicProductionAgent:
    """AI music production: sonic archeology, voice model training, track generation."""

    def __init__(self, agent_id: str = "Music_Prod_001"):
        self.agent_id = agent_id
        self.band_style_cards: Dict[str, BandStyleCard] = {}
        self.voice_models: Dict[str, VoiceModel] = {}
        self.audio_processing_queue: List[Dict[str, Any]] = []
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Music Prod Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def register_band_style_card(self, band_id: str, style_card: BandStyleCard):
        self.band_style_cards[band_id] = style_card
        self._log(f"Band Style Card for '{band_id}' registered.")
        if style_card.vocal_dna_source_audio_path:
            self.train_voice_model(band_id, style_card.vocal_dna_source_audio_path)

    def add_audio_for_processing(self, audio_asset: AudioAsset):
        self._log(f"Adding audio asset {audio_asset.id} for processing.")
        self.audio_processing_queue.append({"asset": audio_asset, "status": "QUEUED"})
        self._process_next_audio_in_queue()

    def _process_next_audio_in_queue(self):
        if not self.audio_processing_queue:
            return
        current_item = self.audio_processing_queue[0]
        asset = current_item["asset"]
        if current_item["status"] == "QUEUED":
            current_item["status"] = "PROCESSING"
            self._log(f"Starting Sonic Archeology for {asset.id}...", level="DEBUG")
            isolated_stems = {
                "vocals": f"{asset.path}_vocals.wav",
                "drums": f"{asset.path}_drums.wav",
                "bass": f"{asset.path}_bass.wav",
                "other": f"{asset.path}_other.wav",
            }
            cleaned_stems = {k: v.replace(".wav", "_cleaned.wav") for k, v in isolated_stems.items()}
            asset.metadata["cleaned_stems"] = cleaned_stems
            asset.status = "CLEANED_AND_STEMMED"
            current_item["status"] = "COMPLETED"
            self._log(f"Sonic Archeology for {asset.id} completed.")
            self.audio_processing_queue.pop(0)
            self._process_next_audio_in_queue()

    def train_voice_model(self, band_id: str, source_audio_path: str):
        self._log(f"Training voice model for {band_id}...", level="INFO")
        voice_model_id = f"VM_{band_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_voice_model = VoiceModel(
            id=voice_model_id,
            band_id=band_id,
            source_audio_path=source_audio_path,
            status="TRAINED",
            model_path=f"models/{voice_model_id}.pth",
        )
        self.voice_models[band_id] = new_voice_model
        self._log(f"Voice model {voice_model_id} trained for {band_id}.")
        if band_id in self.band_style_cards:
            self.band_style_cards[band_id].vocal_dna_model_id = voice_model_id

    def generate_music_track(self, request: TrackGenerationRequest) -> AudioAsset:
        self._log(f"Generating track '{request.title}' for '{request.band_id}'...")
        band_style = self.band_style_cards.get(request.band_id)
        voice_model = self.voice_models.get(request.band_id)
        if not band_style or not voice_model:
            self._log(f"Error: Missing band style or voice model for {request.band_id}.", level="ERROR")
            raise ValueError("Missing band style or voice model.")

        generated_instrumental_path = f"generated/instrumental_{request.id}.wav"
        final_mix_path = generated_instrumental_path

        if request.lyrics and voice_model.status == "TRAINED":
            generated_vocals_path = f"generated/vocals_{request.id}.wav"
            if request.adjustments:
                generated_vocals_path = generated_vocals_path.replace(".wav", "_adjusted.wav")
            final_mix_path = f"generated/{request.id}_final.wav"
            self._log(f"Vocals mixed into: {final_mix_path}")

        final_mix_path_humanized = final_mix_path.replace(".wav", "_humanized.wav")
        new_track_asset = AudioAsset(
            id=request.id,
            title=request.title,
            path=final_mix_path_humanized,
            type="AI_GENERATED_TRACK",
            status="MASTERED_FOR_TESTING",
            band_id=request.band_id,
            metadata={"genre": request.genre, "mood": request.mood, "lyrics_present": bool(request.lyrics)},
        )
        self._log(f"Track '{new_track_asset.title}' generated for {request.band_id}.", level="INFO")
        return new_track_asset
