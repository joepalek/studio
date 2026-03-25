import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import VRCharacter, VRWorldAsset, VRInteractionEvent, BehaviorTree


class VRBehaviorEngineAgent:
    """VR character registration, behavior tree management, and action simulation."""

    def __init__(self, agent_id: str = "VR_Behavior_001"):
        self.agent_id = agent_id
        self.active_vr_characters: Dict[str, VRCharacter] = {}
        self.active_vr_worlds: Dict[str, VRWorldAsset] = {}
        self.behavior_trees: Dict[str, BehaviorTree] = {}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"VR Behavior Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def register_vr_character(self, character: VRCharacter, world_id: str):
        if world_id not in self.active_vr_worlds:
            self._log(f"World {world_id} not registered. Auto-creating placeholder.", level="WARNING")
            self.active_vr_worlds[world_id] = VRWorldAsset(
                id=world_id, name="Temp World", description="", path="",
                status="ACTIVE", artist_info={"name": "N/A", "link": None},
            )
        self.active_vr_characters[character.id] = character
        self.active_vr_characters[character.id].current_world_id = world_id
        self._log(f"VR Character '{character.name}' registered in world '{world_id}'.")
        if not character.backstory:
            self._log(f"Character {character.id} has no backstory. Manual creation required.", level="WARNING")

    def define_behavior_tree(self, tree_id: str, definition: Dict[str, Any]) -> BehaviorTree:
        self._log(f"Defining behavior tree '{tree_id}'...")
        new_tree = BehaviorTree(id=tree_id, definition=definition, status="ACTIVE")
        self.behavior_trees[tree_id] = new_tree
        self._log(f"Behavior tree '{tree_id}' defined.")
        return new_tree

    def update_character_state(self, character_id: str, new_state: Dict[str, Any]):
        character = self.active_vr_characters.get(character_id)
        if not character:
            self._log(f"Error: Character {character_id} not found.", level="ERROR")
            return
        character.current_state.update(new_state)
        self._log(f"Character {character_id} state updated.", level="DEBUG")

    def simulate_character_action(self, character_id: str, current_environment_context: Dict[str, Any]) -> str:
        character = self.active_vr_characters.get(character_id)
        if not character:
            self._log(f"Error: Character {character_id} not found.", level="ERROR")
            return "NO_ACTION"
        self._log(f"Simulating action for character {character_id}...", level="DEBUG")
        relevant_memories = [{"event": "saw player at market",
                               "timestamp": datetime.datetime.now() - datetime.timedelta(hours=2)}]

        if character.birth_date.year < 1950 and "VR_ITEM_MODERN_PHONE" in current_environment_context.get("items_present", []):
            action = f"Character {character.name} (from {character.birth_date.year}) stares curiously at the modern phone."
        elif "player_nearby" in current_environment_context:
            action = f"Character {character.name} greets player based on past interaction."
        else:
            action = f"Character {character.name} proceeds with routine patrol."

        self.update_character_state(character_id, {"last_action": action, "timestamp": datetime.datetime.now()})
        interaction_event = VRInteractionEvent(
            id=f"INTERACT_{character_id}_{datetime.datetime.now().strftime('%H%M%S')}",
            character_id=character_id,
            world_id=character.current_world_id,
            event_type="ACTION",
            details={"action": action},
            timestamp=datetime.datetime.now(),
        )
        return action

    def deploy_clue_givers_npcs(self, world_id: str, geocaching_logic_config: Dict[str, Any]):
        self._log(f"Deploying clue-giver NPCs for geocaching in world {world_id}...")
        npc_count = geocaching_logic_config.get("clue_giver_npcs", 3)
        self._log(f"{npc_count} clue-giver NPCs deployed to world {world_id}.")
