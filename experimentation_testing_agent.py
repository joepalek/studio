import datetime
from typing import Dict, Any, List, Literal, Optional

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import Experiment, TestResult, SimulationReport


class ExperimentationTestingAgent:
    """A/B testing, simulation, and stress testing with optional Mirofish integration."""

    def __init__(self, agent_id: str = "Experimentation_001"):
        self.agent_id = agent_id
        self.active_experiments: Dict[str, Experiment] = {}
        self.testing_protocols: Dict[str, Any] = self._load_testing_protocols()
        self.mirofish_enabled: bool = False
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Experimentation Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def _load_testing_protocols(self) -> Dict[str, Any]:
        return {
            "social_media_engagement": {
                "metrics": ["like_rate", "comment_rate", "share_rate", "sentiment_score"],
                "target_increase": 0.10,
            },
            "product_market_fit_simulation": {
                "metrics": ["purchase_intent", "negative_feedback_rate"],
                "target_purchase_intent": 0.70,
            },
            "game_mechanics_stress_test": {
                "metrics": ["bug_rate", "player_frustration_score"],
                "max_frustration": 0.30,
            },
        }

    def enable_mirofish_integration(self):
        self.mirofish_enabled = True
        self._log("Mirofish integration ENABLED.")

    def design_experiment(self, name: str, project_id: str, hypothesis: str,
                          test_type: Literal["A/B", "Simulation", "StressTest"],
                          assets_to_test: List[Dict[str, Any]],
                          target_metrics: List[str]) -> Experiment:
        experiment_id = f"EXP_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_experiment = Experiment(
            id=experiment_id, name=name, project_id=project_id, hypothesis=hypothesis,
            test_type=test_type, assets_to_test=assets_to_test,
            target_metrics=target_metrics, status="DESIGNED",
        )
        self.active_experiments[experiment_id] = new_experiment
        self._log(f"Experiment '{name}' (ID: {experiment_id}) designed for project {project_id}.")
        return new_experiment

    def execute_experiment(self, experiment_id: str):
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            self._log(f"Experiment {experiment_id} not found.", level="ERROR")
            return
        self._log(f"Executing experiment {experiment.name} (Type: {experiment.test_type})")
        experiment.status = "RUNNING"

        if experiment.test_type == "Simulation" and self.mirofish_enabled:
            sim_report = SimulationReport(
                experiment_id=experiment_id,
                metrics_data={"engagement_rate": 0.08, "sentiment_score": 0.75, "viral_potential": 0.85},
                summary="Mirofish simulation predicts high engagement.",
            )
            self._process_simulation_results(experiment_id, sim_report)
        else:
            test_results = TestResult(
                experiment_id=experiment_id,
                metrics_data={"like_rate": 0.12, "comment_rate": 0.03, "share_rate": 0.01},
                analysis="Basic test showed positive engagement.",
            )
            self._process_test_results(experiment_id, test_results)

    def _process_simulation_results(self, experiment_id: str, sim_report: SimulationReport):
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            return
        if sim_report.metrics_data.get("viral_potential", 0) > 0.8:
            self._send_to_inbox(
                experiment_id,
                f"Mirofish simulation for '{experiment.name}' shows HIGH viral potential.",
                "APPROVE_FULL_DEPLOYMENT",
                urgency="HIGH",
            )
        experiment.results = sim_report
        experiment.status = "COMPLETED"
        self._log(f"Experiment {experiment_id} completed (simulation).")

    def _process_test_results(self, experiment_id: str, test_result: TestResult):
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            return
        protocol = self.testing_protocols.get("social_media_engagement", {})
        if test_result.metrics_data.get("like_rate", 0) > protocol.get("target_increase", 0):
            self._send_to_inbox(
                experiment_id,
                f"Test for '{experiment.name}' met engagement targets. Ready for release.",
                "APPROVE_WIDER_RELEASE",
            )
        experiment.results = test_result
        experiment.status = "COMPLETED"
        self._log(f"Experiment {experiment_id} completed (test).")
