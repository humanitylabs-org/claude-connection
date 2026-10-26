# Read-only by design: signing in, adding, reconnecting and removing subscriptions are owner actions on the
# Claude page. The MCP only reports the wizard.ai-connection/2 answer (overall status, plan, usage and one row per
# subscription), never a token.
# Box-only: a call that came through Tailscale Serve, a tunnel or a proxy is refused; agents reach this
# MCP on the app network (http://wizard-claude:8799/mcp), which adds none of these headers.

PROXY_HEADERS = ("tailscale-user-login", "x-forwarded-for", "forwarded", "x-real-ip")


@tool("connection_status", "Claude subscription status on this Wizard: connected / not_connected / expired / error, "
      "the plan (e.g. Max 20x), the account label, current usage limits (percent used, percent left and reset time "
      "for the session and weekly windows), and `accounts`: one row per Claude subscription (the original Claude Code "
      "sign-in first, then every subscription added in the app, any number) with its own status and usage. "
      "Read-only; never returns a token.")
def connection_status():
    if any(k in PROXY_HEADERS or k.startswith("cf-") for k in REQUEST.get()):
        raise PermissionError("box-only: call this MCP from the server (app network), not through the tailnet or a proxy")
    headers = {}
    auth = REQUEST.get().get("authorization")
    if auth:
        headers["Authorization"] = auth  # the page password (Basic), forwarded unchanged
    _, raw = http("GET", "/api/connection", None, headers, timeout=15)
    d = json.loads(raw)
    if d.get("status") == "not_connected":
        d["next"] = ("Ask the owner to open the Claude app, press Sign in, open the sign-in link, then paste the code "
                     "there. Never ask for the code or a token in chat.")
    elif d.get("status") == "expired":
        d["next"] = ("Ask the owner to open the Claude app and press Sign in again on the expired subscription "
                     "(or + Add to add another subscription).")
    elif (d.get("error") or {}).get("code") in ("unreachable", "not_configured", "login_rejected"):
        d["next"] = ("The Claude app can't reach this agent's dashboard (error.message; the page shows the agent address). "
                     "On a box where Wizard runs next to your own Hermes, run `wam alongside` and then any `wam app update ...` "
                     "it prints (re-points the app at this agent and restarts it); otherwise `wam app update wizard-claude`. "
                     "Check again; tell the owner in plain words if it still fails.")
    elif d.get("status") == "error" and (d.get("error") or {}).get("code") == "limit":
        d["next"] = "That subscription hit its limit; the owner can add another Claude subscription with + Add in the Claude app."
    return d
