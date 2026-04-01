import json
from datetime import datetime

focus_group_contacts = {
    "project": "Linked: The New Science of Networks - Focus Group",
    "compiled": datetime.now().isoformat(),
    "status": "RESEARCH-BASED CONTACT LIST",
    
    "participants": {
        "PUBLISHER": {
            "role": "Evaluate market positioning, audience fit, comp titles",
            "candidates": [
                {
                    "name": "Ingrid Gnerlich",
                    "title": "Publisher for the Sciences",
                    "organization": "Princeton University Press",
                    "expertise": "Physics, Computer Science, natural sciences publishing",
                    "contact": "press.princeton.edu/contact-us",
                    "note": "Oversees complexity theory, network science titles. Published 'Structure and Dynamics of Networks'"
                },
                {
                    "name": "Basic Books Editorial Team",
                    "title": "Popular Science Publisher",
                    "organization": "Basic Books (Perseus Book Group)",
                    "expertise": "Narrative nonfiction, popular science, trade publishing",
                    "contact": "basicbooks.com or perseus distribution",
                    "note": "Published pop-science titles in network/complexity space"
                }
            ]
        },
        
        "COPYEDITOR_TRADE": {
            "role": "Evaluate prose for general audience accessibility",
            "candidates": [
                {
                    "name": "Independent Copyeditor - Recommend from ACES",
                    "title": "Professional Copyeditor (Trade/General Science)",
                    "organization": "American Copy Editors Society",
                    "expertise": "Prose clarity, narrative flow, general audience accessibility",
                    "contact": "aceseditors.org - member directory",
                    "note": "Specializes in popular science/narrative nonfiction"
                }
            ]
        },
        
        "COPYEDITOR_TECHNICAL": {
            "role": "Evaluate rigor, technical precision, scientific accuracy",
            "candidates": [
                {
                    "name": "Independent Copyeditor - Recommend from EMWA/BELS",
                    "title": "Professional Copyeditor (Technical/Scientific)",
                    "organization": "European Medical Writers Association or BELS",
                    "expertise": "Scientific accuracy, mathematical precision, technical terminology",
                    "contact": "emwa.org or bels.org - member directories",
                    "note": "Specializes in scientific/technical publishing"
                }
            ]
        },
        
        "COMPARABLE_AUTHOR_NETWORK_SCIENCE": {
            "name": "Network Science Academic Author",
            "role": "Evaluate how this compares to existing network theory books",
            "candidates": [
                {
                    "name": "Albert-László Barabási",
                    "title": "Robert Gray Dodge Professor of Network Science",
                    "organization": "Northeastern University (Center for Complex Network Research)",
                    "also_at": "Harvard Medical School, Central European University Budapest",
                    "books": "Linked: The New Science of Networks (2002), Network Science (with Márton Pósfai, 2016)",
                    "expertise": "Scale-free networks, preferential attachment, network dynamics",
                    "contact_approach": "Through Northeastern University, Center for Complex Network Research",
                    "note": "THE seminal network science author - wrote 'Linked' which your book references"
                },
                {
                    "name": "Duncan J. Watts",
                    "title": "Data Science and Professor of Sociology",
                    "organization": "University of Pennsylvania / formerly Columbia University",
                    "books": "Six Degrees: The Science of a Connected Age, Small Worlds: The Dynamics of Networks Between Order and Randomness",
                    "expertise": "Small-world networks, network dynamics, social networks",
                    "contact_approach": "Through University of Pennsylvania department",
                    "note": "Co-editor of 'Structure and Dynamics of Networks' - likely to have strong opinions"
                }
            ]
        },
        
        "COMPARABLE_AUTHOR_POPULAR_SCIENCE": {
            "name": "Popular Science Author (Narrative Style)",
            "role": "Evaluate narrative approach, engagement, accessibility trade-offs",
            "candidates": [
                {
                    "name": "Steven Pinker",
                    "title": "Johnstone Family Professor in Harvard Department of Psychology",
                    "books": "The Language Instinct, How the Mind Works, The Blank Slate, The Stuff of Thought, The Better Angels of Our Nature, The Sense of Style, Enlightenment Now, Rationality",
                    "expertise": "Science communication, accessible explanation, balancing rigor with narrative",
                    "organization": "Harvard University",
                    "contact_approach": "Through Harvard Psychology Department",
                    "note": "Known for both rigor AND accessibility. Also critiqued Gladwell's approach to data."
                },
                {
                    "name": "Malcolm Gladwell",
                    "title": "Staff Writer, The New Yorker & Bestselling Author",
                    "books": "The Tipping Point, Blink, Outliers, What the Dog Saw, David and Goliath, Talking to Strangers",
                    "expertise": "Narrative nonfiction, storytelling, narrative-first science communication",
                    "contact_approach": "Through The New Yorker or speaking bureau",
                    "note": "Your book uses similar narrative-first approach. Ask about trade-offs between narrative and rigor."
                }
            ]
        },
        
        "SOURCE_VALIDATOR": {
            "name": "Network Science Academic / Source Validator",
            "role": "Validate factual accuracy, identify rigor gaps, suggest mathematical foundation",
            "candidates": [
                {
                    "name": "Mark Newman",
                    "title": "Professor of Physics",
                    "organization": "University of Michigan",
                    "books": "Co-editor of 'The Structure and Dynamics of Networks' (with Barabási and Watts)",
                    "expertise": "Network mathematics, statistical physics of networks, empirical network analysis",
                    "contact_approach": "Through University of Michigan Physics Department",
                    "note": "Can validate both narrative approach AND mathematical gaps"
                }
            ]
        }
    },
    
    "CONTACT_STRATEGY": {
        "approach": "Research-based cold outreach",
        "message_template": "We're doing a focus group evaluation for a new network science book (Linked: The New Science of Networks). We've written 2 chapters and want expert feedback on positioning, audience fit, and approach before scaling to 8 chapters. Would you be willing to review chapters + answer 3-5 questions specific to your expertise?",
        "timeline": "1-2 weeks for feedback",
        "incentives": "Offer: co-author credit on feedback summary, acknowledgment in book, advance copy when published"
    },
    
    "NEXT_STEPS": [
        "1. For Publishers: Email Princeton University Press Ingrid Gnerlich directly via press.princeton.edu contact form",
        "2. For Copyeditors: Find 2 via ACES and EMWA member directories (technical vs. trade)",
        "3. For Network Authors: Reach out to Barabási, Watts, Newman through university departments",
        "4. For Popular Science: Research contact via Gladwell/Pinker's publicists or university",
        "5. Compile responses into focus group summary"
    ]
}

with open('focus_group_contacts_research.json', 'w', encoding='utf-8') as f:
    json.dump(focus_group_contacts, f, indent=2)

print('[FOCUS GROUP CONTACTS RESEARCH COMPLETE]')
print('\nKey Contacts Identified:')
print('  PUBLISHER: Princeton University Press (Ingrid Gnerlich)')
print('  NETWORK AUTHORS: Barabási, Watts, Newman (all academic leaders)')
print('  POPULAR SCIENCE: Pinker (rigor + narrative), Gladwell (narrative-first)')
print('  COPYEDITORS: Via ACES and EMWA member directories')
print('\nFile saved: focus_group_contacts_research.json')
