import datetime
from typing import Dict, Any, List, Literal

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import Subscription, HardwareAsset, ResourceUsageReport, FundingAlert
from financial_billing_agent import FinancialBillingAgent


class ResourceSubscriptionManagementAgent:
    """Resource and subscription monitoring, hardware allocation, and wishlist funding."""

    def __init__(self, agent_id: str = "Resource_Mgmt_001"):
        self.agent_id = agent_id
        self.subscriptions: Dict[str, Subscription] = self._load_initial_subscriptions()
        self.hardware_assets: Dict[str, HardwareAsset] = self._load_initial_hardware()
        self.paid_tier_wishlist: List[Dict[str, Any]] = self._load_initial_wishlist()
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.financial_agent = FinancialBillingAgent()
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Resource Mgmt Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def _load_initial_subscriptions(self) -> Dict[str, Subscription]:
        return {
            "ClaudeCode": Subscription(id="CLAUDE_001", service="ClaudeCode", tier="FREE",
                                       status="ACTIVE", cost_monthly=0.0, usage_limit="CAPPED"),
            "GeminiFlash": Subscription(id="GFL_001", service="GeminiFlash", tier="FREE",
                                        status="ACTIVE", cost_monthly=0.0, usage_limit="CAPPED"),
            "ElevenLabs": Subscription(id="EL_001", service="ElevenLabs", tier="FREE_TRIAL",
                                       status="ACTIVE", cost_monthly=0.0, usage_limit="LIMITED"),
            "GoogleDrive": Subscription(id="GD_001", service="GoogleDrive", tier="FREE",
                                        status="ACTIVE", cost_monthly=0.0, usage_limit="15GB"),
        }

    def _load_initial_hardware(self) -> Dict[str, HardwareAsset]:
        return {
            "External_PC_GPU": HardwareAsset(
                id="GPU_EX001", name="External AI System GPU", type="GPU",
                status="EXISTING", capacity="Low-End", availability="LOCAL_EXTERNAL", allocated_tasks=[],
            )
        }

    def _load_initial_wishlist(self) -> List[Dict[str, Any]]:
        return [
            {"id": "WL_001", "name": "Enhanced Claude Code Subscription", "category": "AI_SERVICE",
             "cost_estimate": 500.0, "priority": 1, "status": "PENDING_FUNDING",
             "impact": "Resolves primary bottleneck, unlocks all projects."},
            {"id": "WL_002", "name": "Dedicated GPU Hardware", "category": "HARDWARE",
             "cost_estimate": 2500.0, "priority": 2, "status": "PENDING_FUNDING",
             "impact": "Massive offload, new local AI capabilities."},
            {"id": "WL_003", "name": "ElevenLabs Paid Tier", "category": "AI_SERVICE",
             "cost_estimate": 50.0, "priority": 3, "status": "PENDING_FUNDING",
             "impact": "Professional vocal consistency for AI Music Label."},
            {"id": "WL_004", "name": "Google Drive Storage Upgrade", "category": "CLOUD_STORAGE",
             "cost_estimate": 10.0, "priority": 4, "status": "PENDING_FUNDING",
             "impact": "Accommodates large data sets."},
        ]

    def monitor_all_resources(self):
        self._log("Monitoring all resources and subscriptions...", level="DEBUG")
        current_usage = {
            "ClaudeCode": {"usage": "HIGH"}, "GeminiFlash": {"usage": "HIGH"},
            "ElevenLabs": {"usage": "LOW"}, "GoogleDrive": {"usage": "10GB"},
        }
        for sub_id, sub in self.subscriptions.items():
            if sub.status == "ACTIVE" and sub.usage_limit == "CAPPED" and \
                    current_usage.get(sub.service, {}).get("usage") == "HIGH":
                self._send_to_inbox(
                    sub_id,
                    f"{sub.service} usage is capped. Upgrade recommended.",
                    "APPROVE_SUBSCRIPTION_UPGRADE",
                    urgency="HIGH",
                )
        gpu_asset = self.hardware_assets.get("External_PC_GPU")
        if gpu_asset and gpu_asset.status == "OVERLOADED":
            self._send_to_inbox(
                gpu_asset.id,
                "External AI System GPU is overloaded.",
                "REVIEW_GPU_USAGE_AND_OPTIMIZE",
            )

    def allocate_hardware_task(self, hardware_id: str, task_id: str, agent_requesting: str) -> bool:
        hardware = self.hardware_assets.get(hardware_id)
        if not hardware:
            self._log(f"Hardware {hardware_id} not found.", level="ERROR")
            return False
        if hardware.status == "OVERLOADED":
            self._log(f"Hardware {hardware_id} overloaded. Cannot allocate {task_id}.", level="WARNING")
            return False
        hardware.allocated_tasks.append({"task_id": task_id, "agent": agent_requesting,
                                          "timestamp": datetime.datetime.now()})
        self._log(f"Task {task_id} allocated to {hardware_id}.")
        return True

    def update_wishlist_status(self, wishlist_id: str,
                                new_status: Literal["PENDING_FUNDING", "FUNDED", "ACQUIRED", "DECLINED"]):
        for item in self.paid_tier_wishlist:
            if item["id"] == wishlist_id:
                item["status"] = new_status
                self._log(f"Wishlist item '{item['name']}' updated to {new_status}.")
                if new_status == "FUNDED":
                    self._send_to_inbox(
                        wishlist_id,
                        f"Wishlist item '{item['name']}' funded! Initiate procurement.",
                        "APPROVE_PROCUREMENT_OR_ALLOCATE_FUNDS",
                        urgency="HIGH",
                    )
                return
        self._log(f"Wishlist item {wishlist_id} not found.", level="ERROR")

    def review_funding_for_wishlist(self, available_funds: float):
        self._log(f"Reviewing wishlist with available funds: {available_funds}")
        self.paid_tier_wishlist.sort(key=lambda x: x["priority"])
        for item in self.paid_tier_wishlist:
            if item["status"] == "PENDING_FUNDING" and available_funds >= item["cost_estimate"]:
                self._send_to_inbox(
                    item["id"],
                    f"Recommend funding '{item['name']}' (Est. Cost: {item['cost_estimate']}). Available: {available_funds}",
                    "APPROVE_WISHLIST_ITEM_FUNDING",
                    urgency="HIGH",
                )
                return
