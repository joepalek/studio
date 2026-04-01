import json, os
from datetime import datetime

# Bundle concept reference + focus group intake + sample chapters

package = {
    "project": "Linked: The New Science of Networks",
    "focus_group_package_created": datetime.now().isoformat(),
    
    "what_we_are_asking": [
        "Is this the right book direction, or are we reassembling a shoe and calling it shoes?",
        "Does the current narrative approach match the original intent?",
        "Who should actually read this?",
        "What should we fix or change before we write 6 more chapters?"
    ],
    
    "materials_included": {
        "1_original_concept_reference": "linked_concept_reference.json - what we originally intended to build",
        "2_focus_group_intake": "focus_group_intake.json - the questions we're asking experts",
        "3_chapters_1_and_2": "Available in ghost_outlines/ folder - current prose output",
        "4_peer_review_results": "6.7/10 average - narrative strong, rigor weak"
    },
    
    "expert_roles_needed": [
        {
            "role": "Publisher",
            "expertise": "Market positioning, audience fit, comp titles",
            "will_tell_us": "If this book is marketable and to whom"
        },
        {
            "role": "Copyeditor (2-3)",
            "expertise": "Prose quality, reader accessibility, clarity",
            "will_tell_us": "If the writing works for the intended audience"
        },
        {
            "role": "Comparable Authors (2-3)",
            "expertise": "Similar works, genre norms, unique angles",
            "will_tell_us": "How this compares to existing network science books"
        },
        {
            "role": "Source Validator",
            "expertise": "Non-fiction accuracy, data validation, rigor requirements",
            "will_tell_us": "If we're building the right TYPE of book (theory vs. narrative)"
        }
    ],
    
    "critical_decision_point": {
        "problem": "We built a narrative popular-science book but the original brief may have been for a rigorous theory book.",
        "risk": "Continue 6 more chapters in wrong direction",
        "solution": "Focus group validates direction before we write 48,000 more words",
        "timeline": "Get feedback from focus group BEFORE Chapter 3"
    }
}

with open('focus_group_package_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(package, f, indent=2)

print('[FOCUS GROUP PACKAGE MANIFEST CREATED]')
print('\nReady to send to focus group:')
print('  1. linked_concept_reference.json')
print('  2. focus_group_intake.json')
print('  3. Chapters 1 & 2 PDF/DOCX')
print('  4. Peer review results (6.7/10)')
print('\nFocus group answers the core question:')
print('  "Is this the right book, or a reassembled shoe?"')
