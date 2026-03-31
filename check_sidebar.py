import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
content = open('G:/My Drive/Projects/_studio/sidebar-agent.html', encoding='utf-8', errors='replace').read()
title = re.search(r'<title>(.*?)</title>', content)
print('Title:', title.group(1) if title else 'not found')
tabs = re.findall(r"data-tab='([^']+)'", content)
if not tabs:
    tabs = re.findall(r'data-tab="([^"]+)"', content)
print('Tabs:', tabs)
lines = content.count('\n')
print('Total lines:', lines)
# check for mobile-inbox references
mobile_refs = content.count('mobile-inbox')
print('mobile-inbox refs:', mobile_refs)
# check for agent inbox tab
agent_inbox = 'agent' in content.lower() and 'inbox' in content.lower()
print('Has agent inbox concept:', agent_inbox)
