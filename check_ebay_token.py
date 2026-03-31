import json, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = json.load(open('G:/My Drive/Projects/_studio/ebay-token-cache.json'))
t = c.get('user_token', {})
print('access_token:', str(t.get('access_token',''))[:25] + '...')
print('refresh_token:', 'YES' if t.get('refresh_token') else 'NO')
exp = t.get('expires_at', 0)
print('expires_at:', 'VALID' if exp > time.time() else 'EXPIRED')
print('token_type:', t.get('token_type',''))
scope = t.get('scope','')
for s in scope.split(' '):
    print(' ', s)
