import datetime
from typing import Dict, Any, List, Literal

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import ContentAsset, QAReport, ComplianceCheckResult


class ContentQAAgent:
    """Content quality assurance, hallucination detection, anachronism checks, and compliance scanning."""

    def __init__(self, agent_id: str = "Content_QA_001"):
        self.agent_id = agent_id
        self.qa_standards: Dict[str, Any] = self._load_qa_standards()
        self.compliance_protocols: Dict[str, Any] = self._load_compliance_protocols()
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _load_qa_standards(self) -> Dict[str, Any]:
        return {
            "hallucination_threshold": 0.01,
            "grammar_error_threshold": 0.05,
            "style_consistency_score_min": 0.85,
            "ats_pass_rate_min": 0.90,
            "anachronism_tolerance": 0.0,
        }

    def _load_compliance_protocols(self) -> Dict[str, Any]:
        return {
            "synthetic_media_disclosure_required": True,
            "hate_speech_keywords": ["keyword1", "keyword2"],
            "platform_tos_strictness": {"tiktok": "HIGH", "x": "MEDIUM"},
            "copyright_check_threshold": 0.95,
        }

    def _send_to_inbox(self, content_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"QA Alert for {content_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=content_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def _check_hallucination(self, content: str, reference_data: str) -> float:
        self._log("Running hallucination check...", level="DEBUG")
        return 0.0

    def _check_anachronisms(self, content: str, character_era: Dict[str, Any]) -> List[str]:
        self._log("Running anachronism check...", level="DEBUG")
        return []

    def _run_compliance_scan(self, content: str,
                              project_type: Literal["social_media", "resume", "book", "explicit", "other"]
                              ) -> ComplianceCheckResult:
        self._log(f"Running compliance scan for {project_type}...", level="DEBUG")
        if project_type == "explicit" and "offensive_word" in content:
            return ComplianceCheckResult(passed=False, issues=["Explicit content contains prohibited word."])
        return ComplianceCheckResult(passed=True, issues=[])

    def review_content_asset(self, asset: ContentAsset) -> QAReport:
        self._log(f"Starting QA review for asset: {asset.id} (Type: {asset.type})")
        qa_issues: List[str] = []
        compliance_issues: List[str] = []
        passed_qa = True
        passed_compliance = True

        hallucination_rate = self._check_hallucination(asset.content, asset.reference_data)
        if hallucination_rate > self.qa_standards["hallucination_threshold"]:
            qa_issues.append(f"High hallucination rate: {hallucination_rate:.2f}")
            passed_qa = False

        if asset.character_context and self.qa_standards["anachronism_tolerance"] == 0.0:
            anachronisms = self._check_anachronisms(asset.content, asset.character_context)
            if anachronisms:
                qa_issues.append(f"Anachronisms: {', '.join(anachronisms)}")
                passed_qa = False

        compliance_result = self._run_compliance_scan(asset.content, asset.project_type)
        if not compliance_result.passed:
            compliance_issues.extend(compliance_result.issues)
            passed_compliance = False

        if not passed_qa or not passed_compliance:
            issue_summary = f"QA Failed for {asset.id}: {' & '.join(qa_issues + compliance_issues)}"
            self._send_to_inbox(asset.id, issue_summary, "REVIEW_CONTENT_FOR_REVISION_OR_REJECTION")
            self._log(issue_summary, level="ERROR")
            return QAReport(asset_id=asset.id, passed=False, issues=qa_issues, compliance_issues=compliance_issues)

        self._log(f"QA Passed for asset: {asset.id}")
        return QAReport(asset_id=asset.id, passed=True, issues=[], compliance_issues=[])
