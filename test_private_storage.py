"""Synthetic CLI writer tests. No installed CLI or credentials are used."""
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import private_storage
import server


class PrivateStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root/'config'
        self.work = self.root/'work'
        self.settings = patch.multiple(server, CLAUDE_DIR=str(self.config), WORK=self.work)
        self.settings.start()
        self.old_umask = os.umask(0)

    def tearDown(self):
        os.umask(self.old_umask)
        self.settings.stop()
        self.temp.cleanup()

    def test_create_cli_refresh_and_legacy_restart_preserve_bytes(self):
        private_storage.harden_login(self.config)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o700)
        raw = b'{ "claudeAiOauth":{}, "unknown":"retain original bytes" }\n'
        for name in ('.credentials.json','.claude.json'):
            (self.config/name).write_bytes(raw)
            (self.config/name).chmod(0o777)
        self.config.chmod(0o777)
        private_storage.harden_login(self.config)
        for p in self.config.iterdir():
            self.assertEqual(p.read_bytes(), raw)
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
        # Same file-create/replace semantics as an official CLI refresh, child umask even if parent is 000.
        code = "from pathlib import Path; import os; p=Path(os.environ['CLAUDE_CONFIG_DIR']); t=p/'.new'; t.write_bytes(b'synthetic-rotated'); t.replace(p/'.credentials.json')"
        subprocess.run([sys.executable,'-c',code],env=server.claude_env(),check=True,umask=0o077)
        self.assertEqual((self.config/'.credentials.json').stat().st_mode & 0o777,0o600)
        private_storage.harden_login(self.config)
        self.assertEqual((self.config/'.credentials.json').read_bytes(),b'synthetic-rotated')
        self.assertEqual(self.work.stat().st_mode & 0o777,0o700)
        self.assertEqual((self.work/'home').stat().st_mode & 0o777,0o700)

    def test_login_symlink_rejected_without_mutating_target(self):
        private_storage.directory(self.config)
        outside=self.root/'outside'; outside.write_bytes(b'synthetic'); outside.chmod(0o644)
        (self.config/'.credentials.json').symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'^Private storage unavailable.$'):
            private_storage.harden_login(self.config)
        self.assertEqual(outside.stat().st_mode & 0o777,0o644)

    def test_test_error_output_and_exception_logs_are_sanitized(self):
        sentinel='SYNTHETIC-DO-NOT-EXPOSE'
        completed=subprocess.CompletedProcess([],1,json.dumps({'is_error':True,'result':sentinel}),sentinel)
        with patch.object(server.subprocess,'run',return_value=completed) as run:
            code,body=server.run_test()
        self.assertEqual(code,502)
        self.assertNotIn(sentinel,json.dumps(body))
        self.assertEqual(run.call_args.kwargs['umask'],0o077)
        out=io.StringIO()
        with contextlib.redirect_stderr(out):
            try: raise RuntimeError(sentinel)
            except RuntimeError: server.Server.handle_error(None,None,None)
        self.assertNotIn(sentinel,out.getvalue())

    def test_every_cli_subprocess_has_explicit_umask(self):
        import ast
        for filename in ('server.py','inference.py'):
            tree=ast.parse(Path(filename).read_text())
            calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr in ('run','Popen')]
            self.assertTrue(calls)
            for call in calls:
                self.assertTrue(any(k.arg=='umask' and isinstance(k.value,ast.Constant) and k.value.value==0o077 for k in call.keywords), filename+':'+str(call.lineno))

    def test_mcp_errors_are_sanitized(self):
        spec=importlib.util.spec_from_file_location('test_front', Path(__file__).parent/'mcp/front.py')
        assert spec is not None and spec.loader is not None
        front=importlib.util.module_from_spec(spec);spec.loader.exec_module(front)
        def fail():raise RuntimeError('SYNTHETIC-DO-NOT-EXPOSE')
        front.TOOLS['synthetic']=({},fail)
        answer=front.rpc({'method':'tools/call','id':1,'params':{'name':'synthetic'}})
        self.assertNotIn('SYNTHETIC-DO-NOT-EXPOSE',json.dumps(answer))
        self.assertTrue(answer['result']['isError'])


if __name__ == '__main__': unittest.main()
