import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import ClientLead, ProjectProposal, QuoteEstimate
from financial_billing_agent import FinancialBillingAgent


class CTWClientManagerAgent:
    """CTW project lifecycle manager with inbox-driven supervisor approval gates."""

    def __init__(self, agent_id: str = "CTW_Client_Manager_001"):
        self.agent_id = agent_id
        self.active_projects: Dict[str, Any] = {}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, project_id: str, question: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"CTW Alert for {project_id}: {question}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=project_id,
            question=question,
            required_action=required_action,
            urgency=urgency,
        )
        self.active_projects[project_id]["status"] = "PAUSED_FOR_REVIEW"

    def _check_inbox_for_resolution(self, project_id: str) -> Optional[Dict[str, Any]]:
        resolved_item = self.inbox.get_resolved_item(agent_id=self.agent_id, project_id=project_id)
        if resolved_item:
            self._log(f"Project {project_id}: Inbox item resolved.")
            return resolved_item
        return None

    def onboard_new_client_project(self, client_data: Dict[str, Any], project_brief: Dict[str, Any]) -> str:
        project_id = f"CTW_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.active_projects) + 1}"
        self.active_projects[project_id] = {
            "client_data": client_data,
            "brief": project_brief,
            "status": "CLIENT_ONBOARDED",
            "current_stage": "INITIATION",
            "history": [{"timestamp": datetime.datetime.now(), "event": "Project Initiated"}],
        }
        self._log(f"New CTW project '{project_id}' onboarded for client: {client_data.get('name', 'N/A')}")
        self._send_to_inbox(
            project_id,
            f"New client project '{project_id}' brief requires initial supervisor review.",
            "APPROVE_BRIEF_AND_START_PROJECT",
        )
        return project_id

    def drive_project_forward(self, project_id: str):
        if project_id not in self.active_projects:
            self._log(f"Error: Project {project_id} not found.", level="ERROR")
            return
        project = self.active_projects[project_id]
        self._log(f"Driving project {project_id}. Status: {project['status']}, Stage: {project['current_stage']}")

        if project["status"] == "PAUSED_FOR_REVIEW":
            resolved_item = self._check_inbox_for_resolution(project_id)
            if resolved_item:
                project["status"] = "RESUMING_AUTOMATION"
                project["history"].append({"timestamp": datetime.datetime.now(),
                                           "event": f"Resumed: {resolved_item['question']}"})
                self.process_inbox_resolution(project_id, resolved_item)
            else:
                self._log(f"Project {project_id} still PAUSED_FOR_REVIEW.", level="DEBUG")
            return

        if project["status"] in ["CLIENT_ONBOARDED", "RESUMING_AUTOMATION", "IN_PROGRESS"]:
            if project["current_stage"] == "INITIATION":
                project["current_stage"] = "CONTENT_GENERATION"
                project["status"] = "IN_PROGRESS"
                self._send_to_inbox(project_id,
                                    f"Content generation for '{project_id}' complete. Needs review.",
                                    "REVIEW_CONTENT_AND_APPROVE")
            elif project["current_stage"] == "CONTENT_GENERATION":
                project["current_stage"] = "QA_REVIEW"
                project["status"] = "IN_PROGRESS"
                self._send_to_inbox(project_id,
                                    f"QA for '{project_id}' complete. Needs supervisor approval.",
                                    "APPROVE_QA_AND_PREPARE_DELIVERY")
            elif project["current_stage"] == "QA_REVIEW":
                project["current_stage"] = "DELIVERY_PREPARATION"
                project["status"] = "IN_PROGRESS"
                self._send_to_inbox(project_id,
                                    f"Project '{project_id}' ready for final delivery.",
                                    "CONFIRM_DELIVERY_AND_FINALIZE")
            elif project["current_stage"] == "DELIVERY_PREPARATION":
                project["current_stage"] = "COMPLETED"
                project["status"] = "COMPLETED"
                project["history"].append({"timestamp": datetime.datetime.now(), "event": "Project Completed"})
                self._log(f"CTW Project {project_id} successfully completed.", level="INFO")

    def process_inbox_resolution(self, project_id: str, resolved_item: Dict[str, Any]):
        resolution = resolved_item.get("resolution_data")
        question = resolved_item.get("question", "")
        self._log(f"Project {project_id}: Processing resolution for '{question}': {resolution}")
        if "initial supervisor review" in question:
            self.active_projects[project_id]["status"] = "IN_PROGRESS"
            self.active_projects[project_id]["current_stage"] = "INITIATION"
        elif "Content generation" in question:
            self.active_projects[project_id]["status"] = "IN_PROGRESS"
            self.active_projects[project_id]["current_stage"] = "CONTENT_GENERATION"
        elif "QA for" in question:
            self.active_projects[project_id]["status"] = "IN_PROGRESS"
            self.active_projects[project_id]["current_stage"] = "QA_REVIEW"
        elif "ready for final delivery" in question:
            self.active_projects[project_id]["status"] = "IN_PROGRESS"
            self.active_projects[project_id]["current_stage"] = "DELIVERY_PREPARATION"
        self.drive_project_forward(project_id)
