"""Acceptance-only loopback provider injection. Not shipped in either app recipe."""
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, '/app')
provider = sys.argv[1]
if provider == 'claude':
    class Usage(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            raw=json.dumps({'five_hour':{'utilization':10,'resets_at':'2030-01-01T00:00:00Z'}}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    fake=ThreadingHTTPServer(('127.0.0.1',0),Usage)
    os.environ['WIZARD_CLAUDE_USAGE_URL']='http://127.0.0.1:'+str(fake.server_port)+'/usage'
else:
    spec=importlib.util.spec_from_file_location('synthetic_provider','/app/test-chatgpt.py')
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    state={'lock':threading.Lock(),'requests':[],'polls':0,'refreshes':0,
           'refresh':'SYNTHETIC-ONLY-REFRESH','invalid':False,'mode':'ok',
           'delta_sent':threading.Event(),'continue':threading.Event()}
    handler=type('SyntheticProvider',(fixture.Fake,),{'state':state})
    fake=ThreadingHTTPServer(('127.0.0.1',0),handler)
    upstream='http://127.0.0.1:'+str(fake.server_port)
    import codex
    import server
    import account_owner
    server.OWNER=account_owner.Pool('/data',factory=lambda p:codex.Connection(p,upstream,upstream+'/backend-api'))
    account_owner._INSTANCE=server.OWNER
threading.Thread(target=fake.serve_forever,daemon=True).start()
runpy.run_path('/app/pool_server.py',run_name='__main__')
