# studio_core/data_models.py
# Shared data models for the Synthetic Talent Agency / AI Entertainment Studio
# All agents import from this file

from dataclasses import dataclass, field
import datetime
from typing import Dict, Any, List, Literal, Optional

# --- Generic Studio Core ---

@dataclass
class StudioAsset:
    id: str
    type: Literal[
        "GENERATED_CONTENT", "VR_ENVIRONMENT", "VR_CHARACTER", "AI_BAND_TRACK",
        "MUSIC_VIDEO", "SOCIAL_MEDIA_POST", "RESUME", "PROPOSAL", "WEBSITE",
        "RAW_DATA", "CLEANED_DATA", "VOICE_MODEL", "HARDWARE", "SOFTWARE_LICENSE",
        "LEGAL_DOCUMENT", "FINANCIAL_REPORT", "OTHER"
    ]
    status: Literal[
        "NEW", "RAW", "IN_PROCESSING", "CLEANED", "TRAINED", "DRAFT",
        "READY_FOR_QA", "IN_QA", "APPROVED", "REJECTED", "DORMANT",
        "UNDER_RE_EVALUATION", "MASTERED_FOR_TESTING", "IN_A&R_TESTING",
        "PLANNED", "DEPLOYED", "ARCHIVED", "COMPLETED"
    ]
    path: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Idea:
    id: str
    title: str
    description: str
    source: str
    rating: int  # 1-10
    status: Literal[
        "NEW", "PENDING_FEASIBILITY_REVIEW", "FEASIBILITY_STUDY", "APPROVED",
        "ARCHIVED", "RE_EVALUATED_ACTIVE", "UNDER_RE_EVALUATION_ARCHIVE"
    ]
    feasibility_score: float = 0.0
    last_re_evaluated_date: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class WhiteboardEntry(StudioAsset):
    content_id: str = ""

# --- Financial ---

@dataclass
class Invoice:
    id: str
    client_id: str
    project_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    due_date: datetime.date
    status: Literal["PENDING", "PARTIALLY_PAID", "PAID", "OVERDUE", "PENDING_ESCROW_RELEASE"]
    payment_terms: str
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class PaymentTransaction:
    id: str
    invoice_id: str
    amount: float
    method: str
    reference: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    is_escrow: bool = False
    escrow_status: Literal["PENDING", "RELEASED", "CANCELLED"] = "PENDING"

@dataclass
class FinancialSummary:
    total_invoices_outstanding: int
    total_revenue_ytd: float
    current_cash_flow: float
    legal_retainer_balance: float
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

# --- Legal ---

@dataclass
class LegalQuery:
    id: str
    topic: str
    context: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class LegalReport:
    query_id: str
    summary: str
    risks: List[str]
    recommendations: List[str]
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class ComplianceCheckResult:
    passed: bool
    issues: List[str]
    report_details: Dict[str, Any] = field(default_factory=dict)

# --- Client Solutions ---

@dataclass
class ClientLead:
    id: str
    client_info: Dict[str, Any]
    inquiry: str
    status: Literal[
        "NEW", "QUALIFIED", "PROPOSAL_REVIEW", "PROPOSAL_APPROVED",
        "PRESENTED_TO_CLIENT", "AWAITING_PAYMENT_CONFIRMATION", "PAYMENT_SECURED", "REJECTED"
    ]
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    project_scope: Optional[Dict[str, Any]] = None
    proposal: Optional[Any] = None

@dataclass
class ProjectProposal:
    id: str
    lead_id: str
    title: str
    scope: Dict[str, Any]
    quote: Any
    status: Literal["DRAFT", "PENDING_REVIEW", "PRESENTED_TO_CLIENT", "ACCEPTED", "REJECTED"]
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class QuoteEstimate:
    amount: float
    currency: str
    type: Literal["ESTIMATE", "FINAL_QUOTE"]
    details: Dict[str, Any] = field(default_factory=dict)

# --- QA ---

