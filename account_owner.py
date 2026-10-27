"""Claude Code owns each login inside this app's declared claude-login share."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import threading
import usage
from accounts import Accounts


class Pool:
    def __init__(self, directory):
        self.root = Path(directory)
        self.logins = {}
        self.readers = {}
        self.lock = threading.RLock()
        self.cursor = 0
        self.renewing = set()
        self.renewed_at = {}
        self.accounts = Accounts(self.root, 'claude', self)

    def atomic(self, name, value):
        fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=self.root)
        try:
            with os.fdopen(fd, 'w') as output:
                os.fchmod(output.fileno(), 0o600)
                json.dump(value, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.root / name)
            directory = os.open(self.root, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def directory(self, ident):
        path = self.root if ident == 'legacy' else self.root / 'accounts' / ident
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        return path

    def has_legacy(self):
        return (self.root / '.credentials.json').exists()

    def status(self, ident):
        if ident not in self.readers:
            self.readers[ident] = usage.ConnectionReader(str(self.directory(ident)), os.environ.get('WIZARD_CLAUDE_USAGE_URL', usage.USAGE_URL))
        result = self.readers[ident].read()
        if result.get('status') == 'expired' and os.environ.get('WIZARD_CLAUDE_AUTO_RENEW', '1') != '0':
            import time
            with self.lock:
                if ident in self.renewing:
                    return {**result, 'status': 'renewing'}
                if time.monotonic() - self.renewed_at.get(ident, -1000) >= 600:
                    self.renewing.add(ident)
                    threading.Thread(target=self._renew, args=(ident,), daemon=True).start()
                    return {**result, 'status': 'renewing'}
        return result

    def _renew(self, ident):
        import server
        import time
        try:
            server.run_test(str(self.directory(ident)))
        finally:
            with self.lock:
                self.renewed_at[ident] = time.monotonic()
                self.renewing.discard(ident)
                self.readers.pop(ident, None)

    def connect(self, ident, lease=None):
        import server
        login = server.Login(str(self.directory(ident)), lease=lease)
        with self.lock:
            self.logins[ident] = login
        url = login.wait_url()
        if not url or not login.alive():
            self.cancel(ident)
            raise ValueError('Claude Code did not show a sign-in link')
        return {'url': url}

    def submit(self, ident, code):
        with self.lock:
            login = self.logins.get(ident)
            if login is None:
                raise ValueError('Unknown login')
        result = login.submit(code)
        with self.lock:
            self.logins.pop(ident, None)
            self.readers.pop(ident, None)
        # CLI success is not sufficient: verify the expected app-owned credential file exists.
        if result.get('ok') and not (self.directory(ident) / '.credentials.json').is_file():
            return {'ok': False}
        return result

    def cancel(self, ident):
        with self.lock:
            login = self.logins.pop(ident, None)
        if login is not None:
            login.close()

    def disconnect(self, ident):
        import server
        self.cancel(ident)
        result = subprocess.run([server.CLAUDE, 'auth', 'logout'], env=server.claude_env(str(self.directory(ident))),
            stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
        if result.returncode != 0 or (self.directory(ident) / '.credentials.json').exists():
            raise ValueError('Claude logout needs review')
        self.readers.pop(ident, None)

    def integration(self):
        # A provider login is not proof a host/alongside agent consumes the share.
        # WAM writes this read-only marker only after a declared share grant is compiled.
        marker = os.environ.get('WIZARD_CLAUDE_CONSUMER_STATE')
        if marker:
            try:
                state = json.loads(Path(marker).read_text())
                if state.get('share') == 'claude-login' and state.get('status') == 'mounted':
                    return {'status': 'registered', 'connected': True}
            except (OSError, ValueError):
                pass
        return {'status': 'unavailable', 'connected': False,
            'message': "Can't verify your agent's access. Ask it to connect the Claude app's claude-login share; sign-ins remain stored in this app."}

    def changed(self):
        pass

    def select(self):
        with self.lock:
            rows = self.accounts.rows()
            if not rows:
                return str(self.root)  # inference reports signed_out after request/grant validation
            offset = self.cursor % len(rows)
            self.cursor += 1
        import inference
        ordered = rows[offset:] + rows[:offset]
        for row in ordered:
            directory = str(self.directory(row['id']))
            try:
                inference.token(directory)
                return directory
            except inference.Fault:
                continue
        return str(self.directory(ordered[0]['id']))  # preserve structured expired/signed_out errors


_INSTANCE = None
_INIT = threading.Lock()


def instance():
    global _INSTANCE
    import server
    with _INIT:
        if _INSTANCE is None:
            _INSTANCE = Pool(server.CLAUDE_DIR)
    return _INSTANCE


class Local:
    @classmethod
    def accounts(cls, provider):
        if provider != 'claude':
            raise ValueError('Wrong provider')
        return instance().accounts.public()

    @classmethod
    def request(cls, provider, suffix='', body=None):
        if provider != 'claude':
            raise ValueError('Wrong provider')
        if suffix.startswith('/operations/') and body is None:
            return instance().accounts.poll(suffix.rsplit('/', 1)[-1])
        if suffix == '/operations' and isinstance(body, dict):
            return instance().accounts.act(body)
        return cls.accounts(provider)
