import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
content = open('G:/My Drive\Projects/_studio/sidebar-agent.html', encoding='utf-8', errors='replace').read()

# Find all switchTab onclick lines with context
matches = [(m.start(), m.group()) for m in re.finditer(r"onclick=\"switchTab\('[^']+'\)\"[^>]*>[^<]+</div>", content)]
for pos, m in matches:
    line_no = content[:pos].count('\n') + 1
    print(f"Line {line_no}: {m[:80]}")
