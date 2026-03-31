import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
content = open('G:/My Drive/Projects/_studio/sidebar-agent.html', encoding='utf-8', errors='replace').read()
lines = content.split('\n')

# Find any line with only '} catch' that follows another '} catch' within 5 lines
problems = []
for i in range(1, len(lines)):
    if re.search(r'^\s*\}\s*catch\s*\(', lines[i]):
        # Look back up to 8 lines for another catch
        for j in range(max(0,i-8), i):
            if re.search(r'^\s*\}\s*catch\s*\(', lines[j]):
                problems.append((j+1, i+1))
                break

if problems:
    print('DUPLICATE CATCHES FOUND:')
    for a, b in problems:
        print('  Lines ' + str(a) + ' and ' + str(b))
        for k in range(a-2, b+2):
            if 0 <= k < len(lines):
                print('    ' + str(k+1) + ': ' + lines[k])
else:
    print('No duplicate catch blocks found - syntax OK')

# Also check brace balance in JS section
js = content[content.find('<script>\n// ═══ STATE'):]
js = js[:js.rfind('</script>')]
ob = js.count('{')
cb = js.count('}')
print('JS brace balance: open=' + str(ob) + ' close=' + str(cb) + ' diff=' + str(ob-cb))
