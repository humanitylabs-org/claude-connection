---
wizard: 0.2
id: wizard-claude
name: Claude
type: external
category: system
tags: [security]
version: 0.2.0
summary: Connect your Claude subscription once; every agent on the box uses it, and you see how much is left.
icon: icon.png
license: MIT
source: https://github.com/humanitylabs-org/claude-connection
runtime:
  kind: runtipi
  config: runtipi/config.json
  compose: runtipi/docker-compose.yml
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
health: /health
---

# Claude

Connect your Claude Pro or Max subscription once on the Claude page, and every agent on this Wizard uses it. The sign-in runs Anthropic's official Claude Code login and stays in a private shared volume; agents never see the token.

This is a Wizard AI connection app (`wizard.ai-connection/2`): `GET /api/connection` reports whether Claude is connected, your plan, and your current usage limits, and the MCP tool `connection_status` gives agents the same answer. It replaces the Claude part of AI Accounts and reuses its sign-in volume, so an existing sign-in shows Connected straight away.
