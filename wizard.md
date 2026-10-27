---
wizard: 0.2
id: wizard-claude
name: Claude
type: external
category: system
tags: [security]
version: 0.3.0
summary: Connect one or more Claude subscriptions; every agent on the box uses them, and you see how much each has left.
icon: icon.png
license: MIT
source: https://github.com/oscarhenrycollins/claude-connection
runtime:
  kind: runtipi
  config: runtipi/config.json
  compose: runtipi/docker-compose.yml
  package:
    mode: source
    root: .
mcp:
  path: /mcp
  port: 8799
  transport: streamable-http
skill: SKILL.md
view:
  path: /
  port: 8799
provides:
- ai-connection
- claude-subscription
shares:
- id: claude-login
  path: claude
health: /health
---

# Claude

Sign in with your subscription in this connection app. Add as many subscriptions as you need on one accounts page. Sign-in and renewal live in private app-data, not your agent. The page reports provider status separately from whether the agent can use it, so an alongside box cannot mistake an unused local login for a working agent connection.

See `docs/APP_OWNED_LOGIN.md` for the design, onboarding integration, exclusive migration requirements, and evidence boundaries. Existing agent-owned subscriptions are not silently copied or deleted.
