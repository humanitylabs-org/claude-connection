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


## Explicit fresh-install initialization (staged, not released)

Reuse: EXTEND the app-owned recipe initializer; REUSE existing app credential writers and installed runtime identity 1000:1000. No view/shared shell function changes.

Docker-created bind mounts hide the image-owned directory. The recipe now gates engine startup on two bounded one-shots: root with only CHOWN prepares an **empty root-owned** mount, then 1000:1000 with ALL capabilities dropped validates metadata through nofollow directory FDs. Both have no network, read-only rootfs and no-new-privileges. Validation mounts the exact data directory read-only. This split needs no DAC_OVERRIDE, DAC_READ_SEARCH, FOWNER, SETUID or SETGID. Existing runtime services retain their original nonroot/read-only/cap-drop contract.

Existing runtime-owned data is not chmoded, chowned, parsed or rewritten by initialization. The validator rejects foreign ownership, symlinks, hard-linked regular files, special files and device-crossing trees. Partial existing runtime-owned trees pass without creating missing subdirectories; normal app writers create them privately. There is no recursive chmod/chown and no UID fallback. All normal app data paths and grants remain unchanged.

A populated root-owned directory, wrong UID/GID, or invalid link fails closed. This can expose an already-incompatible historical install: stop that app through an approved maintenance window, make a byte-preserving/ownership-preserving backup, classify the exact canonical store, and stage a separately approved migration. Do not fix this by recursive chown or by substituting an empty volume. No backup or automatic migration is performed by the initializer.

For an empty 0:0 root only, mode is set0700 before ownership is handed to1000:1000. A failed chown restores the original empty-root mode while it is still0:0. If ownership transfer succeeded but subsequent validation/startup fails, retain the prepared directory; do not blindly roll ownership back after a runtime may have written. Rollback is an approved stopped-app restore of the current canonical generation and its recorded metadata, not a stale credential copy. Returning to the old recipe is not a data rollback.

The inline helper comes from prepare_private_data.py; refresh with python3 tools/inline-private-data.py. The pinned official Python image already supplies stdlib Python, so no helper image build and no APP_SOURCE_DIR support are required. Run test_private_initialization.py with PyYAML in the test interpreter. Its mocked ownership failures are source regressions, not real cross-UID evidence; the separate forum container fixture exercises genuine0:0 to1000:1000 and1101:2202 ownership transitions.

On an old WAM release the recipe can initialize fresh storage, but the old manager's later recursive a+rwx still defeats private modes; compatibility is not continuous privacy. The patched WAM lifecycle must be separately approved. Container nofollow checks cannot detect a host bind-source symlink already resolved by the privileged Docker daemon; host installer/daemon trust remains necessary. No encryption, same-UID isolation, Docker isolation or live migration is claimed.
