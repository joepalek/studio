#!/usr/bin/env python3
"""
CX Agent - Asset Quality Gate & Distribution Router
Master implementation for asset validation, routing, usage tracking, and social media intelligence

Usage:
  python cx_agent.py --mode daily_scan
  python cx_agent.py --mode validate --asset_id ebay_listing_20260329_001
  python cx_agent.py --mode monitor --hours 24
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple
import hashlib
import logging

sys.path.insert(0, 'G:/My Drive/Projects/_studio')
from studio_core.agent_inbox import AgentInbox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [CX_AGENT] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/cx_agent.log', encoding='utf-8', errors='replace'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "manifest_path": "asset_distribution_manifest.json",
    "log_path": "data/asset_creation_log.json",
    "staging_folder": "data/asset_staging/",
    "quality_threshold_pass": 8,
    "quality_threshold_review": 5,
    "retry_max": 1,
    "retry_delay_seconds": 3600,
    "job_cull_schedule": "02:00",
    "monitoring_interval_seconds": 3600,
}

def get_utc_now() -> str:
    """Get current UTC time in ISO format with timezone"""
    return datetime.now(timezone.utc).isoformat()

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class Asset:
    """Represents a created asset"""
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.asset_id = data.get("asset_id")
        self.creator_agent = data.get("creator_agent")
        self.asset_type = data.get("asset_type")
        self.created_at = data.get("created_at")
        self.project = data.get("project")
        self.content = data.get("content", {})
        self.metadata = data.get("metadata", {})

class ValidationResult:
    """Validation result for an asset"""
    def __init__(self, format_pass: bool, quality_score: int, brand_alignment: bool):
        self.format_pass = format_pass
        self.quality_score = quality_score
        self.brand_alignment = brand_alignment
        self.overall_status = self._compute_status()
        self.timestamp = get_utc_now()
    
    def _compute_status(self) -> str:
        if not self.format_pass:
            return "format_fail"
        if self.quality_score >= 8 and self.brand_alignment:
            return "pass"
        elif self.quality_score >= 5:
            return "review"
        else:
            return "reject"

# ============================================================================
# VALIDATION LOGIC
# ============================================================================

class AssetValidator:
    """Validates assets against format, quality, and brand alignment criteria"""
    
    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
    
    def validate_format(self, asset: Asset) -> bool:
        """Check if asset matches expected schema for its type"""
        required_fields = {
            "listing": ["title", "price", "condition"],
            "character_file": ["character_name", "visual_formats", "personality"],
            "script_draft": ["title", "word_count", "chapter_count", "status"],
            "job_posting": ["title", "description", "location", "salary_range"]
        }
        
        required = required_fields.get(asset.asset_type, [])
        content = asset.content
        
        missing = [f for f in required if f not in content]
        if missing:
            logger.warning(f"Format check failed for {asset.asset_id}: missing fields {missing}")
            return False
        return True
    
    def score_quality(self, asset: Asset) -> int:
        """Score asset quality 1-10"""
        score = 5
        
        content_fields = len(asset.content)
        score += min(3, content_fields // 2)
        
        preview = str(asset.content.get("preview", ""))
        if len(preview) > 100:
            score += 1
        
        if len(asset.metadata) > 3:
            score += 1
        
        return min(10, score)
    
    def check_brand_alignment(self, asset: Asset) -> bool:
        """Check if asset aligns with Commonwealth Picker / Solvik brand"""
        content_str = json.dumps(asset.content).lower()
        
        red_flags = ["spam", "misleading", "unethical", "false"]
        for flag in red_flags:
            if flag in content_str:
                logger.warning(f"Brand alignment check failed for {asset.asset_id}: found red flag '{flag}'")
                return False
        
        green_signals = ["authentic", "clear", "professional", "honest"]
        green_count = sum(1 for signal in green_signals if signal in content_str)
        
        return green_count >= 1 or len(content_str) > 0
    
    def validate(self, asset: Asset) -> ValidationResult:
        """Run full validation"""
        format_pass = self.validate_format(asset)
        quality_score = self.score_quality(asset) if format_pass else 1
        brand_alignment = self.check_brand_alignment(asset) if format_pass else False
        
        result = ValidationResult(format_pass, quality_score, brand_alignment)
        logger.info(f"Validated {asset.asset_id}: format={format_pass}, quality={quality_score}, brand={brand_alignment}, status={result.overall_status}")
        
        return result

# ============================================================================
# ROUTING LOGIC
# ============================================================================

class AssetRouter:
    """Routes validated assets to their destinations"""
    
    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
    
    def route(self, asset: Asset, validation: ValidationResult) -> Tuple[str, str, bool]:
        """Route asset to destination. Returns: (destination_type, destination_path, success)"""
        
        if validation.overall_status != "pass":
            return self._route_to_whiteboard(asset, validation)
        
        creator_config = self.manifest.get("creator_agents", {}).get(asset.creator_agent, {})
        routing = creator_config.get("routing", {})
        
        if asset.creator_agent == "eBay_Listing_Agent":
            return self._route_ebay(asset, routing)
        elif asset.creator_agent == "CTW_Agent":
            return self._route_ctw(asset, routing)
        elif asset.creator_agent == "Ghost_Book_Agent":
            return self._route_ghost_book(asset, routing)
        elif asset.creator_agent == "Jobs_Agent":
            return self._route_jobs(asset, routing)
        else:
            return self._route_to_whiteboard(asset, validation)
    
    def _route_ebay(self, asset: Asset, routing: Dict) -> Tuple[str, str, bool]:
        """Route to eBay API"""
        destination = routing.get("destination", "eBay API")
        endpoint = routing.get("upload_protocol", "https://api.ebay.com/v1/item/upload")
        
        logger.info(f"Routing {asset.asset_id} to {destination}")
        success = self._mock_upload_to_ebay(asset)
        
        return ("eBay", endpoint, success)
    
    def _route_ctw(self, asset: Asset, routing: Dict) -> Tuple[str, str, bool]:
        """Route CTW outputs to project folder or characters_final"""
        asset_type = asset.content.get("type", asset.asset_type)
        
        if asset_type == "character_file":
            destination_path = f"G:/My Drive/Projects/CTW/characters_final/{asset.content.get('character_name')}/"
            destination_type = "characters_final_folder"
        else:
            project_name = asset.project or "ctw_outputs"
            destination_path = f"G:/My Drive/Projects/{project_name}/outputs/"
            destination_type = "project_folder"
        
        logger.info(f"Routing {asset.asset_id} to {destination_path}")
        success = self._mock_copy_to_drive(asset, destination_path)
        
        return (destination_type, destination_path, success)
    
    def _route_ghost_book(self, asset: Asset, routing: Dict) -> Tuple[str, str, bool]:
        """Route Ghost_Book assets based on status"""
        status = asset.content.get("status", "draft")
        
        if status == "draft":
            destination_path = "G:/My Drive/Projects/Ghost_Book/scripts_books_draft/"
            destination_type = "ghost_book_draft"
        elif status == "done":
            destination_path = "G:/My Drive/Projects/Ghost_Book/done_books_scripts/"
            destination_type = "ghost_book_done"
        elif status == "final":
            destination_path = "G:/My Drive/Projects/Ghost_Book/final_books_scripts/"
            destination_type = "ghost_book_final"
        else:
            destination_path = "G:/My Drive/Projects/Ghost_Book/scripts_books_draft/"
            destination_type = "ghost_book_draft"
        
        logger.info(f"Routing {asset.asset_id} ({status}) to {destination_path}")
        success = self._mock_copy_to_drive(asset, destination_path)
        
        return (destination_type, destination_path, success)
    
    def _route_jobs(self, asset: Asset, routing: Dict) -> Tuple[str, str, bool]:
        """Route job postings to Jobs_Match repository"""
        destination_path = "G:/My Drive/Projects/Job_Match/jobs_repository/"
        destination_type = "job_match_repository"
        
        logger.info(f"Routing {asset.asset_id} to {destination_path}")
        success = self._mock_copy_to_drive(asset, destination_path)
        
        return (destination_type, destination_path, success)
    
    def _route_to_whiteboard(self, asset: Asset, validation: ValidationResult) -> Tuple[str, str, bool]:
        """Route failed/review assets to staging/whiteboard"""
        logger.warning(f"Routing {asset.asset_id} to whiteboard (status: {validation.overall_status})")
        return ("whiteboard_staging", f"data/asset_staging/{asset.asset_id}/", True)
    
    def _mock_upload_to_ebay(self, asset: Asset) -> bool:
        """Mock eBay API upload"""
        logger.info(f"[MOCK] Uploading {asset.asset_id} to eBay API")
        return True
    
    def _mock_copy_to_drive(self, asset: Asset, destination: str) -> bool:
        """Mock Google Drive copy"""
        logger.info(f"[MOCK] Copying {asset.asset_id} to {destination}")
        return True

# ============================================================================
# USAGE TRACKING & SOCIAL INTELLIGENCE
# ============================================================================

class UsageTracker:
    """Tracks asset usage and performance; feeds social media intelligence"""
    
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.load_log()
    
    def load_log(self):
        """Load asset_creation_log.json"""
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                self.log_data = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Log not found at {self.log_path}. Creating new log.")
            self.log_data = {
                "log_metadata": {
                    "system": "Master Asset Creation & Distribution Log",
                    "created": get_utc_now(),
                    "maintained_by": "CX_Agent"
                },
                "assets": [],
                "summary_stats": {}
            }
    
    def save_log(self):
        """Save log back to disk"""
        try:
            with open(self.log_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(self.log_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved asset log to {self.log_path}")
        except Exception as e:
            logger.error(f"Failed to save log: {e}")
    
    def add_asset(self, asset: Asset, validation: ValidationResult, routing_result: Tuple) -> Dict:
        """Add new asset to log with validation and routing info"""
        destination_type, destination_path, routing_success = routing_result
        
        log_entry = {
            "asset_id": asset.asset_id,
            "creator_agent": asset.creator_agent,
            "asset_type": asset.asset_type,
            "created_at": asset.created_at,
            "project": asset.project,
            "content": asset.content,
            "validation": {
                "format_check": {"status": "pass" if validation.format_pass else "fail"},
                "quality_score": {"score": validation.quality_score},
                "brand_alignment": {"status": "pass" if validation.brand_alignment else "fail"},
                "overall_status": validation.overall_status,
                "validated_at": validation.timestamp,
                "cx_agent_id": "CX_Agent_20260329"
            },
            "routing": {
                "destination_type": destination_type,
                "destination_path": destination_path,
                "routed_at": get_utc_now(),
                "routing_status": "success" if routing_success else "failed"
            },
            "usage_tracking": {
                "first_usage_at": None,
                "metrics": {},
                "last_metrics_update": None,
                "performance_status": "pending",
                "hours_active": 0
            },
            "social_media": {
                "amplification_candidate": validation.quality_score >= 8,
                "signal_strength": "high" if validation.quality_score >= 9 else "medium" if validation.quality_score >= 7 else "low"
            },
            "metadata": asset.metadata
        }
        
        self.log_data["assets"].append(log_entry)
        self.save_log()
        
        logger.info(f"Added {asset.asset_id} to asset log")
        return log_entry
    
    def identify_amplification_candidates(self) -> List[Dict]:
        """Identify high-performing assets for social media amplification"""
        candidates = []
        for asset in self.log_data.get("assets", []):
            validation = asset.get("validation", {})
            quality = validation.get("quality_score", {}).get("score", 0)
            status = validation.get("overall_status", "")
            usage = asset.get("usage_tracking", {})
            metrics = usage.get("metrics", {})
            
            if quality >= 8 and status == "pass" and len(metrics) > 0:
                candidates.append({
                    "asset_id": asset["asset_id"],
                    "asset_type": asset["asset_type"],
                    "quality_score": quality,
                    "metrics": metrics,
                    "creator_agent": asset["creator_agent"]
                })
        
        return candidates
    
    def cull_expired_jobs(self) -> int:
        """Remove expired job postings (not updated in >30 days)"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        assets_before = len(self.log_data.get("assets", []))
        
        kept_assets = []
        for a in self.log_data.get("assets", []):
            if a["asset_type"] != "job_posting":
                kept_assets.append(a)
            else:
                try:
                    created_at_str = a.get("created_at", "")
                    if created_at_str:
                        asset_date = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if asset_date > cutoff_date:
                            kept_assets.append(a)
                except (ValueError, TypeError):
                    kept_assets.append(a)
        
        self.log_data["assets"] = kept_assets
        assets_after = len(self.log_data.get("assets", []))
        culled = assets_before - assets_after
        
        if culled > 0:
            logger.info(f"Culled {culled} expired job postings")
            self.save_log()
        
        return culled

