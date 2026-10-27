#!/usr/bin/env python3
"""Synthetic CLI sign-in + native stream. Never contacts a real provider."""
import json
import os
from pathlib import Path
import sys
import time

root=Path(os.environ['CLAUDE_CONFIG_DIR'])
root.mkdir(mode=0o700,parents=True,exist_ok=True)
if sys.argv[1:3]==['auth','login']:
    print('Open https://claude.ai/oauth/authorize?fixture=synthetic-only',flush=True)
    if input('Paste code: ').strip()!='SYNTHETIC#ONLY':sys.exit(1)
    p=root/'.credentials.json'
    p.write_text(json.dumps({'claudeAiOauth':{'accessToken':'synthetic-'+root.name,
        'refreshToken':'synthetic-refresh-only','expiresAt':(time.time()+3600)*1000,
        'subscriptionType':'max','rateLimitTier':'default_claude_max_5x'}}));p.chmod(0o600)
    (root/'.claude.json').write_text(json.dumps({'oauthAccount':{'emailAddress':root.name+'@example.invalid'}}))
    print('Successfully logged in',flush=True);time.sleep(.2);sys.exit(0)
if sys.argv[1:3]==['auth','logout']:
    (root/'.credentials.json').unlink(missing_ok=True);sys.exit(0)
try:
    auth=json.loads((root/'.credentials.json').read_text())['claudeAiOauth']
    if auth['expiresAt']<=time.time()*1000:raise ValueError('expired')
except (OSError,ValueError,KeyError):
    print('Not logged in',file=sys.stderr);sys.exit(1)
if sys.argv[1:3]==['auth','status']:
    print(json.dumps({'loggedIn':True,'subscriptionType':'max'}));sys.exit(0)
if '--version' in sys.argv:print('2.1.263 (synthetic offline CLI)');sys.exit(0)
# Native subprocess protocol, not a fake Hermes client or fake agent.
for line in sys.stdin:
    json.loads(line)
text='app-owned-'+root.name
if os.environ.get('PROBE_CONSUMED_PATH'):
    with open(os.environ['PROBE_CONSUMED_PATH'],'a') as f:f.write(root.name+'\n')
for row in [
    {'type':'stream_event','event':{'type':'content_block_delta','delta':{'type':'text_delta','text':text}}},
    {'type':'assistant','message':{'role':'assistant','content':[{'type':'text','text':text}],'stop_reason':'end_turn'}},
    {'type':'stream_event','event':{'type':'message_stop'}},
    {'type':'result','subtype':'success','is_error':False,'num_turns':1,'usage':{'input_tokens':1,'output_tokens':1}}
]:print(json.dumps(row),flush=True)
