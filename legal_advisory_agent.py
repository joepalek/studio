import datetime
from typing import Dict, Any, List

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import LegalQuery, LegalReport, ComplianceCheckResult


class LegalComplianceAdvisoryAgent:
    """Legal research, compliance risk assessment, and retainer fund tracking."""

    def __init__(self, agent_id: str = "Legal_Advisory_001"):
        self.agent_id = agent_id
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.current_laws: Dict[str, Any] = self._load_current_legal_landscape()
        self.platform_policies: Dict[str, Any] = self._load_platform_policies()
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _load_current_legal_landscape(self) -> Dict[str, Any]:
        self._log("Loading current legal landscape...", level="DEBUG")
        return {
            "synthetic_media_disclosure_laws": {
                "US_CA_SB11": {"active": True, "details": "Requires disclosure for synthetic political/explicit media."}
            },
            "data_privacy_laws": {
                "GDPR": {"active": True, "details": "EU data privacy."},
                "CCPA": {"active": True, "details": "California data privacy."},
            },
            "copyright_fair_use_guidelines": {
                "US_Fair_Use": {"active": True, "details": "Educational, parody, criticism."}
            },
            "ai_generated_content_ownership": {"status": "UNCLEAR", "details": "Evolving legal landscape."},
        }

    def _load_platform_policies(self) -> Dict[str, Any]:
        self._log("Loading platform policies...", level="DEBUG")
        return {
            "Meta": {"adult_content": "PROHIBITED", "synthetic_media_disclosure": "REQUIRED"},
            "TikTok": {"adult_content": "PROHIBITED", "synthetic_media_disclosure": "REQUIRED_FOR_REALISTIC_AI"},
            "Fanvue": {"adult_content": "PERMITTED_WITH_AGE_GATING", "synthetic_media_disclosure": "REQUIRED"},
        }

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Legal Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def research_law_or_policy(self, query: LegalQuery) -> LegalReport:
        self._log(f"Researching legal query: {query.topic} for {query.context}")
        if query.topic == "synthetic_media_disclosure" and query.context == "California":
            return LegalReport(
                query_id=query.id,
                summary="California SB 11 requires disclosure for synthetic media in political/explicit contexts.",
                risks=["Failure to disclose can lead to fines or platform bans."],
                recommendations=["Ensure all AI-generated content meets disclosure guidelines."],
            )
        elif query.topic == "copyright" and "old band music" in query.context:
            return LegalReport(
                query_id=query.id,
                summary="Remastering old band music requires acquiring master and publishing rights.",
                risks=["Infringement lawsuits if rights not properly secured."],
                recommendations=["Verify all contracts. Consult specialized IP lawyer for digital replica rights."],
            )
        return LegalReport(
            query_id=query.id,
            summary=f"No specific match for '{query.topic}' in '{query.context}'. Further analysis needed.",
            risks=[],
            recommendations=[],
        )

    def assess_project_risk(self, project_name: str, project_scope: Dict[str, Any]) -> LegalReport:
        self._log(f"Assessing legal risk for project: {project_name}")
        risks = []
        recommendations = []
        if "AI-Generated 3D Explicit Content" in project_name:
            risks += ["High platform restriction and legal scrutiny.", "Evolving synthetic media laws."]
            recommendations += ["Strict disclosure protocol via Content QA Agent.", "Dedicated legal retainer funding."]
            self._send_to_inbox(
                project_name,
                f"High-risk project '{project_name}' requires careful legal strategy.",
                "APPROVE_LEGAL_STRATEGY_AND_FUND_RETAINER",
            )
        if "data_acquisition" in project_scope.get("activities", []):
            risks.append("GDPR/CCPA compliance for user data.")
            recommendations.append("Implement robust data anonymization and consent mechanisms.")
        if not risks:
            risks.append("No immediate high-level legal risks detected.")
            recommendations.append("Continue monitoring with Content QA Agent.")
        return LegalReport(
            query_id=f"risk_assessment_{project_name}",
            summary=f"Legal Risk Assessment for {project_name}",
            risks=risks,
            recommendations=recommendations,
        )

    def track_legal_retainer_fund(self, fund_status: Dict[str, Any]):
        self._log(f"Tracking legal retainer fund. Balance: {fund_status.get('current_balance', 0)}")
        if fund_status.get("current_balance", 0) < fund_status.get("target_minimum", 0):
            self._send_to_inbox(
                "LegalRetainer",
                f"Legal retainer fund below target: {fund_status.get('current_balance', 0)} / {fund_status.get('target_minimum', 0)}",
                "REVIEW_RETAINER_FUNDING_STRATEGY",
            )
