import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = open('G:/My Drive/Projects/_studio/sidebar-agent.html', encoding='utf-8', errors='replace').read()
print('boot-screen:', c.count('boot-screen'))
print('Boot animation:', c.count('Boot animation'))
print('const INJECTED:', c.count('const INJECTED'))
print('File size:', len(c))
