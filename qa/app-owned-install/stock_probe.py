"""Actual stock Hermes AIAgent consuming installed app data; provider/CLI synthetic."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

provider=sys.argv[1]
root=Path(sys.argv[2]).resolve()
base=sys.argv[3]
home=root/'proof'/('stock-home-'+provider)
home.mkdir(mode=0o700,parents=True,exist_ok=True)
os.environ['HERMES_HOME']=str(home)
os.environ['HERMES_SKIP_UPDATE_CHECK']='1'
os.environ['HERMES_DISABLE_SUDO']='1'
sys.path.insert(0,str(root/'stock-hermes'))
if provider=='claude':
    source=root/'proof'/'installed-claude'/'data'/'claude'
    plugin=home/'plugins'/'claude-subscription-directsdk-experimental'
    shutil.copytree(root/'official-plugins'/'claude-subscription-directsdk',plugin,dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git','__pycache__','tests','evals'))
    cli=root/'acceptance'/'cli_fixture.py';cli.chmod(0o755)
    os.environ['CLAUDE_SUBSCRIPTION_DIRECTSDK_CONFIG_DIR']=str(source)
    os.environ['CLAUDE_SUBSCRIPTION_DIRECTSDK_COMMAND']=str(cli)
    os.environ['PROBE_CONSUMED_PATH']=str(root/'proof'/'consumed-claude-accounts.txt')
    name='claude-subscription-directsdk-experimental';model='claude-sonnet-5'
    kwargs={'provider':name,'api_mode':'chat_completions','command':str(cli),
            'api_key':'external-process','base_url':'process://'+name}
else:
    source=root/'proof'/'installed-chatgpt'/'data'
    bearer=json.loads((source/'gateway-token.json').read_text())['token']
    name='openai-codex';model='gpt-5.6-sol'
    kwargs={'provider':name,'api_mode':'codex_responses','api_key':bearer,'base_url':base+'/v1'}
    os.environ['HERMES_CODEX_BASE_URL']=base+'/v1'
(home/'config.yaml').write_text('model:\n  provider: '+name+'\n  default: '+model+'\nplugins:\n  enabled: []\n')
from run_agent import AIAgent
answers=[]
agent=AIAgent(model=model,quiet_mode=True,max_iterations=2,enabled_toolsets=[],
              skip_context_files=True,skip_memory=True,**kwargs)
for i in range(2):
    result=agent.run_conversation('Say one short word.',system_message='You are an isolated acceptance test. No tools.')
    answer=result.get('final_response','')
    assert ('app-owned-' in answer if provider=='claude' else 'hello' in answer),str(result)
    answers.append(answer)
if getattr(agent,'client',None) and hasattr(agent.client,'close'):agent.client.close()
assert not any('synthetic-refresh-only' in p.read_text(errors='replace') or 'SYNTHETIC-ONLY-REFRESH' in p.read_text(errors='replace')
               for p in home.glob('*.json')),'Provider refresh material escaped app-data'
if provider=='claude':
    consumed=(root/'proof'/'consumed-claude-accounts.txt').read_text().splitlines()
    assert len(set(consumed))>=2,consumed
    helper=root/'service/hermes-plugin/wizard-os/dashboard/app_owned_login.py'
    spec=importlib.util.spec_from_file_location('consumer_readback',helper)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    state=mod.claude_status()
    assert state['status']=='mounted' and state['in_use'] and len(state['accountIds'])==2,state
    assert state['ownerId']==json.loads((source/'owner.json').read_text())['id']
    print(json.dumps({'provider':provider,'stock_agent_answers':answers,'consumed_account_ids':sorted(set(consumed)),
                      'actual_provider_readback':state,'provider_refresh_material_in_agent':False}))
else:
    print(json.dumps({'provider':provider,'stock_agent_answers':answers,'agent_credential':'app-local bearer only',
                      'provider_refresh_material_in_agent':False}))
