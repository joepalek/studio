import datetime
from typing import Dict, Any, List, Optional, Literal


class AgentInbox:
    """Central hub for managing items that require supervisor review and action.
    Agents add items here; the supervisor resolves them. Singleton pattern.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentInbox, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.items: List[Dict[str, Any]] = []
        self._next_item_id = 1
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
            f"[AgentInbox] [INFO] Initialized."
        )

    def add_item(
        self,
        agent_id: str,
        project_id: str,
        question: str,
        required_action: str,
        status: Literal[
            "PENDING_SUPERVISOR_REVIEW", "RESOLVED", "ARCHIVED"
        ] = "PENDING_SUPERVISOR_REVIEW",
        urgency: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM",
        resolution_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        item_id = f"INBOX_{self._next_item_id:04d}"
        self._next_item_id += 1
        new_item = {
            "id": item_id,
            "timestamp": datetime.datetime.now(),
            "agent_id": agent_id,
            "project_id": project_id,
            "question": question,
            "required_action": required_action,
            "status": status,
            "urgency": urgency,
            "resolution_data": resolution_data,
        }
        self.items.append(new_item)
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [AgentInbox] [INFO] "
            f"Item '{item_id}' added by '{agent_id}' for '{project_id}' (Urgency: {urgency})."
        )
        return item_id

    def get_pending_items(
        self,
        urgency_filter: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None,
    ) -> List[Dict[str, Any]]:
        urgency_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        pending = [item for item in self.items if item["status"] == "PENDING_SUPERVISOR_REVIEW"]
        if urgency_filter and urgency_filter in urgency_map:
            filter_level = urgency_map[urgency_filter]
            pending = [item for item in pending if urgency_map.get(item["urgency"], 0) >= filter_level]
        pending.sort(key=lambda item: (urgency_map.get(item["urgency"], 0), item["timestamp"]))
        return pending

    def resolve_item(self, item_id: str, resolution_data: Dict[str, Any]) -> bool:
        for item in self.items:
            if item["id"] == item_id and item["status"] == "PENDING_SUPERVISOR_REVIEW":
                item["status"] = "RESOLVED"
                item["resolution_data"] = resolution_data
                print(
                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [AgentInbox] [INFO] "
                    f"Item '{item_id}' resolved."
                )
                return True
        return False

    def get_resolved_item(
        self, agent_id: str, project_id: str
    ) -> Optional[Dict[str, Any]]:
        for i, item in enumerate(self.items):
            if (
                item["agent_id"] == agent_id
                and item["project_id"] == project_id
                and item["status"] == "RESOLVED"
            ):
                resolved_item = self.items.pop(i)
                resolved_item["status"] = "ARCHIVED"
                return resolved_item
        return None

    def get_all_items(self) -> List[Dict[str, Any]]:
        return self.items
