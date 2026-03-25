import datetime
from typing import Dict, Any, List, Literal

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import ClientLead, ProjectProposal, QuoteEstimate
from financial_billing_agent import FinancialBillingAgent


class ClientSolutionsAgent:
    """Client lead intake, qualification, proposal generation, and payment securing."""

    def __init__(self, agent_id: str = "Client_Solutions_001"):
        self.agent_id = agent_id
        self.active_leads: Dict[str, ClientLead] = {}
        self.website_status: Dict[str, Any] = {"status": "NOT_BUILT", "url": None}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.financial_agent = FinancialBillingAgent()
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Client Solutions Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def generate_lead_website(self, domain_name: str, services_offered: List[str]):
        self._log(f"Initiating lead generation website creation for domain: {domain_name}")
        if self.website_status["status"] == "NOT_BUILT":
            self.website_status["status"] = "BUILDING"
            self.website_status["url"] = f"https://{domain_name}"
            self.website_status["services"] = services_offered
            self._send_to_inbox(
                "WebsiteBuild",
                f"Lead generation website build initiated for {domain_name}.",
                "REVIEW_WEBSITE_AND_APPROVE_DEPLOYMENT",
            )
        else:
            self._log(f"Website already in status: {self.website_status['status']}")

    def intake_new_lead(self, client_info: Dict[str, Any], initial_inquiry: str) -> str:
        lead_id = f"LEAD_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.active_leads) + 1}"
        new_lead = ClientLead(
            id=lead_id,
            client_info=client_info,
            inquiry=initial_inquiry,
            status="NEW",
            timestamp=datetime.datetime.now(),
        )
        self.active_leads[lead_id] = new_lead
        self._log(f"New lead {lead_id} from {client_info.get('email', 'N/A')}: {initial_inquiry}")
        self.qualify_lead(lead_id)
        return lead_id

    def qualify_lead(self, lead_id: str):
        if lead_id not in self.active_leads:
            self._log(f"Error: Lead {lead_id} not found.", level="ERROR")
            return
        lead = self.active_leads[lead_id]
        if lead.status != "NEW":
            return
        lead.status = "QUALIFIED"
        lead.project_scope = {
            "description": lead.inquiry,
            "estimated_effort_hours": 100,
            "estimated_cost_range": (5000, 15000),
        }
        self._log(f"Lead {lead_id} qualified.")
        self.generate_proposal(lead_id)

    def generate_proposal(self, lead_id: str):
        if lead_id not in self.active_leads or self.active_leads[lead_id].status != "QUALIFIED":
            self._log(f"Error: Lead {lead_id} not qualified.", level="ERROR")
            return
        lead = self.active_leads[lead_id]
        proposal_id = f"PROP_{lead_id}"
        new_proposal = ProjectProposal(
            id=proposal_id,
            lead_id=lead_id,
            title=f"Proposal for {lead.client_info.get('name', 'Client')}'s Inquiry",
            scope=lead.project_scope,
            quote=QuoteEstimate(
                amount=lead.project_scope["estimated_cost_range"][0],
                currency="USD",
                type="ESTIMATE",
            ),
            status="DRAFT",
        )
        lead.proposal = new_proposal
        lead.status = "PROPOSAL_REVIEW"
        self._send_to_inbox(
            lead_id,
            f"Draft proposal {proposal_id} for lead {lead_id} ready for supervisor review.",
            "REVIEW_PROPOSAL_AND_APPROVE_FOR_CLIENT",
        )

    def present_proposal_and_secure_payment(self, lead_id: str, final_quote_amount: float,
                                             requires_downpayment: bool = True):
        if lead_id not in self.active_leads or self.active_leads[lead_id].status != "PROPOSAL_REVIEW":
            self._log(f"Error: Lead {lead_id} not in proposal review stage.", level="ERROR")
            return
        lead = self.active_leads[lead_id]
        lead.proposal.quote.amount = final_quote_amount
        lead.proposal.status = "PRESENTED_TO_CLIENT"
        downpayment_amount = final_quote_amount * 0.3 if requires_downpayment else final_quote_amount
        invoice = self.financial_agent.generate_invoice(
            client_id=lead.client_info.get("id", lead_id),
            project_id=lead.id,
            items=[{"description": lead.proposal.title, "amount": final_quote_amount}],
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            total_amount=downpayment_amount,
            payment_terms="Downpayment" if requires_downpayment else "Full Payment",
        )
        lead.status = "AWAITING_PAYMENT_CONFIRMATION"
        self._log(f"Lead {lead_id} awaiting payment for invoice {invoice.id}.")

    def notify_payment_secured(self, project_id: str, amount: float):
        for lead_id, lead in self.active_leads.items():
            if lead.id == project_id and lead.status == "AWAITING_PAYMENT_CONFIRMATION":
                lead.status = "PAYMENT_SECURED"
                self._send_to_inbox(
                    lead_id,
                    f"Payment secured for project {project_id} (${amount}). Ready for commencement.",
                    "APPROVE_PROJECT_COMMENCEMENT",
                    urgency="HIGH",
                )
                return
        self._log(f"Payment secured for unknown project {project_id}.", level="WARNING")
