#!/usr/bin/env python3
"""Synthetic CLI contract fixture, never contacts Anthropic."""
import json
import os
from pathlib import Path
import sys
import time
root = Path(os.environ['CLAUDE_CONFIG_DIR'])
root.mkdir(mode=0o700, parents=True, exist_ok=True)
if sys.argv[1:3] == ['auth', 'login']:
    print('Open https://claude.ai/oauth/authorize?fixture=synthetic-only', flush=True)
    code = input('Paste code: ')
    if code.strip() != 'SYNTHETIC#ONLY': sys.exit(1)
    path = root / '.credentials.json'
    path.write_text(json.dumps({'claudeAiOauth': {'accessToken':'synthetic-'+root.name,
        'refreshToken':'synthetic-refresh-only','expiresAt':(time.time()+3600)*1000,
        'subscriptionType':'max','rateLimitTier':'default_claude_max_5x'}}))
    path.chmod(0o600)
    (root/'.claude.json').write_text(json.dumps({'oauthAccount':{'emailAddress':root.name+'@example.invalid'}}))
    print('Successfully logged in', flush=True)
    # Keep PTY alive until the parent has drained success (matches the real interactive CLI).
    time.sleep(.2)
elif sys.argv[1:3] == ['auth', 'logout']:
    (root/'.credentials.json').unlink(missing_ok=True)
    print('Logged out')
else:
    print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'OK','modelUsage':{'claude-haiku-4-5-20251001':{}},'usage':{'input_tokens':2,'output_tokens':1}}))
