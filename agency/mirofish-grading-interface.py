#!/usr/bin/env python3
"""
MIROFISH GRADING INTERFACE
Simple CLI/file-based grading system for character specs.
Grade specs 1-10, save results, track pass/fail.
"""

import json
import os
from datetime import datetime
from pathlib import Path


class SpecGrader:
    def __init__(self):
        self.queue_file = Path("G:/My Drive/Projects/_studio/agency/spec-queue/spec-queue-current.json")
        self.grades_file = Path("G:/My Drive/Projects/_studio/agency/spec-queue/spec-grades.json")
        self.passing_specs = Path("G:/My Drive/Projects/_studio/agency/spec-queue/passing-specs.json")
        
        self.specs = []
        self.grades = {}
        self.load_specs()
        self.load_grades()
    
    def load_specs(self):
        """Load current spec queue"""
        if self.queue_file.exists():
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.specs = data.get('specs', [])
                print(f"✓ Loaded {len(self.specs)} specs")
        else:
            print(f"ERROR: {self.queue_file} not found")
    
    def load_grades(self):
        """Load existing grades if any"""
        if self.grades_file.exists():
            with open(self.grades_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.grades = data.get('grades', {})
                print(f"✓ Loaded existing grades for {len(self.grades)} specs")
    
    def save_grades(self):
        """Save all grades to file"""
        grades_data = {
            "last_updated": datetime.now().isoformat(),
            "total_graded": len(self.grades),
            "grades": self.grades
        }
        with open(self.grades_file, 'w', encoding='utf-8') as f:
            json.dump(grades_data, f, indent=2)
    
    def get_ungraded_specs(self):
        """Return specs that haven't been graded yet"""
        return [s for s in self.specs if s['id'] not in self.grades]
    
    def grade_spec(self, spec_id, grade, feedback=""):
        """Record a grade for a spec"""
        if not (1 <= grade <= 10):
            print("ERROR: Grade must be 1-10")
            return False
        
        self.grades[spec_id] = {
            "grade": grade,
            "feedback": feedback,
            "graded_date": datetime.now().isoformat(),
            "pass": grade >= 8  # Threshold: 8+ passes
        }
        return True
    
    def generate_report(self):
        """Generate grading report and save passing specs"""
        
        total = len(self.specs)
        graded = len(self.grades)
        ungraded = total - graded
        
        passing = [g for g in self.grades.values() if g['pass']]
        failing = [g for g in self.grades.values() if not g['pass']]
        
        report = {
            "report_date": datetime.now().isoformat(),
            "summary": {
                "total_specs": total,
                "graded": graded,
                "ungraded": ungraded,
                "passing": len(passing),
                "failing": len(failing),
                "pass_rate": f"{(len(passing)/graded*100 if graded > 0 else 0):.1f}%"
            },
            "grades": self.grades
        }
        
        print("\n" + "="*70)
        print("GRADING REPORT")
        print("="*70)
        print(f"Total specs: {total}")
        print(f"Graded: {graded} ({graded/total*100:.0f}%)")
        print(f"Ungraded: {ungraded}")
        print(f"\nPassing (8+): {len(passing)} ({len(passing)/graded*100 if graded > 0 else 0:.1f}%)")
        print(f"Failing (<8): {len(failing)} ({len(failing)/graded*100 if graded > 0 else 0:.1f}%)")
        
        # Grade distribution
        print(f"\nGrade distribution:")
        distribution = {}
        for grade_data in self.grades.values():
            g = grade_data['grade']
            distribution[g] = distribution.get(g, 0) + 1
        
        for grade in sorted(distribution.keys(), reverse=True):
            count = distribution[grade]
            pct = (count / graded * 100) if graded > 0 else 0
            bar = "█" * (count // 2)  # Simple bar chart
            print(f"  {grade}/10: {bar} {count} ({pct:.1f}%)")
        
        # By universe
        print(f"\nBy universe:")
        universe_grades = {}
        for spec in self.specs:
            universe = spec['universe']
            spec_id = spec['id']
            if spec_id in self.grades:
                if universe not in universe_grades:
                    universe_grades[universe] = []
                universe_grades[universe].append(self.grades[spec_id]['grade'])
        
        for universe in sorted(universe_grades.keys()):
            grades_list = universe_grades[universe]
            avg = sum(grades_list) / len(grades_list)
            print(f"  {universe}: avg {avg:.1f} ({len(grades_list)} graded)")
        
        print("="*70 + "\n")
        
        # Save passing specs
        passing_spec_ids = [spec_id for spec_id, grade_data in self.grades.items() if grade_data['pass']]
        passing_specs_list = [s for s in self.specs if s['id'] in passing_spec_ids]
        
        passing_data = {
            "generated": datetime.now().isoformat(),
            "total_passing": len(passing_specs_list),
            "pass_threshold": 8,
            "specs": passing_specs_list
        }
        
        with open(self.passing_specs, 'w', encoding='utf-8') as f:
            json.dump(passing_data, f, indent=2)
        
        print(f"✓ Saved {len(passing_specs_list)} passing specs to {self.passing_specs.name}")
        
        return report
    
    def interactive_grade(self):
        """Interactive grading mode"""
        
        ungraded = self.get_ungraded_specs()
        
        if not ungraded:
            print("All specs have been graded!")
            self.generate_report()
            return
        
        print(f"\nGrading ungraded specs ({len(ungraded)} remaining)...\n")
        
        for idx, spec in enumerate(ungraded, 1):
            print(f"\n[{idx}/{len(ungraded)}] {spec['name']} ({spec['universe']})")
            print(f"  Archetype: {spec['archetype']}")
            print(f"  Traits: {', '.join(spec['personality_traits'][:4])}")
            print(f"  Voice: {spec['voice']}")
            print(f"  Backstory: {spec['backstory'][:80]}...")
            print(f"  Age: {spec['age']}, Pronouns: {spec['pronouns']}")
            
            while True:
                try:
                    grade_input = input(f"\n  Grade (1-10) or 'skip'/'quit': ").strip()
                    
                    if grade_input.lower() == 'quit':
                        print("\nSaving and exiting...")
                        self.save_grades()
                        self.generate_report()
                        return
                    
                    if grade_input.lower() == 'skip':
                        print("  Skipped")
                        break
                    
                    grade = int(grade_input)
                    if 1 <= grade <= 10:
                        feedback = input(f"  Feedback (optional): ").strip()
                        self.grade_spec(spec['id'], grade, feedback)
                        self.save_grades()
                        print(f"  ✓ Graded {grade}/10")
                        break
                    else:
                        print("  ERROR: Grade must be 1-10")
                except ValueError:
                    print("  ERROR: Enter a number or 'skip'/'quit'")
        
        print("\nAll specs graded!")
        self.generate_report()
    
    def batch_grade_high(self, grade=9):
        """Quick mode: grade all ungraded as 'high quality' (9/10)"""
        ungraded = self.get_ungraded_specs()
        for spec in ungraded:
            self.grade_spec(spec['id'], grade, "batch_graded_high")
        self.save_grades()
        print(f"✓ Batch graded {len(ungraded)} specs as {grade}/10")
        self.generate_report()
    
    def show_stats(self):
        """Show current grading stats"""
        ungraded = self.get_ungraded_specs()
        graded = len(self.specs) - len(ungraded)
        
        print(f"\nGrading Stats:")
        print(f"  Total specs: {len(self.specs)}")
        print(f"  Graded: {graded}")
        print(f"  Ungraded: {len(ungraded)}")
        
        if self.grades:
            passing = sum(1 for g in self.grades.values() if g['pass'])
            print(f"  Passing: {passing}")
            print(f"  Failing: {graded - passing}")


def main():
    """Main grading interface"""
    
    grader = SpecGrader()
    
    print(f"\n{'='*70}")
    print("MIROFISH GRADING INTERFACE")
    print(f"{'='*70}")
    
    while True:
        print("\nOptions:")
        print("  1 = Interactive grading")
        print("  2 = Batch grade all as 9/10 (quick)")
        print("  3 = Show stats")
        print("  4 = Generate report")
        print("  5 = Exit")
        
        choice = input("\nChoice (1-5): ").strip()
        
        if choice == '1':
            grader.interactive_grade()
        elif choice == '2':
            confirm = input("Batch grade all ungraded specs as 9/10? (y/n): ").strip().lower()
            if confirm == 'y':
                grader.batch_grade_high(9)
        elif choice == '3':
            grader.show_stats()
        elif choice == '4':
            grader.generate_report()
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