# ============================================================================
# MAIN CX AGENT ORCHESTRATOR
# ============================================================================

class CXAgent:
    """Master orchestrator for asset validation, routing, and tracking"""
    
    def __init__(self, manifest_path: str, log_path: str):
        self.manifest_path = manifest_path
        self.log_path = log_path
        
        if not os.path.exists(manifest_path):
            logger.error(f"Manifest not found at {manifest_path}")
            self.manifest = {"creator_agents": {}}
        else:
            try:
                with open(manifest_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.manifest = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}")
                self.manifest = {"creator_agents": {}}
        
        self.agent_id = "CXAgent_001"
        self.inbox = AgentInbox()
        self.validator = AssetValidator(self.manifest)
        self.router = AssetRouter(self.manifest)
        self.tracker = UsageTracker(log_path)
    
    def process_asset(self, asset_data: Dict) -> bool:
        """Full pipeline: validate → route → track"""
        asset = Asset(asset_data)
        logger.info(f"Processing asset: {asset.asset_id} ({asset.asset_type} from {asset.creator_agent})")
        
        validation = self.validator.validate(asset)
        routing_result = self.router.route(asset, validation)
        self.tracker.add_asset(asset, validation, routing_result)
        
        return validation.overall_status == "pass"
    
    def daily_scan(self):
        """Run daily CX Agent tasks"""
        logger.info("=== DAILY CX AGENT SCAN ===")
        
        culled = self.tracker.cull_expired_jobs()
        logger.info(f"Culled {culled} expired jobs")
        
        amplification_candidates = self.tracker.identify_amplification_candidates()
        logger.info(f"Identified {len(amplification_candidates)} amplification candidates")
        
        for candidate in amplification_candidates:
            logger.info(f"  → {candidate['asset_id']} ({candidate['asset_type']}): quality={candidate['quality_score']}")

        if amplification_candidates:
            self.inbox.add_item(
                agent_id=self.agent_id,
                project_id="CXAgent",
                question=f"Found {len(amplification_candidates)} amplification candidates",
                required_action="Review digest",
                urgency="LOW"
            )

        self._output_for_social_media(amplification_candidates)
    
    def _output_for_social_media(self, candidates: List[Dict]):
        """Output high-performers for social media agent consumption"""
        output = {
            "generated_at": get_utc_now(),
            "amplification_candidates": candidates
        }
        
        output_path = "data/social_media_feed.json"
        try:
            with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(output, f, indent=2)
            logger.info(f"Wrote social media feed to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write social media feed: {e}")

# ============================================================================
# CLI & SCHEDULING
# ============================================================================

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CX Agent - Asset Quality Gate & Distribution Router")
    parser.add_argument("--mode", choices=["daily_scan", "validate", "monitor"], default="daily_scan",
                        help="Operation mode")
    parser.add_argument("--asset_id", help="Asset ID (for validate mode)")
    parser.add_argument("--hours", type=int, default=24, help="Hours to monitor (for monitor mode)")
    
    args = parser.parse_args()
    
    cx_agent = CXAgent(CONFIG["manifest_path"], CONFIG["log_path"])
    
    if args.mode == "daily_scan":
        cx_agent.daily_scan()
    
    elif args.mode == "validate":
        if not args.asset_id:
            print("Error: --asset_id required for validate mode")
            sys.exit(1)
        logger.info(f"Validating asset {args.asset_id}")
    
    elif args.mode == "monitor":
        logger.info(f"Monitoring assets for {args.hours} hours")

if __name__ == "__main__":
    main()
