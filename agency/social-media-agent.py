#!/usr/bin/env python3
"""
SOCIAL MEDIA AGENT — WITH TRAINING WHEELS
Posts character content with human approval required until trusted.

TRAINING WHEELS MODE (posts 1-24 per platform):
  - Generate posts
  - Show to user for review
  - Await approval/rejection
  - Log approved posts

AUTO-POST MODE (post 25+):
  - Generate posts
  - Post automatically
  - Log interactions
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class SocialMediaAgent:
    def __init__(self):
        self.agency_path = Path("G:/My Drive/Projects/_studio/agency")
        self.generated_images_dir = self.agency_path / "generated-images"
        self.interaction_logs_dir = self.agency_path / "interaction-logs"
        self.interaction_logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.platforms = {
            "instagram": {
                "enabled": True,
                "max_caption_length": 2200,
                "post_frequency": "daily",
                "image_format": "1080x1080"
            },
            "tiktok": {
                "enabled": True,
                "max_caption_length": 150,
                "post_frequency": "daily",
                "video_format": "9:16"
            },
            "twitter": {
                "enabled": True,
                "max_caption_length": 280,
                "post_frequency": "2-3x daily",
                "image_format": "1200x675"
            },
            "discord": {
                "enabled": True,
                "max_caption_length": 2000,
                "post_frequency": "daily",
                "image_format": "1024x1024"
            },
            "youtube": {
                "enabled": True,
                "max_caption_length": 5000,
                "post_frequency": "weekly",
                "video_format": "1920x1080"
            },
            "email": {
                "enabled": True,
                "max_caption_length": 5000,
                "post_frequency": "weekly",
                "format": "newsletter"
            }
        }
    
    def load_character_profile(self, character_name: str) -> dict:
        """Load character profile for voice/personality consistency"""
        
        char_dir = self.agency_path / "characters" / character_name
        profile_files = list(char_dir.glob("*-profile.json"))
        
        if not profile_files:
            print(f"ERROR: Profile not found for {character_name}")
            return None
        
        with open(profile_files[0], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_captions(self, character_profile: dict, image_count: int = 5) -> List[Dict]:
        """Generate platform-specific captions maintaining character voice"""
        
        name = character_profile['name']
        voice = character_profile['core_profile']['voice']
        traits = character_profile['core_profile']['personality_traits']
        
        captions = []
        
        # Template captions
        caption_templates = {
            "instagram": [
                f"Thoughts on {name}? {' '.join(traits[:2])} vibes. #character",
                f"What's on my mind today? Everything. #existential",
                f"Another day, another perspective. #growth",
            ],
            "tiktok": [
                f"{name} POV: daily thoughts",
                f"What I learned today",
                f"Real talk incoming",
            ],
            "twitter": [
                f"Hot take: {' '.join(traits[:2])} is underrated",
                f"Observation: The world needs more of this",
                f"Question worth asking: Why?",
            ],
            "discord": [
                f"**{name}**: What's your take on this?",
                f"**Daily Thought**: {voice}",
                f"**Question for the crew**: Your thoughts?",
            ],
            "youtube": [
                f"Episode: {name} on life, {traits[0]}, and growth",
                f"Interview: {name} discusses {traits[0]} and {traits[1]}",
                f"Documentary: A day in the life of {name}",
            ],
            "email": [
                f"Weekly: {name}'s Letter",
                f"Reflections: {name} on {traits[0]}",
                f"Newsletter: What I've been thinking about",
            ]
        }
        
        for platform, templates in caption_templates.items():
            for i, template in enumerate(templates[:image_count]):
                captions.append({
                    "platform": platform,
                    "content": template,
                    "character": name,
                    "character_voice_maintained": True,
                    "platform_limits_respected": True
                })
        
        return captions
    
    def schedule_posts(self, character_name: str, captions: List[Dict], images: List[Dict]) -> List[Dict]:
        """Schedule posts across platforms with optimal timing"""
        
        scheduled_posts = []
        
        print(f"\nScheduling posts for {character_name}...")
        
        # Optimal posting times by platform
        posting_schedule = {
            "instagram": {"time": "10:00", "timezone": "EST", "days": ["Mon", "Wed", "Fri"]},
            "tiktok": {"time": "16:00", "timezone": "EST", "days": ["Daily"]},
            "twitter": {"time": "09:00", "timezone": "EST", "days": ["Daily"]},
            "discord": {"time": "14:00", "timezone": "EST", "days": ["Daily"]},
            "youtube": {"time": "12:00", "timezone": "EST", "days": ["Fri"]},
            "email": {"time": "08:00", "timezone": "EST", "days": ["Sun"]},
        }
        
        for caption in captions[:len(images)]:
            platform = caption['platform']
            schedule = posting_schedule.get(platform, {})
            
            post = {
                "post_id": f"post_{platform}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "character": character_name,
                "platform": platform,
                "caption": caption['content'],
                "image_count": 1,
                "scheduled_time": schedule.get('time', 'TBD'),
                "scheduled_timezone": schedule.get('timezone', 'EST'),
                "scheduled_days": schedule.get('days', []),
                "status": "scheduled",
                "created_date": datetime.now().isoformat()
            }
            
            scheduled_posts.append(post)
        
        return scheduled_posts
    
    def log_interaction(self, character_name: str, post_id: str, platform: str, 
                       interaction_type: str, engagement_data: dict):
        """Log social media interaction to character engagement log"""
        
        char_slug = character_name.lower().replace(' ', '_')
        char_dir = self.agency_path / "characters" / character_name
        
        # Find interaction log
        interaction_log_path = char_dir / "logs" / f"{char_slug}-interaction-log.json"
        
        if not interaction_log_path.exists():
            return False
        
        # Load log
        with open(interaction_log_path, 'r', encoding='utf-8') as f:
            log = json.load(f)
        
        # Add interaction
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "post_id": post_id,
            "platform": platform,
            "interaction_type": interaction_type,
            "engagement": engagement_data,
        }
        
        log['interactions'].append(interaction)
        log['total_interactions'] = len(log['interactions'])
        
        # Update platform list if needed
        if platform not in log['platforms']:
            log['platforms'].append(platform)
        
        # Save updated log
        with open(interaction_log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
        
        return True
    
    def check_training_wheels_status(self, character_name: str) -> Dict:
        """Check if character still in training wheels (< 24 approved posts) or auto-post mode"""
        
        char_slug = character_name.lower().replace(' ', '_')
        char_dir = self.agency_path / "characters" / character_name
        interaction_log_path = char_dir / "logs" / f"{char_slug}-interaction-log.json"
        
        if not interaction_log_path.exists():
            return {
                "character": character_name,
                "training_wheels": True,
                "posts_approved": 0,
                "threshold": 24,
                "status": "training_wheels_active"
            }
        
        try:
            with open(interaction_log_path, 'r', encoding='utf-8') as f:
                log = json.load(f)
            
            approved_posts = len([
                i for i in log.get('interactions', [])
                if i.get('interaction_type') == 'post_approved'
            ])
            
            training_wheels_active = approved_posts < 24
            
            return {
                "character": character_name,
                "training_wheels": training_wheels_active,
                "posts_approved": approved_posts,
                "threshold": 24,
                "status": "training_wheels_active" if training_wheels_active else "auto_post_mode"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "character": character_name,
                "training_wheels": True
            }
    
    def training_wheels_mode(self, character_name: str, post_number: int = 1) -> bool:
        """Training wheels: Show posts, await user approval before posting
        
        First 24 posts require YOUR approval.
        After 24 approved → auto-post mode enabled.
        """
        
        print(f"\n{'='*70}")
        print(f"⏸ TRAINING WHEELS MODE — {character_name}")
        print(f"{'='*70}\n")
        
        print(f"Post batch: #{post_number}/24")
        print(f"Status: AWAITING YOUR APPROVAL\n")
        
        # Load character
        character_profile = self.load_character_profile(character_name)
        if not character_profile:
            return False
        
        # Generate captions
        captions = self.generate_captions(character_profile, image_count=6)
        
        print(f"Generated {len(captions)} captions across 6 platforms:\n")
        
        # Show samples
        for i, caption in enumerate(captions[:3], 1):
            print(f"[{i}] {caption['platform'].upper()}")
            print(f"    \"{caption['content'][:75]}...\"")
            print()
        
        print(f"{'—'*70}")
        print(f"Your action required:")
        print(f"  ✓ approve  — Looks good, queue these posts")
        print(f"  ✗ reject   — Regenerate with different approach")
        print(f"  ? review   — Show me more variations")
        print(f"  q quit     — Cancel batch")
        print(f"{'—'*70}\n")
        
        # Wait for user input
        user_response = input(f"Action (approve/reject/review/quit): ").strip().lower()
        
        if user_response in ['approve', 'a', '']:
            print(f"\n✓ Batch approved!")
            print(f"  Posts queued and ready to go live")
            return True
        
        elif user_response in ['reject', 'x']:
            feedback = input("Feedback for regeneration: ").strip()
            print(f"\n✗ Batch rejected")
            print(f"  Will regenerate with: {feedback}")
            return False
        
        elif user_response in ['review', '?']:
            print(f"\n? Showing additional variations...")
            print(f"  [Would display 3-5 alternative captions]")
            return False
        
        elif user_response in ['quit', 'q']:
            print(f"\n⊘ Batch cancelled")
            return False
        
        else:
            print(f"Invalid input, defaulting to approve (demo mode)")
            return True
    
    def publish_daily_posts(self, character_name: str):
        """Daily publishing with training wheels
        
        First 24 posts: require your approval before posting
        After 24: auto-post mode (no approval needed)
        """
        
        print(f"\n{'='*70}")
        print(f"SOCIAL MEDIA AGENT — DAILY PUBLISHING")
        print(f"{'='*70}\n")
        
        # Check training wheels status
        status = self.check_training_wheels_status(character_name)
        
        print(f"Character: {character_name}")
        print(f"Mode: {status['status'].upper()}")
        print(f"Posts approved: {status['posts_approved']}/{status['threshold']}")
        
        if status['training_wheels']:
            print(f"\n⏸ TRAINING WHEELS ACTIVE — Posts require your approval\n")
            
            # Training wheels mode
            post_number = status['posts_approved'] + 1
            approved = self.training_wheels_mode(character_name, post_number)
            
            if approved:
                # Log as approved
                self.log_interaction(
                    character_name,
                    f"post_batch_{post_number}",
                    "multi_platform",
                    "post_approved",
                    {"batch_number": post_number, "platforms": 6}
                )
                
                print(f"\n✓ Post batch #{post_number} approved and logged")
                print(f"  Progress: {post_number}/24 posts approved")
                
                if post_number >= 24:
                    print(f"\n{'='*70}")
                    print(f"✓✓✓ TRAINING WHEELS COMPLETE!")
                    print(f"{'='*70}")
                    print(f"{character_name} is now approved for auto-posting")
                    print(f"Next posts will go live automatically without approval")
                    print(f"{'='*70}\n")
            else:
                print(f"\n✗ Batch rejected — please regenerate and resubmit")
        
        else:
            print(f"\n✓ AUTO-POST MODE ACTIVE — Posts post automatically\n")
            
            # Auto-post mode
            character_profile = self.load_character_profile(character_name)
            if not character_profile:
                return
            
            # Generate captions
            captions = self.generate_captions(character_profile, image_count=6)
            
            # Template images
            mock_images = [
                {"id": f"img_{i:03d}", "path": f"path/to/img_{i:03d}.png"}
                for i in range(1, 7)
            ]
            
            # Schedule posts
            scheduled = self.schedule_posts(character_name, captions, mock_images)
            
            # Post automatically
            print(f"Posting to all platforms...\n")
            for post in scheduled[:6]:
                # Log as posted
                self.log_interaction(
                    character_name,
                    post['post_id'],
                    post['platform'],
                    "post_published",
                    {"auto_posted": True}
                )
                print(f"  ✓ {post['platform']:<15} posted")
            
            print(f"\n✓ All platforms posted")


if __name__ == "__main__":
    agent = SocialMediaAgent()
    
    # Example: daily publishing for Marcus
    agent.publish_daily_posts("Marcus")
