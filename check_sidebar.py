import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = open('G:/My Drive/Projects/_studio/sidebar-agent.html', encoding='utf-8', errors='replace').read()
print('sidebar_http refs in sidebar-agent.html:', c.count('sidebar_http'))
print('serve_sidebar refs:', c.count('serve_sidebar'))

# Also check all bat files and scheduler scripts for sidebar_http references
import os
found = []
for root, dirs, files in os.walk('G:/My Drive/Projects/_studio'):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'vector-memory', 'chroma_db']]
    for f in files:
        if f.endswith(('.bat', '.py', '.md', '.json', '.xml')):
            path = os.path.join(root, f)
            try:
                content = open(path, encoding='utf-8', errors='replace').read()
                if 'sidebar_http' in content and f != 'STUDIO_AUDIT.md':
                    found.append(f'{f}: {content.count("sidebar_http")} refs')
            except:
                pass
print('Files referencing sidebar_http:', found if found else 'NONE')
