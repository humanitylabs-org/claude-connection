#!/usr/bin/env python3
"""SYNTHETIC CLI stand-in: test loopback OAuth rotation, not Anthropic certification."""
import fcntl
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

root = Path(os.environ['CLAUDE_CONFIG_DIR'])
with (root / '.fixture-refresh.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    path = root / '.credentials.json'
    stored = json.loads(path.read_text())
    auth = stored['claudeAiOauth']
    if auth['expiresAt'] <= (time.time() + 120) * 1000:
        url = json.loads((root / '.fixture.json').read_text())['issuer']
        req = Request(url + '/oauth/token', data=json.dumps({'grant_type': 'refresh_token',
            'refresh_token': auth['refreshToken']}).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urlopen(req, timeout=5) as r:
                result = json.loads(r.read())
        except HTTPError:
            print(json.dumps({'is_error': True, 'result': 'Login expired. Reconnect.'}))
            raise SystemExit(1)
        auth.update(accessToken=result['access_token'], refreshToken=result['refresh_token'],
                    expiresAt=(time.time() + result['expires_in']) * 1000)
        fd, tmp = tempfile.mkstemp(dir=root)
        with os.fdopen(fd, 'w') as f:
            os.fchmod(f.fileno(), 0o600)
            json.dump(stored, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
print(json.dumps({'is_error': False, 'result': 'OK', 'modelUsage': {'claude-haiku-4-5': {}}}))
