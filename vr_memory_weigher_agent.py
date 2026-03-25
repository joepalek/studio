import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import VRCharacter, VRWorldAsset, VRInteractionEvent, SpatialAnchor, MemoryWeighting


class VRMemoryWeigherAgent:
    """VR character memory recording, contextual retrieval, and spatial anchor management."""

    def __init__(self, agent_id: str = "VR_Memory_001"):
        self.agent_id = agent_id
        self.character_memories: Dict[str, List[Dict[str, Any]]] = {}
        self.active_vr_characters: Dict[str, VRCharacter] = {}
        self.spatial_anchors: Dict[str, SpatialAnchor] = {}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"VR Memory Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def register_vr_character(self, character: VRCharacter):
        if character.id not in self.character_memories:
            self.character_memories[character.id] = []
        self.active_vr_characters[character.id] = character
        self._log(f"Memory bank initialized for VR Character '{character.name}'.")

    def record_interaction_event(self, event: VRInteractionEvent):
        if event.character_id not in self.character_memories:
            placeholder = VRCharacter(
                id=event.character_id,
                name=f"Unknown_Char_{event.character_id}",
                birth_date=datetime.date(1900, 1, 1),
                persona_traits={},
            )
            self.register_vr_character(placeholder)
        memory_entry = {
            "event_id": event.id,
            "world_id": event.world_id,
            "timestamp": event.timestamp,
            "details": event.details,
            "weight": self._calculate_memory_weight(event),
        }
        self.character_memories[event.character_id].append(memory_entry)
        self._log(f"Recorded memory for {event.character_id} with weight {memory_entry['weight']:.2f}")

    def _calculate_memory_weight(self, event: VRInteractionEvent) -> float:
        recency_factor = max(0.1, 1.0 - (datetime.datetime.now() - event.timestamp).total_seconds() / (30 * 24 * 3600))
        emotional_factor = event.details.get("emotional_impact", 0.5)
        type_factor = (1.0 if event.event_type == "CRITICAL_EVENT"
                       else 0.8 if event.event_type == "ACTION" else 0.3)
        return recency_factor * emotional_factor * type_factor

    def get_contextual_memories(self, character_id: str, current_context: Dict[str, Any],
                                 limit: int = 5) -> List[Dict[str, Any]]:
        character = self.active_vr_characters.get(character_id)
        if not character:
            character = VRCharacter(
                id=character_id,
                name=f"Unknown_Char_{character_id}",
                birth_date=datetime.date(1900, 1, 1),
                persona_traits={},
            )
        self._log(f"Retrieving contextual memories for {character_id}...", level="DEBUG")
        relevant_memories = []
        for mem in self.character_memories.get(character_id, []):
            memory_year = mem["timestamp"].year
            if character.birth_date.year < memory_year < datetime.datetime.now().year + 50:
                if any(keyword in str(mem["details"]) for keyword in current_context.get("keywords", [])):
                    relevant_memories.append(mem)
                elif current_context.get("world_id") == mem.get("world_id"):
                    relevant_memories.append(mem)
        relevant_memories.sort(key=lambda m: m["weight"], reverse=True)
        self._log(f"Retrieved {len(relevant_memories[:limit])} memories for {character_id}.")
        return relevant_memories[:limit]

    def set_spatial_anchor(self, world_id: str, anchor_id: str, coordinates: Dict[str, float],
                            associated_asset_id: Optional[str] = None):
        self._log(f"Setting spatial anchor '{anchor_id}' in world '{world_id}'...")
        new_anchor = SpatialAnchor(
            id=anchor_id,
            world_id=world_id,
            coordinates=coordinates,
            associated_asset_id=associated_asset_id,
            status="ACTIVE",
        )
        self.spatial_anchors[anchor_id] = new_anchor
        self._log(f"Spatial anchor {anchor_id} set in {world_id}.")

    def generate_digital_trace_or_ghost(self, deceased_character_id: str, world_id: str) -> Dict[str, Any]:
        self._log(f"Generating digital trace for {deceased_character_id} in {world_id}...")
        ghost_appearance_details = {
            "appearance_modifier": "translucent_flickering",
            "sound_effect": "faint_whisper_or_old_radio_static",
            "behavior_script": "path_patrol_near_significant_memory_location",
            "interaction_logic": "responds_with_faded_memories_only",
        }
        self._send_to_inbox(
            deceased_character_id,
            f"Digital trace generated for {deceased_character_id} in world {world_id}. Review and approve.",
            "APPROVE_GHOST_DEPLOYMENT_OR_REVISE",
        )
        return {"character_id": deceased_character_id, "world_id": world_id, "details": ghost_appearance_details}
