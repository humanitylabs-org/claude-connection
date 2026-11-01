# Private storage hardening (source-only)

Reuse:
- Credential owner: REUSE: official Claude Code login/refresh — no parallel token writer or JSON reserialization.
- Login/runtime boundary: EXTEND: `server.claude_env`, login/test/logout subprocesses and `inference.run` — child umask077 and private runtime dirs.
- Metadata-only repair: EXTEND: server lifecycle — app-local `private_storage.py` fchmods the known login files, rejecting symlinks, without opening their contents. Included in Dockerfile.
- MCP front: EXTEND: `mcp/front.py` — fixed failure messages, regenerated inline compose.

The branch is based on the deployed public server lineage `0da65a4`. Oscar upstream's different server lacks current inference behavior; do not substitute it as a release base. No app-owned installed skill is edited.

## Verify

`python3 -m unittest -v test_private_storage`

`python3 test-inference.py`

`python3 test-usage.py`

All use synthetic credentials/fake CLI/loopback only. Storage tests prove restrictive creation, CLI-style atomic refresh under child umask077 even with permissive parent umask, metadata-only legacy0777 repair retaining canonical bytes, rejected symlink, every CLI subprocess's explicit umask and sanitized error/MCP output. Existing fake-CLI inference tests exercise short-lived config isolation/warm spares; usage tests prove the credential file is not rewritten. A real pinned official CLI refresh remains a separate approved canary; the synthetic refresh is not that proof.

Only the exact expected `OK` test reply is returned; arbitrary CLI error/success transcript is not reflected. Normal conversation replies still use the inference path. HTTP request/error logs and MCP failures omit raw exception text. Account/plan status remains available; raw tokens are not an API.

## Boundary and release gate

**0700/0600 is not encryption or same-UID isolation.** Runtipi recursively chmods app-data `a+rwx` on lifecycle operations. It can widen a running mount after app startup; startup/post-CLI repair is not continuous protection. The official CLI may also change persistence behavior in future releases; run the pinned-image canary before release.

A private named volume/tmpfs or lifecycle exclusion requires an explicit compatible migration, not an empty-volume mount. Preserve original bytes/unknown fields, unattended official refresh, existing grants and a single writer. Broker custody with distinct app UIDs needs actual agent Docker/sudo fencing before claiming model-tool separation. Warm spares must be drained on later credential generation changes. Prove current-generation rollback and recovery before any plaintext removal. No migration, CLI login/logout, model switch, token revocation or live restart is performed here. Heavy/container/browser tests run via forum admission.
