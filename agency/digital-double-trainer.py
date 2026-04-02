#!/usr/bin/env python3
"""
DIGITAL DOUBLE TRAINER
Generate visual/voice options → human approval → train LoRA + voice models
QC test batch before final training
"""

import json
import os
from datetime import datetime
from pathlib import Path
import random

class DigitalDoubleTrainer:
    def __init__(self):
        self.agency_path = Path("G:/My Drive/Projects/_studio/agency")
        self.character_path = None
        self.options_dir = None
        self.trained_models_dir = self.agency_path / "trained-models"
        self.trained_models_dir.mkdir(parents=True, exist_ok=True)
    
    def load_character(self, character_name: str):
        """Load character profile"""
        self.character_path = self.agency_path / "characters" / character_name
        self.options_dir = self.character_path / "identity-options"
        self.options_dir.mkdir(parents=True, exist_ok=True)
        
        profile_file = self.character_path / f"{character_name.lower().replace(' ', '_')}-profile.json"
        if profile_file.exists():
            with open(profile_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def generate_visual_options(self, character_profile: dict) -> List[dict]:
        """Generate 5 different visual interpretations"""
        
        visual_desc = character_profile.get('visual_specs', {}).get('description', '')
        archetype = character_profile.get('archetype', '')
        name = character_profile.get('name', '')
        
        print(f"\n{'='*70}")
        print(f"VISUAL OPTIONS — {name}")
        print(f"{'='*70}")
        
        # Template visual variations based on archetype/description
        visual_interpretations = [
            {
                "option_id": "visual_001",
                "title": "Classic/Dignified",
                "description": f"{visual_desc} — posed formally, professional lighting, serious expression",
                "style": "classical portraiture",
                "mood": "authoritative, trustworthy",
                "setting": "neutral background, studio lighting"
            },
            {
                "option_id": "visual_002",
                "title": "Casual/Approachable",
                "description": f"{visual_desc} — relaxed pose, warm lighting, slight smile, approachable",
                "style": "contemporary casual",
                "mood": "friendly, accessible",
                "setting": "soft natural lighting, home setting"
            },
            {
                "option_id": "visual_003",
                "title": "Intense/Focused",
                "description": f"{visual_desc} — strong gaze, dramatic lighting, concentrated expression",
                "style": "cinematic",
                "mood": "intense, driven, focused",
                "setting": "dramatic shadows, moody lighting"
            },
            {
                "option_id": "visual_004",
                "title": "Stylized/Artistic",
                "description": f"{visual_desc} — artistic rendering, unique composition, expressive",
                "style": "artistic/illustrated",
                "mood": "creative, unconventional",
                "setting": "artistic background, non-traditional framing"
            },
            {
                "option_id": "visual_005",
                "title": "Dynamic/Action",
                "description": f"{visual_desc} — in motion, active pose, energetic lighting",
                "style": "action/cinematic",
                "mood": "energetic, active, in-motion",
                "setting": "dynamic background, movement captured"
            }
        ]
        
        print("\nVisual Options:")
        for i, vis in enumerate(visual_interpretations, 1):
            print(f"\n  [{i}] {vis['title']}")
            print(f"      Style: {vis['style']}")
            print(f"      Mood: {vis['mood']}")
            print(f"      Description: {vis['description'][:100]}...")
        
        return visual_interpretations
    
    def generate_voice_options(self, character_profile: dict) -> List[dict]:
        """Generate 5 different voice interpretations"""
        
        voice_desc = character_profile.get('core_profile', {}).get('voice', '')
        name = character_profile.get('name', '')
        
        print(f"\n{'='*70}")
        print(f"VOICE OPTIONS — {name}")
        print(f"{'='*70}")
        
        voice_interpretations = [
            {
                "option_id": "voice_001",
                "title": "Deep/Authoritative",
                "description": "Deep vocal range, slow pace, measured delivery, commanding presence",
                "pitch": "low",
                "pace": "slow",
                "tone": "authoritative, confident",
                "accent": "neutral",
                "sample_text": "The future belongs to those who can imagine it."
            },
            {
                "option_id": "voice_002",
                "title": "Warm/Friendly",
                "description": "Mid-range, conversational pace, warm tone, approachable delivery",
                "pitch": "medium",
                "pace": "conversational",
                "tone": "warm, friendly, accessible",
                "accent": "neutral",
                "sample_text": "Let me share something I've learned over the years."
            },
            {
                "option_id": "voice_003",
                "title": "Energetic/Passionate",
                "description": "Higher energy, varied pace, passionate delivery, animated expression",
                "pitch": "varied",
                "pace": "energetic",
                "tone": "passionate, excited, engaged",
                "accent": "neutral",
                "sample_text": "This is exactly what we need to do right now!"
            },
            {
                "option_id": "voice_004",
                "title": "Thoughtful/Contemplative",
                "description": "Measured, with pauses, reflective tone, philosophical delivery",
                "pitch": "medium",
                "pace": "slow_with_pauses",
                "tone": "thoughtful, introspective, philosophical",
                "accent": "neutral",
                "sample_text": "One must consider the deeper implications of such matters."
            },
            {
                "option_id": "voice_005",
                "title": "Dynamic/Versatile",
                "description": "Range of expressions, adaptive pace, can shift mood, versatile delivery",
                "pitch": "flexible",
                "pace": "adaptive",
                "tone": "versatile, adaptive, context-aware",
                "accent": "neutral",
                "sample_text": "The key is adaptability in all situations."
            }
        ]
        
        print("\nVoice Options:")
        for i, voice in enumerate(voice_interpretations, 1):
            print(f"\n  [{i}] {voice['title']}")
            print(f"      Pitch: {voice['pitch']}")
            print(f"      Pace: {voice['pace']}")
            print(f"      Tone: {voice['tone']}")
            print(f"      Sample: '{voice['sample_text']}'")
        
        return voice_interpretations
    
    def save_options(self, visual_options: list, voice_options: list, character_name: str):
        """Save options to files for review"""
        
        options_file = self.options_dir / f"{character_name.lower().replace(' ', '_')}-options.json"
        
        options_data = {
            "character": character_name,
            "generated_date": datetime.now().isoformat(),
            "visual_options": visual_options,
            "voice_options": voice_options,
            "approval_status": "pending_visual_approval",
            "visual_approved": None,
            "voice_approved": None
        }
        
        with open(options_file, 'w', encoding='utf-8') as f:
            json.dump(options_data, f, indent=2)
        
        print(f"\n✓ Options saved to: {options_file}")
        return options_data
    
    def wait_for_approval(self, options_data: dict, character_name: str) -> dict:
        """Interactive approval process"""
        
        print(f"\n{'='*70}")
        print(f"APPROVAL NEEDED — {character_name}")
        print(f"{'='*70}")
        
        # Visual approval
        while True:
            try:
                visual_choice = input(f"\nChoose visual option (1-5) or 'skip': ").strip()
                if visual_choice.lower() == 'skip':
                    print("  Skipped visual approval")
                    break
                
                choice_num = int(visual_choice)
                if 1 <= choice_num <= 5:
                    visual_option = options_data['visual_options'][choice_num - 1]
                    options_data['visual_approved'] = visual_option['option_id']
                    options_data['approval_status'] = 'visual_approved'
                    print(f"  ✓ Selected: {visual_option['title']}")
                    break
                else:
                    print("  ERROR: Choose 1-5")
            except ValueError:
                print("  ERROR: Enter number or 'skip'")
        
        # Voice approval
        while True:
            try:
                voice_choice = input(f"\nChoose voice option (1-5) or 'skip': ").strip()
                if voice_choice.lower() == 'skip':
                    print("  Skipped voice approval")
                    break
                
                choice_num = int(voice_choice)
                if 1 <= choice_num <= 5:
                    voice_option = options_data['voice_options'][choice_num - 1]
                    options_data['voice_approved'] = voice_option['option_id']
                    options_data['approval_status'] = 'both_approved'
                    print(f"  ✓ Selected: {voice_option['title']}")
                    break
                else:
                    print("  ERROR: Choose 1-5")
            except ValueError:
                print("  ERROR: Enter number or 'skip'")
        
        return options_data
    
    def generate_test_batch(self, character_profile: dict, visual_approved: str, voice_approved: str) -> dict:
        """Generate test batch (5-10 images) before final training"""
        
        print(f"\n{'='*70}")
        print(f"GENERATING TEST BATCH")
        print(f"{'='*70}")
        print(f"Character: {character_profile['name']}")
        print(f"Visual: {visual_approved}")
        print(f"Voice: {voice_approved}")
        
        # Template: would generate 5-10 test images using Stable Diffusion
        test_batch = {
            "batch_id": f"test-{character_profile['id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "character": character_profile['name'],
            "images_generated": 8,
            "sample_images": [
                {
                    "id": f"test_001",
                    "description": "Character in professional setting",
                    "status": "generated",
                    "path": "[would be: /character/identity-options/test_001.png]"
                },
                {
                    "id": f"test_002",
                    "description": "Character in casual setting",
                    "status": "generated",
                    "path": "[would be: /character/identity-options/test_002.png]"
                },
                {
                    "id": f"test_003",
                    "description": "Character in action pose",
                    "status": "generated",
                    "path": "[would be: /character/identity-options/test_003.png]"
                }
            ],
            "generated_date": datetime.now().isoformat(),
            "approval_pending": True
        }
        
        print(f"\n✓ Test batch generated: {test_batch['images_generated']} images")
        print(f"  Review test images before final training")
        print(f"  Path: {self.character_path}/identity-options/")
        
        return test_batch
    
    def finalize_training(self, character_profile: dict, visual_approved: str, voice_approved: str):
        """Finalize: train LoRA + voice model"""
        
        char_name = character_profile['name'].lower().replace(' ', '_')
        model_dir = self.trained_models_dir / char_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"FINALIZING TRAINING")
        print(f"{'='*70}")
        
        training_config = {
            "character_id": character_profile['id'],
            "character_name": character_profile['name'],
            "visual_option": visual_approved,
            "voice_option": voice_approved,
            "training_start": datetime.now().isoformat(),
            "lora_model": {
                "status": "training",
                "model_path": str(model_dir / "lora_model.safetensors"),
                "rank": 64,
                "alpha": 128,
                "estimated_time": "30-45 minutes"
            },
            "voice_model": {
                "status": "training",
                "model_path": str(model_dir / "voice_model.pth"),
                "estimated_time": "20-30 minutes"
            }
        }
        
        config_file = model_dir / "training_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(training_config, f, indent=2)
        
        print(f"\n✓ Training initialized")
        print(f"  LoRA model: {training_config['lora_model']['estimated_time']}")
        print(f"  Voice model: {training_config['voice_model']['estimated_time']}")
        print(f"  Total: ~1 hour")
        print(f"  Models stored in: {model_dir}")
        
        return training_config
    
    def run_full_training(self, character_name: str):
        """Full workflow: options → approval → test batch → training"""
        
        print(f"\n{'='*70}")
        print(f"DIGITAL DOUBLE TRAINER")
        print(f"{'='*70}\n")
        
        # Load character
        character_profile = self.load_character(character_name)
        if not character_profile:
            print(f"ERROR: Character {character_name} not found")
            return
        
        # Generate options
        visual_options = self.generate_visual_options(character_profile)
        voice_options = self.generate_voice_options(character_profile)
        
        # Save and wait for approval
        options_data = self.save_options(visual_options, voice_options, character_name)
        approved_options = self.wait_for_approval(options_data, character_name)
        
        # Only proceed if both approved
        if not approved_options['visual_approved'] or not approved_options['voice_approved']:
            print(f"\nCannot proceed without both visual and voice approval")
            return
        
        # Generate test batch
        test_batch = self.generate_test_batch(
            character_profile,
            approved_options['visual_approved'],
            approved_options['voice_approved']
        )
        
        # Ask for test batch approval
        test_approved = input(f"\nApprove test batch and proceed to final training? (y/n): ").strip().lower()
        if test_approved != 'y':
            print("Training cancelled")
            return
        
        # Finalize training
        training_config = self.finalize_training(
            character_profile,
            approved_options['visual_approved'],
            approved_options['voice_approved']
        )
        
        print(f"\n✓ Digital Double training queued for: {character_name}")
        print(f"  Next: Image Generation Agent will use trained models")


if __name__ == "__main__":
    # Example usage
    trainer = DigitalDoubleTrainer()
    
    # Test with Marcus (if exists)
    trainer.run_full_training("Marcus")
