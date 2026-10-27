# Claude

> **Contribution fork — upstream is canonical.** Wizard OS releases install
> [oscarhenrycollins/claude-connection](https://github.com/oscarhenrycollins/claude-connection).
> The app-owned multi-subscription port is contributed there as
> [upstream PR #4](https://github.com/oscarhenrycollins/claude-connection/pull/4),
> rebuilt on Oscar's current code rather than this fork's older divergent main.
> Follow upstream for release/onboarding work. Do not pin new boxes to this fork's
> main or treat a fork-only login fix as shipped. Existing pins/data are not changed
> by this documentation notice.

## Source and fork

Release fork of [oscarhenrycollins/claude-connection](https://github.com/oscarhenrycollins/claude-connection). Miguel's repository remains canonical in the public Wizard App Index; this fork is installed explicitly by repository and does not automatically publish to that index. Engine images are built from these sources in `humanitylabs-org/wizard-app-store`. The fork uses host port 18799 by default to avoid the legacy demo port; the engine remains private behind its front service.

Connect your Claude subscription once; every agent on the box uses it, and you see how much is left.

A [Wizard app](https://www.aiwizards.com/wizard-apps) (System App) and the first per-provider **AI connection** app (decision #61: one connection app per AI provider). Open its page, press **Connect**, sign in with Claude, paste the code, and press **Test**. The sign-in runs Anthropic's official Claude Code login and stays in this app's `${APP_DATA_DIR}/data/claude`, mounted at `/claude` with the existing `CLAUDE_CONFIG_DIR=/claude` semantics. `wizard.md` exports it as `shares: [{id: claude-login, path: claude}]`. Hermes Agent declares `mounts: [{app: wizard-claude, share: claude-login, path: /claude}]`; App Manager supplies that bind mount only while the owner grants access. The official Claude Code client, not Hermes core, reads the login.

## App-data and share migration (0.3.0)

The engine image remains pinned to the unchanged 0.2.2 digest; 0.3.0 changes the recipe and ownership contract, not engine code. Keep the app-data directory writable by UID/GID 1000 and private to the owner. Back up the Claude app's app-data, not a Docker named volume. Sharing the whole config folder preserves Claude Code's refresh lock; consumers must use a compatible official CLI.

Upgrade with the App Manager implementation of Wizard OS decisions #79/#80. It stops callers and copies the legacy `wizard-ai-accounts-claude` volume once into the Claude app's `data/claude`, preserving ownership and modes and leaving the old volume intact. Do not start old AI Accounts or a second box against a copied rotating login. Stock Runtipi alone does not perform this migration or compile share grants; a direct compose upgrade without the App Manager can present an empty login. Grant/revoke access through App Manager; never hard-code another app's app-data path in a consumer recipe.

## Contract: `wizard.ai-connection/2`

`GET /api/connection` (box-only, never a token):

```json
{"contract": "wizard.ai-connection/2", "provider": "claude", "name": "Claude",
 "status": "connected", "plan": "Max 20x", "account": "you@example.com",
 "usage": {"fetchedAt": "…", "limits": [{"id": "session:…", "label": "Session", "usedPercent": 12, "remainingPercent": 88, "resetsAt": "…"}], "paid": null},
 "error": null}
```

`status` is `connected | not_connected | expired | error`. Usage comes from Anthropic's OAuth usage endpoint, cached 60 s; on an outage the last good reading is kept for up to 30 min with `error.code: unreachable`. The token is never refreshed here (refresh tokens are single-use; a refresh would sign agents out), so an expired token reads `expired` until Claude Code renews it. Rows match the Wizard Agent Service's `/wizard/ai-usage` shape exactly.

## Connection Router (`wizard.ai-connection/2`, decision #65)

Implements [spec/CONNECTION_ROUTER.md](https://github.com/humanitylabs-org/wizard-os/blob/main/spec/CONNECTION_ROUTER.md).
The `/1` status/plan/account/usage fields keep their existing semantics; `/2` adds
`models: [{id, label, tier, abilities}]` (context size is optional and not guessed).
These are configured model allowlists, not entitlement probes. Unavailable models
fail closed; there is no account, model or provider fallback.

`POST /api/infer` accepts `{model, system?, messages, max_tokens?, stream?, abilities?}`.
Messages are nonempty lists of exact `{role: "user"|"assistant", content: string}`.
Only streaming is supported (`stream: true` or omitted), with SSE `delta` text,
then `done` carrying the **provider-reported effective model** and usage. Errors use
`signed_out|expired|limit|unreachable|provider_error`. Missing done is failure;
discard provisional text on an error. No arbitrary tools, profile, URL or headers
are accepted in the body. No inference request/response content is logged or saved.

### Router grants and exposure

`WIZARD_GRANTS_FILE` uses the router's configuration shape:

```json
{"enforce": true, "incoming": [{"from": "wizard-connection-router", "sha256": "<64 lowercase hex SHA-256 of the opaque router grant>"}]}
```

The router sends that opaque token in `X-Wizard-Grant`; configure its `outgoing`
entry under this provider's app ID. Known grants belonging to other apps are
refused. Missing/malformed grant files fail closed. With no file, or `enforce:false`,
unknown grants are **report-only**, matching the permissions rollout: network peers
are not authenticated as the router. `X-Wizard-App` is never authentication.
Do not expose this port to untrusted peers until enforcement is enabled. Browser
Origin and proxy-identity headers are refused even with a valid grant. A recognized router grant also permits discovery when the owner page has a password;
unknown/report-only grants do not bypass that password. The owner
page password is not an inference credential. Keep owner routes behind their
existing access controls; router traffic stays on the private app network.

### Verification and release

Run the offline tests below; they use only loopback fixtures, never real sign-ins.
Container builds/tests must run on the release builder, not the control-plane VPS.
This source PR does not publish engine images or change the existing pinned image
digests in compose. Before store rollout, the maintainer must build/publish these
sources and update the engine digest; merging metadata alone does not deploy `/2`.

### Claude implementation

`models.json` (override: `WIZARD_CLAUDE_MODELS_FILE`) owns the model/tier list:
Haiku 4.5 / fast, Sonnet 5 / standard, Opus 5.5 / frontier. All advertise
`text`, `streaming`, and opt-in `web_search`.

Inference reads only this app's `/claude/.credentials.json` access credential;
it never refreshes or copies the refresh chain. An explicitly service-supplied
`CLAUDE_CODE_OAUTH_TOKEN` can be used instead and is passed only in child-process
environment, never persisted. In that mode discovery reports credential presence,
not verified validity; the inference result still validates authentication/model.
Each `claude -p` runs in fresh private HOME/config/cwd directories under
`WIZARD_CLAUDE_WORK_DIR`, removed in finally. Safe mode, empty setting sources,
explicit system prompt, disabled slash commands, empty strict MCP configuration,
no sessions and an empty tool allowlist prevent ambient agent context. Only an
explicit `web_search` ability enables `WebSearch`; no shell, file or other tools.
A single user message is passed as stdin text; multi-message histories are an explicit
JSON transcript in stdin, not replayed/persisted CLI sessions. The bundled CLI remains
pinned to 2.1.296. No fallback model is supplied.

Limits: 256 KiB input, 128 messages, 2 active calls, 120 s generation deadline,
4 MiB CLI stream, 1 MiB JSON line. `max_tokens` (1..32768, default 8192) is a
conservative local visible-UTF-8-byte guard plus final provider output-token check,
**not an upstream billing cap**. CLI process groups are killed on deadline/error/
disconnect and temporary directories removed. Deltas are provisional; done requires
successful completion, matching final text, usage, no permission denials and exactly
the approved model in CLI `modelUsage` (also checking assistant-reported models).

```sh
python3 test-usage.py
python3 test-inference.py -v
python3 mcp/inline.py --check
```

## Files

- `wizard.md`: what the app is and what it gives the agent (spec: wizard.md v0.2).
- `runtipi/`: stock Runtipi `config.json` and `docker-compose.yml` (engine pinned by digest).
- `mcp/`: a read-only MCP (`connection_status`) inlined into the compose file by `python3 mcp/inline.py`.
- `server.py`, `usage.py`, `static/`, `Dockerfile`: the page image `ghcr.io/humanitylabs-org/wizard-claude`, built and published from `humanitylabs-org/wizard-app-store` `images/wizard-claude`.
- `test-usage.py`, `test-container.sh`: the unit and container tests CI runs before publishing.
- `SKILL.md`: the skill the agent loads when this app is installed.
- `.github/workflows/publish.yml`: manual dispatch only; do not publish this fork under the canonical app ID.

Replaces the Claude part of [AI Accounts](https://github.com/oscarhenrycollins/ai-accounts). Personal use of your own subscription on your own server; products for other people should use API keys.
