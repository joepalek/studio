"""
Studio Agent System — Startup Health Check
Imports and instantiates all 15 domain agents + core infrastructure.
Does NOT run any tasks — confirms clean boot only.
"""
import sys
import traceback

results = []

def try_import(label, fn):
    try:
        agent = fn()
        results.append((label, "OK", None))
        return agent
    except Exception as e:
        results.append((label, "FAIL", traceback.format_exc()))
        return None


print("=" * 60)
print("STUDIO AGENT SYSTEM — STARTUP HEALTH CHECK")
print("=" * 60)

# --- Core infrastructure ---
try:
    from studio_core.logger import Logger
    from studio_core.agent_inbox import AgentInbox
    from studio_core.ai_orchestrator import AIOrchestrator
    from studio_core.data_models import AgentTask
    core_logger = Logger("Studio_Main", log_to_file=False)
    core_inbox = AgentInbox()
    core_orchestrator = AIOrchestrator(core_logger)
    results.append(("studio_core [Logger, AgentInbox, AIOrchestrator]", "OK", None))
except Exception:
    results.append(("studio_core", "FAIL", traceback.format_exc()))

# --- Domain agents (in dependency order) ---
from financial_billing_agent import FinancialBillingAgent
from internal_asset_flow_agent import InternalAssetIdeaFlowAgent
from ar_marketing_agent import ARMarketingAgent
from client_solutions_agent import ClientSolutionsAgent
from content_qa_agent import ContentQAAgent
from ctw_client_manager_agent import CTWClientManagerAgent
from experimentation_testing_agent import ExperimentationTestingAgent
from legal_advisory_agent import LegalComplianceAdvisoryAgent
from market_intel_agent import MarketIntelligenceOpportunityAgent
from music_production_agent import MusicProductionAgent
from resource_mgmt_agent import ResourceSubscriptionManagementAgent
from virtual_performance_agent import VirtualPerformanceAgent
from vr_behavior_engine_agent import VRBehaviorEngineAgent
from vr_memory_weigher_agent import VRMemoryWeigherAgent
from vr_platform_integration_agent import VRPlatformIntegrationAgent
from vr_scene_generator_agent import VRSceneGeneratorAgent

agents = [
    ("FinancialBillingAgent",                try_import("FinancialBillingAgent",                FinancialBillingAgent)),
    ("InternalAssetIdeaFlowAgent",           try_import("InternalAssetIdeaFlowAgent",           InternalAssetIdeaFlowAgent)),
    ("ARMarketingAgent",                     try_import("ARMarketingAgent",                     ARMarketingAgent)),
    ("ClientSolutionsAgent",                 try_import("ClientSolutionsAgent",                 ClientSolutionsAgent)),
    ("ContentQAAgent",                       try_import("ContentQAAgent",                       ContentQAAgent)),
    ("CTWClientManagerAgent",                try_import("CTWClientManagerAgent",                CTWClientManagerAgent)),
    ("ExperimentationTestingAgent",          try_import("ExperimentationTestingAgent",          ExperimentationTestingAgent)),
    ("LegalComplianceAdvisoryAgent",         try_import("LegalComplianceAdvisoryAgent",         LegalComplianceAdvisoryAgent)),
    ("MarketIntelligenceOpportunityAgent",   try_import("MarketIntelligenceOpportunityAgent",   MarketIntelligenceOpportunityAgent)),
    ("MusicProductionAgent",                 try_import("MusicProductionAgent",                 MusicProductionAgent)),
    ("ResourceSubscriptionManagementAgent",  try_import("ResourceSubscriptionManagementAgent",  ResourceSubscriptionManagementAgent)),
    ("VirtualPerformanceAgent",              try_import("VirtualPerformanceAgent",              VirtualPerformanceAgent)),
    ("VRBehaviorEngineAgent",                try_import("VRBehaviorEngineAgent",                VRBehaviorEngineAgent)),
    ("VRMemoryWeigherAgent",                 try_import("VRMemoryWeigherAgent",                 VRMemoryWeigherAgent)),
    ("VRPlatformIntegrationAgent",           try_import("VRPlatformIntegrationAgent",           VRPlatformIntegrationAgent)),
    ("VRSceneGeneratorAgent",                try_import("VRSceneGeneratorAgent",                VRSceneGeneratorAgent)),
]

print()
print("AGENT STATUS")
print("-" * 60)
ok_count = 0
fail_count = 0
for label, status, tb in results:
    icon = "[OK]" if status == "OK" else "[!!]"
    print(f"  {icon}  {label}: {status}")
    if status == "OK":
        ok_count += 1
    else:
        fail_count += 1
        if tb:
            for line in tb.strip().splitlines()[-3:]:
                print(f"       {line}")

print()
print("-" * 60)
print(f"  {ok_count} OK  |  {fail_count} FAILED")
print("=" * 60)

if fail_count > 0:
    sys.exit(1)
