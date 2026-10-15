# Claude

Connect your Claude subscription once; every agent on the box uses it, and you see how much is left.

A [Wizard app](https://www.aiwizards.com/wizard-apps) (System App) and the first per-provider **AI connection** app (decision #61: one connection app per AI provider). Open its page, press **Connect**, sign in with Claude, paste the code, and press **Test**. The sign-in runs Anthropic's official Claude Code login and stays in the private shared volume `wizard-ai-accounts-claude`, which agent apps (Hermes Agent from Wizard Apps) mount at `/claude`. Agents never see the token.

## Contract: `wizard.ai-connection/1`

`GET /api/connection` (box-only, never a token):

```json
{"contract": "wizard.ai-connection/1", "provider": "claude", "name": "Claude",
 "status": "connected", "plan": "Max 20x", "account": "you@example.com",
 "usage": {"fetchedAt": "…", "limits": [{"id": "session:…", "label": "Session", "usedPercent": 12, "remainingPercent": 88, "resetsAt": "…"}], "paid": null},
 "error": null}
```

`status` is `connected | not_connected | expired | error`. Usage comes from Anthropic's OAuth usage endpoint, cached 60 s; on an outage the last good reading is kept for up to 30 min with `error.code: unreachable`. The token is never refreshed here (refresh tokens are single-use; a refresh would sign agents out), so an expired token reads `expired` until Claude Code renews it. Rows match the Wizard Agent Service's `/wizard/ai-usage` shape exactly.

## Files

- `wizard.md`: what the app is and what it gives the agent (spec: wizard.md v0.2).
- `runtipi/`: stock Runtipi `config.json` and `docker-compose.yml` (engine pinned by digest).
- `mcp/`: a read-only MCP (`connection_status`) inlined into the compose file by `python3 mcp/inline.py`.
- `server.py`, `usage.py`, `static/`, `Dockerfile`: the page image `ghcr.io/humanitylabs-org/wizard-claude`, built and published from `humanitylabs-org/wizard-app-store` `images/wizard-claude`.
- `test-usage.py`, `test-container.sh`: the unit and container tests CI runs before publishing.
- `SKILL.md`: the skill the agent loads when this app is installed.
- `.github/workflows/publish.yml`: every push to `main` re-publishes to the index.

Replaces the Claude part of [AI Accounts](https://github.com/oscarhenrycollins/ai-accounts). Personal use of your own subscription on your own server; products for other people should use API keys.
