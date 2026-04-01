import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
path = 'G:/My Drive/Projects/_studio/sidebar-agent.html'
c = open(path, encoding='utf-8', errors='replace').read()

# Find and remove the orphaned fragment (boot div remnant between INJECTED and TAB BAR)
tabbar = '<!-- TAB BAR: STATUS | INBOX | CHAT | PLAN | ASSETS | DATA | CFG -->'
inj_end = c.find('// END INJECTED DATA\n</script>') + len('// END INJECTED DATA\n</script>')
tabbar_pos = c.find(tabbar)

if inj_end > 0 and tabbar_pos > inj_end:
    fragment = c[inj_end:tabbar_pos]
    print('Fragment to remove (' + str(len(fragment)) + ' chars):')
    print(repr(fragment[:200]))
    c = c[:inj_end] + '\n' + c[tabbar_pos:]
    print('Removed.')

lines = c.split('\n')
print('Lines 249-262:')
for i in range(248, 263):
    print(str(i+1) + ': ' + lines[i][:85])

open(path, 'w', encoding='utf-8').write(c)
print('Done. Size: ' + str(len(c)))
