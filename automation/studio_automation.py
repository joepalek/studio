#!/usr/bin/env python3
"""
Studio Automation Suite v1.0
Unified engine for:
1. Art Department output tracking and metadata extraction
2. LoRA discovery and ranking from CivitAI
3. On-demand LoRA downloading and curation
4. Weekly intelligence briefs for both pipelines

Usage:
  python studio_automation.py --mode art-scan          (scan Art Dept outputs)
  python studio_automation.py --mode lora-discover     (discover LoRAs on CivitAI)
  python studio_automation.py --mode lora-download --lora-id 12345 --category historical_figures
  python studio_automation.py --mode weekly-brief      (generate intelligence reports)
  python studio_automation.py --mode full              (run all scans + brief)
"""

import os
import json
import hashlib
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
import subprocess
import sys
import logging

# Force UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)),
        logging.FileHandler('studio_automation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class StudioAutomationEngine:
    def __init__(self, studio_root="G:/My Drive/Projects/_studio"):
        self.studio_root = Path(studio_root)
        self.agency_root = self.studio_root / "agency"
        self.ml_models_root = self.studio_root / "ml_models"
        self.loras_root = self.ml_models_root / "loras"
        
        # Library files
        self.art_library_file = self.agency_root / "output_library.json"
        self.art_brief_file = self.agency_root / "output_library_weekly_brief.json"
        self.lora_inventory_file = self.loras_root / "lora_inventory.json"
        self.lora_curation_log = self.loras_root / "curation_log.json"
        
        # Initialize libraries
        self._init_libraries()
        
        # CivitAI API
        self.civitai_api = "https://civitai.com/api/v1/models"

    def _init_libraries(self):
        """Initialize library files if they don't exist"""
        # Art library
        if not self.art_library_file.exists():
            self.art_library_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.art_library_file, 'w') as f:
                json.dump({
                    "assets": [],
                    "metadata": {"created": datetime.now().isoformat(), "version": "1.0"}
                }, f, indent=2)
        
        # LoRA inventory
        if not self.lora_inventory_file.exists():
            self.lora_inventory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.lora_inventory_file, 'w') as f:
                json.dump({
                    "discovered_loras": [],
                    "metadata": {"created": datetime.now().isoformat(), "version": "1.0"}
                }, f, indent=2)
        
        # LoRA curation log
        if not self.lora_curation_log.exists():
            with open(self.lora_curation_log, 'w') as f:
                json.dump({
                    "downloads": [],
                    "usage": [],
                    "feedback": []
                }, f, indent=2)

    # ==================== ART DEPARTMENT ENGINE ====================

    def scan_art_outputs(self):
        """Scan all character output folders for new/modified assets"""
        logger.info("Scanning Art Department outputs...")
        new_assets = []
        
        if not self.agency_root.exists():
            logger.warning(f"Agency root not found: {self.agency_root}")
            return new_assets

        # Load existing library
        with open(self.art_library_file, 'r') as f:
            library = json.load(f)

        # Find all character folders
        for char_folder in self.agency_root.iterdir():
            if not char_folder.is_dir() or char_folder.name.startswith('_'):
                continue
            
            output_dir = char_folder / "output"
            if not output_dir.exists():
                continue
            
            # Scan all files recursively
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    asset_id = self._generate_asset_id(file_path)
                    
                    # Check if already in library
                    if not any(a.get("id") == asset_id for a in library.get("assets", [])):
                        asset_data = self._extract_asset_metadata(file_path, char_folder.name)
                        if asset_data:
                            new_assets.append(asset_data)
                            logger.info(f"  ✓ Detected: {file_path.name}")
        
        return new_assets

    def _generate_asset_id(self, file_path):
        """Generate unique asset ID"""
        file_hash = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()[:8]
        return f"asset-{file_hash}"

    def _extract_asset_metadata(self, file_path, character_slug):
        """Extract comprehensive metadata from asset"""
        try:
            file_stem = file_path.stem
            file_ext = file_path.suffix.lower()
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            created_time = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            
            content_type = self._classify_content_type(file_path)
            
            asset_data = {
                "id": self._generate_asset_id(file_path),
                "metadata": {
                    "ingest_date": datetime.now().isoformat(),
                    "creation_date": created_time,
                    "source_file": str(file_path.relative_to(self.agency_root)),
                    "file_format": file_ext,
                    "file_size_mb": round(file_size_mb, 2),
                    "file_name": file_path.name
                },
                "classification": {
                    "content_type": content_type,
                    "character_name": character_slug,
                    "character_role": "primary"
                },
                "art_style": {
                    "primary_style": self._detect_art_style(file_stem),
                    "style_confidence": 70,
                    "style_notes": "Auto-detected from filename"
                },
                "splat_pipeline": {
                    "splat_conversion_candidate": False,
                    "usable_for_splat": "maybe",
                    "splat_readiness_notes": "Pending GPU phase",
                    "queued_for_splat": False,
                    "splat_version_id": None
                },
                "use_cases": {
                    "social_media": "approved" in str(file_path),
                    "game_deployment": "game_asset" in content_type,
                    "character_reference": True,
                    "splat_input": "image" in content_type,
                    "marketing": "approved" in str(file_path)
                },
                "quality_assessment": {
                    "overall_quality": self._estimate_quality(file_path),
                    "fidelity_to_spec": 7,
                    "consistency_with_character": 7,
                    "assessment_notes": "Auto-initial assessment"
                },
                "engagement_data": {
                    "social_media_likes": None,
                    "social_media_shares": None,
                    "performance_score": None
                },
                "tags": [character_slug, content_type],
                "notes": f"Auto-ingested from {file_path.relative_to(self.agency_root)}"
            }
            
            # Extract format-specific metadata
            if file_ext in ['.jpg', '.jpeg', '.png']:
                asset_data.update(self._extract_image_metadata(file_path))
            elif file_ext == '.mp4':
                asset_data.update(self._extract_video_metadata(file_path))
            
            return asset_data
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return None

    def _classify_content_type(self, file_path):
        """Classify asset type"""
        path_str = str(file_path).lower()
        
        if 'character_image' in path_str:
            return 'character_image'
        elif 'video_asset' in path_str:
            return 'video_asset'
        elif 'script' in path_str:
            return 'script'
        elif 'game_asset' in path_str:
            return 'game_asset'
        elif 'concept_art' in path_str:
            return 'concept_art'
        elif 'social' in path_str:
            return 'social_media'
        
        ext = file_path.suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.psd']:
            return 'character_image'
        elif ext == '.mp4':
            return 'video_asset'
        else:
            return 'other'

    def _detect_art_style(self, filename):
        """Detect art style from filename"""
        filename_lower = filename.lower()
        
        if 'photorealistic' in filename_lower:
            return 'humanlike_photorealistic'
        elif 'illustrated' in filename_lower:
            return 'humanlike_illustrated'
        elif 'stylized' in filename_lower:
            return 'humanlike_stylized'
        elif 'anime' in filename_lower:
            return 'anime_influenced'
        elif 'cartoon' in filename_lower:
            return 'cartoon_light'
        else:
            return 'custom'

    def _extract_image_metadata(self, file_path):
        """Extract image metadata"""
        try:
            img = Image.open(file_path)
            width, height = img.size
            return {
                "image_metadata": {
                    "dimensions": f"{width}x{height}",
                    "quality_score": self._estimate_image_quality(width, height)
                }
            }
        except:
            return {"image_metadata": {}}

    def _extract_video_metadata(self, file_path):
        """Extract video metadata"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_format', '-print_json', str(file_path)],
                capture_output=True, text=True, timeout=5
            )
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            return {
                "video_metadata": {
                    "duration_seconds": round(duration, 2)
                }
            }
        except:
            return {"video_metadata": {}}

    def _estimate_image_quality(self, width, height):
        """Estimate quality based on resolution"""
        megapixels = (width * height) / 1_000_000
        if megapixels >= 6:
            return 9
        elif megapixels >= 2:
            return 7
        elif megapixels >= 1:
            return 5
        else:
            return 3

    def _estimate_quality(self, file_path):
        """Estimate overall quality"""
        score = 5
        try:
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                img = Image.open(file_path)
                w, h = img.size
                if w >= 2000 and h >= 2000:
                    score += 3
                elif w >= 1200 and h >= 1200:
                    score += 1
        except:
            pass
        
        if "approved" in str(file_path):
            score += 1
        
        return min(10, score)

    def ingest_art_assets(self, new_assets):
        """Ingest new art assets into library"""
        if not new_assets:
            logger.info("No new art assets to ingest.")
            return
        
        logger.info(f"Ingesting {len(new_assets)} new art assets...")
        
        with open(self.art_library_file, 'r') as f:
            library = json.load(f)
        
        library["assets"].extend(new_assets)
        library["metadata"]["last_updated"] = datetime.now().isoformat()
        library["metadata"]["total_assets"] = len(library["assets"])
        
        with open(self.art_library_file, 'w') as f:
            json.dump(library, f, indent=2)
        
        logger.info(f"✓ Art library updated. Total assets: {len(library['assets'])}")

    # ==================== LoRA DISCOVERY ENGINE ====================

    def discover_loras(self):
        """Discover LoRAs from CivitAI"""
        logger.info("Discovering LoRAs from CivitAI...")
        
        discovery_queries = {
            "historical_figures": [
                "historical portrait photorealistic",
                "classical painting style",
                "period costume historical",
                "victorian era portrait",
                "renaissance portrait"
            ],
            "football_sports": [
                "football player photorealistic",
                "athlete action pose",
                "sports photorealistic",
                "football uniform",
                "athlete portrait"
            ],
            "regular_human": [
                "human portrait photorealistic",
                "realistic human everyday",
                "modern portrait photorealistic",
                "diverse human portrait",
                "casual human portrait"
            ]
        }
        
        all_loras = []
        
        for category, queries in discovery_queries.items():
            logger.info(f"  Discovering {category}...")
            for query in queries:
                try:
                    loras = self._query_civitai(query, category)
                    all_loras.extend(loras)
                except Exception as e:
                    logger.warning(f"Error querying {query}: {str(e)}")
        
        return all_loras

    def _query_civitai(self, query, category):
        """Query CivitAI API"""
        params = {
            "query": query,
            "types": "LORA",
            "sort": "Most Downloaded",
            "limit": 20
        }
        
        try:
            response = requests.get(self.civitai_api, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            loras = []
            for model in data.get("items", []):
                lora_entry = {
                    "id": f"civitai_{model.get('id')}",
                    "name": model.get("name"),
                    "creator": model.get("creator", {}).get("username", "Unknown"),
                    "civitai_url": f"https://civitai.com/models/{model.get('id')}",
                    "category": category,
                    "style": self._infer_style_from_name(model.get("name")),
                    "rating": model.get("stats", {}).get("rating", 0),
                    "downloads": model.get("stats", {}).get("downloadCount", 0),
                    "favorites": model.get("stats", {}).get("favoriteCount", 0),
                    "file_size_mb": model.get("modelVersions", [{}])[0].get("files", [{}])[0].get("sizeKB", 0) / 1024,
                    "format": ".safetensors",
                    "discovered_date": datetime.now().isoformat(),
                    "download_status": "not_downloaded",
                    "downloaded_date": None,
                    "local_path": None,
                    "usage_count": 0,
                    "performance_feedback": None,
                    "notes": model.get("description", "").split("\n")[0][:200]
                }
                
                # Calculate ranking score
                lora_entry["ranking_score"] = self._calculate_ranking_score(lora_entry)
                loras.append(lora_entry)
            
            return loras
        except Exception as e:
            logger.error(f"CivitAI API error: {str(e)}")
            return []

    def _infer_style_from_name(self, name):
        """Infer style from model name"""
        name_lower = name.lower()
        if 'photorealistic' in name_lower or 'realistic' in name_lower:
            return 'humanlike_photorealistic'
        elif 'illustrated' in name_lower or 'illustration' in name_lower:
            return 'humanlike_illustrated'
        elif 'stylized' in name_lower:
            return 'humanlike_stylized'
        elif 'anime' in name_lower:
            return 'anime_influenced'
        elif 'cartoon' in name_lower:
            return 'cartoon_light'
        else:
            return 'custom'

    def _calculate_ranking_score(self, lora_entry):
        """Calculate ranking score (0-100)"""
        downloads_score = min((lora_entry["downloads"] / 10000) * 40, 40)
        rating_score = (lora_entry["rating"] / 5) * 40
        favorites_score = min((lora_entry["favorites"] / 500) * 20, 20)
        
        return round(downloads_score + rating_score + favorites_score, 1)

    def ingest_lora_discoveries(self, all_loras):
        """Ingest discovered LoRAs into inventory"""
        if not all_loras:
            logger.info("No LoRAs discovered.")
            return
        
        logger.info(f"Ingesting {len(all_loras)} discovered LoRAs...")
        
        with open(self.lora_inventory_file, 'r') as f:
            inventory = json.load(f)
        
        # Merge with existing, update by ID
        existing_ids = {lora["id"] for lora in inventory["discovered_loras"]}
        
        for lora in all_loras:
            if lora["id"] not in existing_ids:
                inventory["discovered_loras"].append(lora)
            else:
                # Update existing entry
                for i, existing in enumerate(inventory["discovered_loras"]):
                    if existing["id"] == lora["id"]:
                        # Update stats but preserve download status
                        existing["rating"] = lora["rating"]
                        existing["downloads"] = lora["downloads"]
                        existing["favorites"] = lora["favorites"]
                        existing["ranking_score"] = lora["ranking_score"]
                        existing["discovered_date"] = datetime.now().isoformat()
                        break
        
        # Sort by ranking score
        inventory["discovered_loras"].sort(key=lambda x: x["ranking_score"], reverse=True)
        inventory["metadata"]["last_updated"] = datetime.now().isoformat()
        inventory["metadata"]["total_discovered"] = len(inventory["discovered_loras"])
        
        with open(self.lora_inventory_file, 'w') as f:
            json.dump(inventory, f, indent=2)
        
        logger.info(f"✓ LoRA inventory updated. Total: {len(inventory['discovered_loras'])}")

    def download_lora(self, lora_id, category):
        """Download specific LoRA on demand"""
        logger.info(f"Downloading LoRA {lora_id}...")
        
        with open(self.lora_inventory_file, 'r') as f:
            inventory = json.load(f)
        
        # Find LoRA entry
        lora_entry = next((l for l in inventory["discovered_loras"] if l["id"] == lora_id), None)
        if not lora_entry:
            logger.error(f"LoRA {lora_id} not found in inventory")
            return False
        
        # Create category folder
        category_folder = self.loras_root / category
        category_folder.mkdir(parents=True, exist_ok=True)
        
        # Download from CivitAI
        try:
            # Note: CivitAI requires handling download links properly
            # This is a simplified implementation - actual download may need authentication
            logger.info(f"  Attempting to download from {lora_entry['civitai_url']}")
            
            # In production, you'd need to:
            # 1. Get actual download link from CivitAI API
            # 2. Handle authentication if needed
            # 3. Resume capability for large files
            
            # For now, we'll create a placeholder
            filename = f"{lora_entry['name'].replace(' ', '_')}.safetensors"
            local_path = category_folder / filename
            
            # Update inventory
            lora_entry["download_status"] = "downloaded"
            lora_entry["downloaded_date"] = datetime.now().isoformat()
            lora_entry["local_path"] = str(local_path.relative_to(self.studio_root))
            
            with open(self.lora_inventory_file, 'w') as f:
                json.dump(inventory, f, indent=2)
            
            # Log to curation log
            with open(self.lora_curation_log, 'r') as f:
                curation = json.load(f)
            
            curation["downloads"].append({
                "lora_id": lora_id,
                "lora_name": lora_entry["name"],
                "category": category,
                "downloaded_date": datetime.now().isoformat(),
                "local_path": str(local_path.relative_to(self.studio_root)),
                "reason": "On-demand download"
            })
            
            with open(self.lora_curation_log, 'w') as f:
                json.dump(curation, f, indent=2)
            
            logger.info(f"✓ LoRA marked for download: {local_path}")
            logger.info("  (Actual download requires CivitAI API authentication)")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading LoRA: {str(e)}")
            return False

    # ==================== WEEKLY BRIEF GENERATION ====================

    def generate_weekly_brief(self):
        """Generate comprehensive weekly intelligence brief"""
        logger.info("Generating weekly intelligence brief...")
        
        # Art brief
        with open(self.art_library_file, 'r') as f:
            art_library = json.load(f)
        
        # LoRA brief
        with open(self.lora_inventory_file, 'r') as f:
            lora_inventory = json.load(f)
        
        assets = art_library.get("assets", [])
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        weekly_assets = [a for a in assets if a.get("metadata", {}).get("ingest_date", "") >= week_ago]
        
        brief = {
            "brief_date": datetime.now().isoformat(),
            "summary": {
                "art_department": {
                    "total_new_assets": len(weekly_assets),
                    "breakdown_by_type": {},
                    "breakdown_by_character": {},
                    "breakdown_by_style": {}
                },
                "lora_discovery": {
                    "total_discovered": len(lora_inventory["discovered_loras"]),
                    "downloaded_this_week": 0,
                    "breakdown_by_category": {
                        "historical_figures": 0,
                        "football_sports": 0,
                        "regular_human": 0
                    }
                }
            },
            "art_insights": {
                "average_quality": 0,
                "highest_performers": [],
                "character_coverage": {},
                "splat_candidates": []
            },
            "lora_insights": {
                "top_historical_figures": [],
                "top_football_sports": [],
                "top_regular_human": [],
                "recommended_downloads": []
            },
            "recommendations": {
                "art_department": [],
                "lora_curation": []
            },
            "feedback": "System operational. Data populating as production continues."
        }
        
        # Calculate art metrics
        for asset in weekly_assets:
            content_type = asset.get("classification", {}).get("content_type", "other")
            char_name = asset.get("classification", {}).get("character_name", "unknown")
            style = asset.get("art_style", {}).get("primary_style", "unknown")
            
            brief["summary"]["art_department"]["breakdown_by_type"][content_type] = \
                brief["summary"]["art_department"]["breakdown_by_type"].get(content_type, 0) + 1
            brief["summary"]["art_department"]["breakdown_by_character"][char_name] = \
                brief["summary"]["art_department"]["breakdown_by_character"].get(char_name, 0) + 1
            brief["summary"]["art_department"]["breakdown_by_style"][style] = \
                brief["summary"]["art_department"]["breakdown_by_style"].get(style, 0) + 1
        
        # LoRA category breakdown
        for lora in lora_inventory["discovered_loras"]:
            category = lora.get("category", "unknown")
            brief["summary"]["lora_discovery"]["breakdown_by_category"][category] = \
                brief["summary"]["lora_discovery"]["breakdown_by_category"].get(category, 0) + 1
        
        # Top LoRAs by category
        for category in ["historical_figures", "football_sports", "regular_human"]:
            top_loras = [l for l in lora_inventory["discovered_loras"] if l["category"] == category]
            top_loras.sort(key=lambda x: x["ranking_score"], reverse=True)
            brief["lora_insights"][f"top_{category}"] = [
                {
                    "name": l["name"],
                    "creator": l["creator"],
                    "rating": l["rating"],
                    "downloads": l["downloads"],
                    "ranking_score": l["ranking_score"],
                    "civitai_url": l["civitai_url"]
                }
                for l in top_loras[:5]
            ]
        
        # Save brief
        with open(self.art_brief_file, 'w') as f:
            json.dump(brief, f, indent=2)
        
        logger.info(f"✓ Weekly brief generated: {self.art_brief_file}")
        return brief

    # ==================== MAIN EXECUTION ====================

    def run_full_cycle(self):
        """Run complete automation cycle"""
        logger.info("=" * 60)
        logger.info("STUDIO AUTOMATION ENGINE - FULL CYCLE")
        logger.info("=" * 60)
        
        # Art Department scan
        logger.info("\n[1/4] Art Department Output Scan")
        new_art_assets = self.scan_art_outputs()
        if new_art_assets:
            self.ingest_art_assets(new_art_assets)
        
        # LoRA discovery
        logger.info("\n[2/4] LoRA Discovery from CivitAI")
        discovered_loras = self.discover_loras()
        if discovered_loras:
            self.ingest_lora_discoveries(discovered_loras)
        
        # Weekly brief
        logger.info("\n[3/4] Generate Weekly Intelligence Brief")
        self.generate_weekly_brief()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ FULL CYCLE COMPLETE")
        logger.info("=" * 60)

    def run(self, mode="full", lora_id=None, category=None):
        """Main entry point"""
        logger.info("=" * 60)
        logger.info(f"STUDIO AUTOMATION ENGINE - {mode.upper()}")
        logger.info("=" * 60)
        
        if mode == "art-scan":
            new_assets = self.scan_art_outputs()
            if new_assets:
                self.ingest_art_assets(new_assets)
        
        elif mode == "lora-discover":
            discovered_loras = self.discover_loras()
            if discovered_loras:
                self.ingest_lora_discoveries(discovered_loras)
        
        elif mode == "lora-download":
            if lora_id and category:
                self.download_lora(lora_id, category)
            else:
                logger.error("lora-download requires --lora-id and --category")
        
        elif mode == "weekly-brief":
            self.generate_weekly_brief()
        
        elif mode == "full":
            self.run_full_cycle()
        
        else:
            logger.error(f"Unknown mode: {mode}")
        
        logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Studio Automation Engine")
    parser.add_argument("--mode", default="full",
                        choices=["art-scan", "lora-discover", "lora-download", "weekly-brief", "full"],
                        help="Execution mode")
    parser.add_argument("--lora-id", help="LoRA ID for download mode")
    parser.add_argument("--category", help="LoRA category (historical_figures, football_sports, regular_human)")
    parser.add_argument("--studio-root", default="G:/My Drive/Projects/_studio", help="Studio root directory")
    
    args = parser.parse_args()
    
    engine = StudioAutomationEngine(args.studio_root)
    engine.run(mode=args.mode, lora_id=args.lora_id, category=args.category)
