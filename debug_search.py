import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
content = open('G:/My Drive/Projects/_studio/sidebar-agent.html', encoding='utf-8', errors='replace').read()
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'chatHist' in line or 'systemPrompt' in line or 'initChat' in line or 'system_prompt' in line.lower():
        print(f'{i}: {line[:120]}')
