
# EXPECTED_RUNTIME_SECONDS: 480
#!/usr/bin/env python3
"""
AI News Scraper - ArXiv, Reddit, GitHub feeds
Runs daily, outputs markdown digest to inbox
"""

import json
import requests
from datetime import datetime, timedelta
import re

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

# Bezos Rule: circuit breaker constant
MAX_CONSECUTIVE_FAILURES = 3

# ============================================================================
# ARXIV DAILY PAPERS
# ============================================================================

def fetch_arxiv_papers():
    """Fetch latest AI papers from ArXiv matching keywords"""
    url = "http://arxiv.org/list/cs.AI/recent"
    keywords = ["agent", "memory", "context", "reasoning", "LLM", "transformer"]
    papers = []
    
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        
        # Parse arXiv HTML (basic regex extraction)
        lines = r.text.split('\n')
        current_paper = {}
        
        for line in lines:
            if '<span class="list-identifier">' in line:
                match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', line)
                if match:
                    current_paper['id'] = match.group(1)
                    current_paper['url'] = f"https://arxiv.org/abs/{match.group(1)}"
            
            if '<div class="list-title mathjax">' in line:
                match = re.search(r'<div class="list-title mathjax">Title:(.*?)</div>', line)
                if match:
                    current_paper['title'] = match.group(1).strip()
            
            if '<div class="list-authors">' in line:
                match = re.search(r'Authors:(.*?)(?:</div>|$)', line)
                if match:
                    current_paper['authors'] = match.group(1).strip()[:100]  # First 100 chars
            
            # Check if any keyword matches title
            if 'title' in current_paper and any(kw.lower() in current_paper['title'].lower() for kw in keywords):
                papers.append(current_paper)
                current_paper = {}
        
        return papers[:5]  # Top 5 matching papers
    
    except Exception as e:
        print(f"ArXiv fetch error: {e}")
        return []

# ============================================================================
# REDDIT ALERTS
# ============================================================================

def fetch_reddit_alerts():
    """Fetch recent high-upvote posts from AI subreddits"""
    subreddits = ["MachineLearning", "Anthropic", "OpenAI", "LanguageModels"]
    alerts = []
    
    # Note: Reddit API requires auth. Using Pushshift alternative or manual check
    # For now, use a simple web scrape approach via a Reddit-friendly endpoint
    
    try:
        for sub in subreddits:
            url = f"https://www.reddit.com/r/{sub}/new.json"
            headers = {'User-Agent': 'AI-Studio-Monitor/1.0'}
            
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            if 'data' in data and 'children' in data['data']:
                for post in data['data']['children'][:10]:
                    post_data = post.get('data', {})
                    upvotes = post_data.get('ups', 0)
                    
                    # Flag bug/error reports
                    title = post_data.get('title', '').lower()
                    if upvotes > 50 and any(x in title for x in ['bug', 'error', 'broke', 'regression', 'exploit', 'vulnerability']):
                        alerts.append({
                            'subreddit': sub,
                            'title': post_data.get('title', 'N/A'),
                            'upvotes': upvotes,
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'alert_type': 'BUG'
                        })
                    elif upvotes > 100:
                        alerts.append({
                            'subreddit': sub,
                            'title': post_data.get('title', 'N/A'),
                            'upvotes': upvotes,
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'alert_type': 'TRENDING'
                        })
        
        return alerts[:10]  # Top 10 alerts
    
    except Exception as e:
        print(f"Reddit fetch error: {e}")
        return []

# ============================================================================
# GITHUB CRITICAL ALERTS
# ============================================================================

def fetch_github_alerts():
    """Check GitHub for critical issues in key repos"""
    repos = [
        "anthropics/anthropic-sdk-python",
        "openai/openai-python",
        "huggingface/transformers",
        "langchain-ai/langchain"
    ]
    alerts = []
    
    try:
        for repo in repos:
            url = f"https://api.github.com/repos/{repo}/issues?state=open&sort=created&order=desc&per_page=10"
            headers = {'User-Agent': 'AI-Studio-Monitor/1.0'}
            
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            if isinstance(data, list):
                for issue in data:
                    title = issue.get('title', '').lower()
                    labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
                    
                    if any(x in title or x in ' '.join(labels) for x in ['critical', 'security', 'vulnerability', 'exploit', 'bug']):
                        alerts.append({
                            'repo': repo,
                            'title': issue.get('title', 'N/A'),
                            'url': issue.get('html_url', 'N/A'),
                            'labels': labels,
                            'created': issue.get('created_at', 'N/A')
                        })
        
        return alerts[:5]
    
    except Exception as e:
        print(f"GitHub fetch error: {e}")
        return []

# ============================================================================
# GENERATE MARKDOWN DIGEST
# ============================================================================

def generate_digest(arxiv_papers, reddit_alerts, github_alerts):
    """Compile all sources into a single markdown digest"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    digest = f"""# AI News & Intelligence Digest
**Generated:** {timestamp}

---

## 📚 ArXiv Papers (Last 24h)

"""
    
    if arxiv_papers:
        for paper in arxiv_papers:
            digest += f"- **{paper.get('title', 'Untitled')}**\n"
            digest += f"  - ID: {paper.get('id', 'N/A')}\n"
            digest += f"  - [{paper.get('url', '#')}]({paper.get('url', '#')})\n\n"
    else:
        digest += "*No new papers matching filters today.*\n\n"
    
    digest += """---

## 🚨 Reddit Alerts (Trending + Bugs)

"""
    
    if reddit_alerts:
        for alert in reddit_alerts:
            icon = "🔴" if alert.get('alert_type') == 'BUG' else "📈"
            digest += f"{icon} **r/{alert.get('subreddit', 'N/A')}** - {alert.get('upvotes', 0)} upvotes\n"
            digest += f"  - {alert.get('title', 'N/A')}\n"
            digest += f"  - [{alert.get('url', '#')}]({alert.get('url', '#')})\n\n"
    else:
        digest += "*No alerts today.*\n\n"
    
    digest += """---

## 🛠️ GitHub Critical Issues

"""
    
    if github_alerts:
        for alert in github_alerts:
            digest += f"- **{alert.get('repo', 'N/A')}**\n"
            digest += f"  - {alert.get('title', 'N/A')}\n"
            digest += f"  - Labels: {', '.join(alert.get('labels', [])[:3])}\n"
            digest += f"  - [{alert.get('url', '#')}]({alert.get('url', '#')})\n\n"
    else:
        digest += "*No critical issues today.*\n\n"
    
    return digest

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("[AI News Scraper] Starting...")
    
    # Fetch all sources
    print("[ArXiv] Fetching papers...")
    arxiv = fetch_arxiv_papers()
    print(f"  > Found {len(arxiv)} papers")
    
    print("[Reddit] Fetching alerts...")
    reddit = fetch_reddit_alerts()
    print(f"  > Found {len(reddit)} alerts")
    
    print("[GitHub] Fetching critical issues...")
    github = fetch_github_alerts()
    print(f"  > Found {len(github)} issues")
    
    # Generate digest
    digest = generate_digest(arxiv, reddit, github)
    
    # Save to file (for inbox pickup or direct viewing)
    output_file = "ai_news_digest.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(digest)
    
    print(f"\n[Done] Digest saved to {output_file}")
    print("\n" + "="*60)
    print(digest)