@dataclass
class ContentAsset:
    id: str
    content: Any
    type: Literal["text", "image", "video", "audio", "code", "json"]
    project_type: Literal["social_media", "resume", "book", "explicit", "vr_dialogue", "music_lyrics", "other"]
    reference_data: Optional[Any] = None
    character_context: Optional[Dict[str, Any]] = None

@dataclass
class QAReport:
    asset_id: str
    passed: bool
    issues: List[str]
    compliance_issues: List[str]
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

# --- Resource Management ---

@dataclass
class Subscription:
    id: str
    service: str
    tier: str
    status: Literal["ACTIVE", "INACTIVE", "PENDING_RENEWAL", "EXPIRED", "CAPPED"]
    cost_monthly: float
    usage_limit: str
    start_date: datetime.date = field(default_factory=datetime.date.today)
    end_date: Optional[datetime.date] = None

@dataclass
class HardwareAsset:
    id: str
    name: str
    type: Literal["GPU", "CPU", "STORAGE", "NETWORK_ADAPTER", "SERVER"]
    status: Literal["EXISTING", "ACQUIRED", "PENDING_PROCUREMENT", "OVERLOADED", "OFFLINE", "ACTIVE"]
    capacity: str
    availability: Literal["LOCAL_EXTERNAL", "CLOUD_INSTANCE", "LOCAL_INTEGRATED"]
    allocated_tasks: List[Dict[str, Any]] = field(default_factory=list)
    acquired_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class ResourceUsageReport:
    resource_id: str
    usage_data: Dict[str, Any]
    cost_data: Dict[str, Any]
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class FundingAlert:
    id: str
    message: str
    amount: float
    urgency: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

# --- Experimentation ---

@dataclass
class Experiment:
    id: str
    name: str
    project_id: str
    hypothesis: str
    test_type: Literal["A/B", "Simulation", "StressTest"]
    assets_to_test: List[Dict[str, Any]]
    target_metrics: List[str]
    status: Literal["DESIGNED", "RUNNING", "COMPLETED", "CANCELLED"]
    results: Optional[Any] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class TestResult:
    experiment_id: str
    metrics_data: Dict[str, Any]
    analysis: str
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class SimulationReport:
    experiment_id: str
    metrics_data: Dict[str, Any]
    summary: str
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

# --- Market Intelligence ---

@dataclass
class MarketReport:
    id: str
    trends: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class ProductIdea:
    id: str
    title: str
    description: str
    source: str
    rating: int
    status: Literal[
        "NEW", "PENDING_FEASIBILITY_REVIEW", "FEASIBILITY_STUDY", "APPROVED",
        "ARCHIVED", "RE_EVALUATED_ACTIVE", "UNDER_RE_EVALUATION_ARCHIVE"
    ]
    feasibility_score: float = 0.0
    last_re_evaluated_date: datetime.datetime = field(default_factory=datetime.datetime.now)

# --- AI Music Label ---

@dataclass
class AudioAsset(StudioAsset):
    band_id: Optional[str] = None
    title: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None

@dataclass
class BandStyleCard:
    id: str
    name: str
    aesthetic: str
    vocal_dna_source_audio_path: Optional[str] = None
    vocal_dna_model_id: Optional[str] = None
    musical_signature: Optional[str] = None
    behavioral_marker: Optional[str] = None

@dataclass
class VoiceModel:
    id: str
    band_id: str
    source_audio_path: str
    status: Literal["TRAINING", "TRAINED", "FAILED"]
    model_path: str

@dataclass
class TrackGenerationRequest:
    id: str
    band_id: str
    title: str
    genre: str
    mood: str
    lyrics: Optional[str] = None
    melody_reference_path: Optional[str] = None
    adjustments: Optional[Dict[str, str]] = None

@dataclass
class MusicRelease:
    id: str
    band_id: str
    tracks: List[str]
    release_type: Literal["SINGLE", "ALBUM"]
    target_date: datetime.date
    status: Literal["PLANNED", "APPROVED_FOR_MARKETING", "MARKETING_ACTIVE", "RELEASED", "CANCELLED"]
    marketing_campaign_id: Optional[str] = None

