#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd)
case "$ROOT" in /srv/work/app-owned-login-*) ;; *) printf 'Refusing non-disposable worker root\n' >&2; exit 2;; esac
mkdir -p "$ROOT/tools" "$ROOT/proof/worker-home" "$ROOT/tmp" "$ROOT/uv-cache"
export HOME="$ROOT/proof/worker-home" TMPDIR="$ROOT/tmp" UV_CACHE_DIR="$ROOT/uv-cache"
export UV_PYTHON_INSTALL_DIR="$ROOT/tools/python"
# Public downloads only; this isolated HOME has no owner login, registry auth or SSH keys.
if [ ! -x "$ROOT/tools/uv-x86_64-unknown-linux-gnu/uv" ]; then
  curl -fsSL https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz -o "$ROOT/tools/uv.tar.gz"
  tar -xzf "$ROOT/tools/uv.tar.gz" -C "$ROOT/tools"
fi
UV="$ROOT/tools/uv-x86_64-unknown-linux-gnu/uv"
if [ ! -d "$ROOT/stock-hermes/.git" ]; then
  git clone --depth=1 https://github.com/NousResearch/hermes-agent.git "$ROOT/stock-hermes"
fi
"$UV" sync --project "$ROOT/stock-hermes" --python 3.14 --no-dev
"$UV" pip install --python "$ROOT/stock-hermes/.venv/bin/python" pytest pytest-asyncio
export HERMES_AGENT_REPO="$ROOT/stock-hermes" PYTHONPATH="$ROOT/stock-hermes"
export HERMES_HOME="$ROOT/proof/unit-test-home"
printf 'Stock Hermes commit: '; git -C "$ROOT/stock-hermes" rev-parse HEAD
"$UV" --version
uname -a
rc=0
(
 cd "$ROOT/official-plugins/claude-subscription-directsdk"
 "$ROOT/stock-hermes/.venv/bin/python" -m pytest -q
) >"$ROOT/proof/canonical-plugin-suite.log" 2>&1 || rc=1
"$ROOT/stock-hermes/.venv/bin/python" "$ROOT/service/hermes-plugin/wizard-os/dashboard/test_app_owned_login.py" >"$ROOT/proof/service-readback.log" 2>&1 || rc=1
python3 "$ROOT/acceptance/run.py" || rc=1
# Exact new WAM pre-start guard, under the project's pinned Bun version.
if [ ! -x "$ROOT/tools/bun-linux-x64/bun" ]; then
  curl -fsSL https://github.com/oven-sh/bun/releases/download/bun-v1.3.0/bun-linux-x64.zip -o "$ROOT/tools/bun.zip"
  unzip -q "$ROOT/tools/bun.zip" -d "$ROOT/tools"
fi
(
 cd "$ROOT/wam"
 "$ROOT/tools/bun-linux-x64/bun" install --frozen-lockfile
 "$ROOT/tools/bun-linux-x64/bun" test packages/backend/src/modules/docker/__tests__/app-owned-claude.test.ts
) >"$ROOT/proof/wam-guard.log" 2>&1 || rc=1
exit "$rc"
