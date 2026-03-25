import datetime
from typing import Dict, Any, List, Literal

from studio_core.ai_orchestrator import AIOrchestrator, MockClaudeCodeSession, MockGeminiFlash, MockOllamaLocal
from studio_core.agent_inbox import AgentInbox
from studio_core.logger import Logger
from studio_core.data_models import Invoice, PaymentTransaction, FinancialSummary


class FinancialBillingAgent:
    """Invoice generation, payment processing, escrow handling, legal retainer tracking."""

    def __init__(self, agent_id: str = "Financial_Billing_001"):
        self.agent_id = agent_id
        self.invoices: Dict[str, Invoice] = {}
        self.transactions: List[PaymentTransaction] = []
        self.current_cash_flow: float = 0.0
        self.legal_retainer_fund: Dict[str, Any] = {"current_balance": 0.0, "target_minimum": 10000.0}
        self.inbox = AgentInbox()
        self.logger = Logger(agent_id)
        self.orchestrator = AIOrchestrator(self.logger)
        self.logger.log(f"{self.agent_id} initialized.", level="INFO")

    def _log(self, message: str, level: str = "INFO"):
        self.logger.log(message, level)

    def _send_to_inbox(self, entity_id: str, issue_summary: str, required_action: str, urgency: str = "MEDIUM"):
        self._log(f"Financial Alert for {entity_id}: {issue_summary}", level="WARNING")
        self.inbox.add_item(
            agent_id=self.agent_id,
            project_id=entity_id,
            question=issue_summary,
            required_action=required_action,
            urgency=urgency,
        )

    def generate_invoice(self, client_id: str, project_id: str, items: List[Dict[str, Any]],
                         due_date: datetime.date, total_amount: float,
                         payment_terms: str = "Net 30") -> Invoice:
        invoice_id = f"INV_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.invoices) + 1}"
        new_invoice = Invoice(
            id=invoice_id, client_id=client_id, project_id=project_id,
            items=items, total_amount=total_amount, due_date=due_date,
            status="PENDING", payment_terms=payment_terms,
        )
        self.invoices[invoice_id] = new_invoice
        self._log(f"Invoice {invoice_id} generated for client {client_id}, total: {total_amount}")
        return new_invoice

    def process_payment(self, invoice_id: str, amount_received: float, payment_method: str,
                        transaction_ref: str, is_escrow: bool = False,
                        escrow_status: Literal["PENDING", "RELEASED"] = "PENDING"):
        if invoice_id not in self.invoices:
            self._log(f"Error: Invoice {invoice_id} not found.", level="ERROR")
            return
        invoice = self.invoices[invoice_id]
        txn_id = f"TXN_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.transactions) + 1}"
        new_txn = PaymentTransaction(
            id=txn_id, invoice_id=invoice_id, amount=amount_received,
            method=payment_method, reference=transaction_ref,
            is_escrow=is_escrow, escrow_status=escrow_status,
        )
        self.transactions.append(new_txn)
        if is_escrow and escrow_status == "RELEASED":
            self.current_cash_flow += amount_received
            invoice.status = "PAID" if amount_received >= invoice.total_amount else "PARTIALLY_PAID"
        elif is_escrow:
            invoice.status = "PENDING_ESCROW_RELEASE"
            self._send_to_inbox(invoice_id, f"Payment ${amount_received} in pending escrow.", "MONITOR_ESCROW_RELEASE", urgency="HIGH")
        else:
            self.current_cash_flow += amount_received
            invoice.status = "PAID" if amount_received >= invoice.total_amount else "PARTIALLY_PAID"
            self._send_to_inbox(invoice_id, f"Payment ${amount_received} secured.", "CONFIRM_PROJECT_COMMENCEMENT", urgency="HIGH")

    def track_overdue_invoices(self):
        now = datetime.date.today()
        for invoice_id, invoice in self.invoices.items():
            if invoice.status in ["PENDING", "PARTIALLY_PAID"] and invoice.due_date < now:
                self._send_to_inbox(invoice_id, f"Invoice {invoice_id} overdue since {invoice.due_date}.",
                                    "INITIATE_COLLECTIONS_PROCESS", urgency="HIGH")

    def get_financial_summary(self) -> FinancialSummary:
        return FinancialSummary(
            total_invoices_outstanding=sum(1 for inv in self.invoices.values() if inv.status == "PENDING"),
            total_revenue_ytd=sum(t.amount for t in self.transactions if t.timestamp.year == datetime.datetime.now().year),
            current_cash_flow=self.current_cash_flow,
            legal_retainer_balance=self.legal_retainer_fund["current_balance"],
        )