@dataclass
class MarketingCampaign:
    id: str
    release_id: str
    strategy: str
    status: Literal["DRAFT", "ACTIVE", "COMPLETED", "PAUSED"]
    platforms: List[str]
    budget: float = 0.0

@dataclass
class CharacterAvatar:
    id: str
    character_name: str
    model_path: str
    behavioral_profile: str
    texture_path: Optional[str] = None
    animation_data_path: Optional[str] = None

@dataclass
class MusicVideo(StudioAsset):
    audio_asset_id: str = ""
    band_id: str = ""
    visual_style_prompt: str = ""
    character_avatars: List[str] = field(default_factory=list)

@dataclass
class VirtualGigOffer:
    id: str
    band_id: str
    venue_name: str
    offer_details: Dict[str, Any]
    status: Literal["OFFERED", "ACCEPTED", "DECLINED", "COMPLETED"]
    negotiation_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class MiroFishReport:
    track_id: str
    metrics_data: Dict[str, float]
    summary: str
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

# --- VR / Immersive Worlds ---

@dataclass
class VRCharacter(StudioAsset):
    name: str = ""
    birth_date: datetime.date = field(default_factory=datetime.date.today)
    persona_traits: Dict[str, float] = field(default_factory=dict)
    backstory: Optional[str] = None
    current_world_id: Optional[str] = None
    current_state: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VRWorldAsset(StudioAsset):
    name: str = ""
    description: str = ""
    artist_info: Dict[str, Optional[str]] = field(default_factory=dict)
    technical_compliance: Dict[str, Any] = field(default_factory=dict)
    theme: Optional[str] = None
    mood: Optional[str] = None
    architectural_style: Optional[str] = None

@dataclass
class VRInteractionEvent:
    id: str
    character_id: str
    world_id: str
    event_type: Literal["ACTION", "OBSERVATION", "CRITICAL_EVENT", "DIALOGUE"]
    details: Dict[str, Any]
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class BehaviorTree:
    id: str
    definition: Dict[str, Any]
    status: Literal["ACTIVE", "INACTIVE", "DRAFT"]
    version: str = "1.0"

@dataclass
class SpatialAnchor:
    id: str
    world_id: str
    coordinates: Dict[str, float]
    associated_asset_id: Optional[str] = None
    status: Literal["ACTIVE", "INACTIVE", "ERROR"] = "ACTIVE"

@dataclass
class MemoryWeighting:
    type: str
    decay_rate: float
    emotional_boost: float

@dataclass
class ArtistSubmission:
    id: str
    artist_name: str
    portfolio_link: str
    world_name: str
    world_description: str
    world_file_path: str
    world_file_metadata: Dict[str, Any]
    submission_date: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class TechnicalRequirementsDoc:
    id: str
    requirements: Dict[str, Any]
    version: str

@dataclass
class VRDeploymentPackage:
    id: str
    project_id: str
    world_assets: List[str]
    character_assets: List[str]
    target_platforms: List[str]
    package_path: str
    deployment_manifests: Dict[str, Any]
    status: Literal[
        "PREPARED", "READY_FOR_APPROVAL", "APPROVED", "DEPLOYING",
        "DEPLOYED", "PARTIALLY_DEPLOYED", "FAILED"
    ]
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class PlatformIntegrationConfig:
    id: str
    platform: str
    status: Literal["ACTIVE", "INACTIVE", "UNDER_MAINTENANCE"]
    deployment_type: Literal["APP_PACKAGE", "EXECUTABLE", "WEB_HOSTED", "DEVELOPMENT_KIT"]
    requirements: Dict[str, Any]

# --- AI Orchestration ---

@dataclass
class AgentTask:
    id: str
    agent_id: str
    description: str
    status: Literal[
        "QUEUED", "RUNNING", "COMPLETED", "FAILED",
        "BLOCKED_RESOURCE", "PENDING_INBOX_RESOLUTION"
    ]
    priority: int  # 1-10
    resources_required: List[str]
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    blocker_info: Optional[str] = None
