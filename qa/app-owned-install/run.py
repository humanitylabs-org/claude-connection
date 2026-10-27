"""Disposable native-amd64 source-package install + actual stock-Hermes consumer proof.

All provider accounts and the Claude CLI are synthetic. This proves installation,
ownership, expiry UX, two inventories, persistence and agent transport, not a paid
provider's login, refresh policy or deployment to an owner's Wizard.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path(os.environ.get('WIZARD_LOGIN_PROOF_ROOT', Path(__file__).resolve().parent.parent)).resolve()
PROOF=ROOT/'proof'
PROOF.mkdir(exist_ok=True)
RESULT={'kind':'disposable source-package install; synthetic providers; actual stock Hermes',
        'safety':'no live app data or owner credentials mounted','checks':{}}


def run(label,argv,cwd=ROOT,env=None,timeout=1200):
    path=PROOF/(label+'.log')
    with path.open('w') as f:
        p=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    RESULT['checks'][label]={'exit_code':p.returncode,'log':path.name}
    (PROOF/'summary.json').write_text(json.dumps(RESULT,indent=2))
    if p.returncode:raise RuntimeError(label+' failed; see '+str(path))


def call(base,path,body=None):
    req=Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={
        'Content-Type':'application/json','X-Wizard-Account-Action':'1'})
    try:r=urlopen(req,timeout=30)
    except HTTPError as e:r=e
    with r:
        raw=r.read()
        if r.status!=200:raise RuntimeError(str((r.status,path,raw[:300])))
        return json.loads(raw)


def wait(base,job,challenge=False):
    deadline=time.monotonic()+35
    while time.monotonic()<deadline:
        out=call(base,'/api/operations/'+job['id'])
        if out['status']!='running' or challenge and out.get('url'):return out
        time.sleep(.1)
    raise RuntimeError('Timed out waiting for account operation')


def signin(app,base,action='add',ident=None):
    payload={'action':action,'confirmed':True,'label':'Synthetic '+str(time.monotonic_ns())}
    if ident:payload['target']=ident
    job=call(base,'/api/operations',payload)
    if app=='claude':
        challenge=wait(base,job,True)
        assert challenge.get('url','').startswith('https://claude.ai/'),challenge
        call(base,'/api/operations',{'action':'submit','operation':job['id'],'code':'SYNTHETIC#ONLY'})
    out=wait(base,job)
    assert out['status']=='succeeded',out
    return out['target']


def install(app):
    installed=PROOF/('installed-'+app)
    if installed.exists():raise RuntimeError('Fresh install requires absent data: '+str(installed))
    installed.mkdir(mode=0o700)
    project='owned-proof-'+app
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','DOCKER_CONFIG','TMPDIR')}
    env.update(APP_SOURCE_DIR=str(ROOT/app),APP_DATA_DIR=str(installed))
    engine='wizard-'+app+'-engine'
    frontend='wizard-'+app
    port=8799 if app=='claude' else 8801
    overlay={'services':{engine:{'volumes':[str(ROOT/'acceptance')+':/fixtures:ro'],
        'command':['python3','/fixtures/fixture_boot.py',app],
        'environment':{'WIZARD_CLAUDE_AUTO_RENEW':'0','WIZARD_CLAUDE_CLAUDE':'/fixtures/cli_fixture.py',
                       'WIZARD_CLAUDE_HERMES_PASSWORD':'','WIZARD_CHATGPT_HERMES_PASSWORD':''}},
        frontend:{'ports':['127.0.0.1::'+str(port)]}}}
    override=PROOF/(app+'-synthetic-only.json');override.write_text(json.dumps(overlay,indent=2))
    compose=['docker','compose','-p',project,'-f',str(ROOT/app/'runtipi/docker-compose.yml'),'-f',str(override)]
    try:
        run(app+'-compose-up',compose+['up','-d','--wait','--wait-timeout','90'],env=env)
        address=subprocess.check_output(compose+['port',frontend,str(port)],env=env,text=True).strip()
        base='http://'+address
        deadline=time.monotonic()+30
        while True:
            try:empty=call(base,'/api/accounts');break
            except Exception:
                if time.monotonic()>deadline:raise
                time.sleep(.2)
        assert empty['owner']=='app' and len(empty['accounts'])==0,empty
        ids=[signin(app,base),signin(app,base)]
        state=call(base,'/api/accounts')
        assert len(state['accounts'])==2 and len(set(ids))==2,state
        assert all(r['status']=='connected' for r in state['accounts']),state
        assert state['integration']['connected'] is False,'Absent agent must not appear connected'
        (PROOF/(app+'-two-subscriptions.json')).write_text(json.dumps(state,indent=2))
        source=installed/'data'/('claude' if app=='claude' else '')
        catalog=json.loads((source/'accounts.json').read_text())
        assert {r['id'] for r in catalog}==set(ids)
        filename='.credentials.json' if app=='claude' else 'connection.json'
        assert all((source/'accounts'/ident/filename).is_file() for ident in ids)
        run(app+'-compose-restart',compose+['restart',engine],env=env)
        deadline=time.monotonic()+20
        while True:
            try:state=call(base,'/api/accounts');break
            except Exception:
                if time.monotonic()>deadline:raise
                time.sleep(.2)
        assert {r['id'] for r in state['accounts']}==set(ids),state
        path=source/'accounts'/ids[0]/filename
        auth=json.loads(path.read_text())
        if app=='claude':auth['claudeAiOauth']['expiresAt']=0
        else:auth['status']='expired'
        path.write_text(json.dumps(auth))
        expired=call(base,'/api/accounts')
        row=next(r for r in expired['accounts'] if r['id']==ids[0])
        assert row['status']=='expired' and row['actions']['reconnect'],row
        assert next(r for r in expired['accounts'] if r['id']==ids[1])['status']=='connected'
        (PROOF/(app+'-expired-reconnect.json')).write_text(json.dumps(expired,indent=2))
        signin(app,base,'reconnect',ids[0])
        run(app+'-stock-agent',[str(ROOT/'stock-hermes/.venv/bin/python'),ROOT/'acceptance/stock_probe.py',app,ROOT,base],env=env,timeout=180)
        cid=subprocess.check_output(compose+['ps','-q',engine],env=env,text=True).strip()
        mounts=subprocess.check_output(['docker','inspect','--format','{{json .Mounts}}',cid],text=True)
        (PROOF/(app+'-installed-mounts.json')).write_text(mounts)
        RESULT['checks'][app+'-install']={'fresh_inventory':True,'two_app_owned_signins':True,
            'restart_persists':True,'expired_offers_reconnect':True,'absent_agent_not_false_connected':True,
            'stock_agent_answers':True,'synthetic_provider':True}
    finally:
        subprocess.run(compose+['logs','--no-color'],env=env,stdout=(PROOF/(app+'-container.log')).open('w'),stderr=subprocess.STDOUT)
        subprocess.run(compose+['down','--remove-orphans'],env=env,check=True)
        RESULT['checks'][app+'-cleanup']='only disposable compose project stopped and removed'
        (PROOF/'summary.json').write_text(json.dumps(RESULT,indent=2))


if __name__=='__main__':
    (ROOT/'acceptance/cli_fixture.py').chmod(0o755)
    try:
        assert os.uname().machine=='x86_64','Native amd64 required'
        for app in ('claude','chatgpt'):
            scripts=['test-recipe.py','test-accounts.py','test-pool.py']+(['test-usage.py'] if app=='claude' else ['test-chatgpt.py'])+['test-inference.py']
            for script in scripts:run(app+'-'+script.removesuffix('.py'),['python3',script],cwd=ROOT/app)
            run(app+'-mcp',['python3','mcp/inline.py','--check'],cwd=ROOT/app)
        for app in ('claude','chatgpt'):install(app)
        RESULT['complete']=True
    except Exception:
        RESULT['complete']=False
        RESULT['failure']=traceback.format_exc()
        print(RESULT['failure'],flush=True)
    finally:(PROOF/'summary.json').write_text(json.dumps(RESULT,indent=2))
    print(json.dumps(RESULT,indent=2),flush=True)
    sys.exit(0 if RESULT.get('complete') else 1)
