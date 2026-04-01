import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = open('G:/My Drive/Projects/_studio/janitor_run.py', encoding='utf-8', errors='replace').read()
lines = c.split('\n')
for i,l in enumerate(lines,1):
    if 'def main' in l or 'Janitor starting' in l:
        print(str(i)+': '+l)
