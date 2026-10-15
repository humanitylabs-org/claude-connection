# Read-only by design: connecting, disconnecting and the test call are owner actions on the Claude page.
# The MCP only reports the wizard.ai-connection/1 answer (status, plan, account label, usage), never a token.
# Box-only: a call that came through Tailscale Serve, a tunnel or a proxy is refused; agents reach this
# MCP on the app network (http://wizard-claude:8799/mcp), which adds none of these headers.

PROXY_HEADERS = ("tailscale-user-login", "x-forwarded-for", "forwarded", "x-real-ip")


@tool("connection_status", "Claude subscription status on this Wizard: connected / not_connected / expired / error, "
      "the plan (e.g. Max 20x), the account label, and current usage limits (percent used, percent left and reset time "
      "for the session and weekly windows, plus any extra-usage spend). Read-only; never returns a token.")
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
        d["next"] = ("Ask the owner to open the Claude app, press Connect, sign in, paste the code, then press Test. "
                     "Never ask for the code or a token in chat.")
    elif d.get("status") == "expired":
        d["next"] = ("Ask the owner to open the Claude app and press Test (Claude Code renews the sign-in); "
                     "if that fails, Connect again.")
    return d
