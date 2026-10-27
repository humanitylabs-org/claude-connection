"""Claude multi-account owner + actual accounts HTTP server; synthetic CLI and usage provider."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import server
import account_owner
import pool_server


@contextmanager
def serving(srv):
    thread=threading.Thread(target=srv.serve_forever,kwargs={'poll_interval':.01},daemon=True);thread.start()
    try: yield 'http://127.0.0.1:'+str(srv.server_port)
    finally: srv.shutdown();srv.server_close();thread.join(3)


class Usage(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        raw=json.dumps({'five_hour':{'utilization':10,'resets_at':'2030-01-01T00:00:00Z'}}).encode()
        self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)


class OwnedClaudeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.cli=self.root/'claude';shutil.copyfile(Path(__file__).parent/'tests/login_cli.py',self.cli);self.cli.chmod(0o755)
        self.backend=ThreadingHTTPServer(('127.0.0.1',0),Usage);self.bctx=serving(self.backend);self.upstream=self.bctx.__enter__()
        self.env=patch.dict(os.environ,{'WIZARD_CLAUDE_USAGE_URL':self.upstream+'/usage','WIZARD_CLAUDE_AUTO_RENEW':'0'});self.env.start()
        self.settings=patch.multiple(server,CLAUDE=str(self.cli),CLAUDE_DIR=str(self.root/'app-data'/'claude'),WORK=self.root/'work');self.settings.start()
        self.pool=account_owner.Pool(self.root/'app-data'/'claude');account_owner._INSTANCE=self.pool
        self.srv=ThreadingHTTPServer(('127.0.0.1',0),pool_server.Handler);self.sctx=serving(self.srv);self.base=self.sctx.__enter__()
    def tearDown(self):
        self.pool.accounts.close();account_owner._INSTANCE=None
        self.sctx.__exit__(None,None,None);self.bctx.__exit__(None,None,None)
        self.settings.stop();self.env.stop();self.tmp.cleanup()
    def call(self,path,body=None,headers=None):
        req=Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json',**(headers or {})})
        try:r=urlopen(req,timeout=8)
        except HTTPError as e:r=e
        with r:return r.status,json.loads(r.read())
    def wait(self,job,challenge=False):
        until=time.monotonic()+4
        while time.monotonic()<until:
            code,result=self.call('/api/operations/'+job['id'])
            self.assertEqual(code,200)
            if result['status']!='running' or challenge and result['url']:return result
            time.sleep(.01)
        self.fail('Operation timed out')
    def add(self,label):
        code,job=self.call('/api/operations',{'action':'add','label':label,'confirmed':True},{'X-Wizard-Account-Action':'1'});self.assertEqual(code,200)
        challenge=self.wait(job,True);self.assertTrue(challenge['url'].startswith('https://claude.ai/'))
        code,submitted=self.call('/api/operations',{'action':'submit','operation':job['id'],'code':'SYNTHETIC#ONLY'},{'X-Wizard-Account-Action':'1'});self.assertEqual(code,200)
        result=self.wait(job);self.assertEqual(result['status'],'succeeded');return result
    def test_two_subscriptions_live_in_app_data_and_restart_no_agent_credentials(self):
        first=self.add('Work');second=self.add('Home')
        code,out=self.call('/api/accounts');self.assertEqual((code,out['owner'],len(out['accounts'])),(200,'app',2))
        self.assertTrue(all(r['status']=='connected' for r in out['accounts']))
        self.assertFalse(out['integration']['connected'])
        self.assertIn("Can't verify",out['integration']['message'])
        self.assertNotIn('synthetic-refresh-only',json.dumps(out))
        for job in (first,second):
            folder=self.pool.directory(job['target']);self.assertEqual(folder.parent,self.pool.root/'accounts')
            self.assertTrue((folder/'.credentials.json').is_file());self.assertEqual(folder.stat().st_mode&0o777,0o700)
        self.assertNotEqual(self.pool.select(),self.pool.select())
        restored=account_owner.Pool(self.pool.root);self.assertEqual(len(restored.accounts.rows()),2);restored.accounts.close()
        code,out=self.call('/api/connection');self.assertEqual(out['status'],'error')
    def test_expiry_offers_reconnect_remove_does_not_touch_other_account(self):
        one=self.add('One');two=self.add('Two');path=self.pool.directory(one['target'])/'.credentials.json'
        creds=json.loads(path.read_text());creds['claudeAiOauth']['expiresAt']=1;path.write_text(json.dumps(creds))
        code,out=self.call('/api/accounts');self.assertEqual(out['accounts'][0]['status'],'expired');self.assertTrue(out['accounts'][0]['actions']['reconnect'])
        code,job=self.call('/api/operations',{'action':'remove','target':one['target'],'confirmed':True},{'X-Wizard-Account-Action':'1'});self.assertEqual(code,200)
        self.assertEqual(self.wait(job)['status'],'succeeded');self.assertEqual([r['id'] for r in self.pool.accounts.rows()],[two['target']])
        self.assertTrue((self.pool.directory(two['target'])/'.credentials.json').is_file())
    def test_cross_origin_and_unconfirmed_actions_denied(self):
        self.assertEqual(self.call('/api/operations',{'action':'add','confirmed':True})[0],403)
        self.assertEqual(self.call('/api/operations',{'action':'add','confirmed':True},{'X-Wizard-Account-Action':'1','Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.call('/api/operations',{'action':'add'},{'X-Wizard-Account-Action':'1'})[0],409)


if __name__=='__main__':unittest.main(verbosity=2)
