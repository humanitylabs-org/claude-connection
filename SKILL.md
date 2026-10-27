---
name: wizard-claude
description: Use when checking the installed Claude connection app. Sign-in belongs to the app, not the agent.
---
# Claude

- Open the installed app for Sign in, + Add, Reconnect and Remove. Never run `hermes auth add` to onboard this app.
- Read `GET /api/accounts` for app-owned subscriptions and separate `integration` consumer status. `GET /api/connection` must not claim a working agent if only a local provider login exists.
- Never print, copy into chat, or refresh provider tokens. Never silently migrate the agent's existing credential pool. Re-sign-in or an exclusive stopped-owner handover is required.
- Request an owner grant for the declared `claude-login` share. Never guess or bind the host Claude login. Preserve the whole directory and CLI locks.
- Preserve all subscriptions, page controls, icons, usage reporting and missing-agent diagnostics. Source and canonical release repository: `oscarhenrycollins/claude-connection`.
- Candidate installation and migration prerequisites are in `docs/APP_OWNED_LOGIN.md`. Synthetic tests do not certify a live provider account.
