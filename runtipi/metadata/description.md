# Claude

Connect your Claude subscriptions (Pro or Max) to this Wizard server: one, or as many as you have. Your agents use them from here, and you can see how much of each one's usage is left.

## Connect Claude

1. Open Claude and press **Sign in** (or **+ Add** for another subscription).
2. Press **Open sign-in**. It opens Claude's own sign-in page; use your phone or computer.
3. Sign in. Claude shows you a code. Paste it into the page and press **Submit**.

Each subscription gets its own row with its plan and usage bars. **Manage** on a row offers **Reconnect** and **Remove** for subscriptions you added here.

## Your original sign-in

If this server was already connected (Claude 0.1, or AI Accounts), that sign-in stays as the first row and keeps working. When it needs to sign in again, the row shows **Sign in again**, which opens the original Claude Code sign-in page (Connect, paste the code, Test, Disconnect). On an agent without the Wizard OS account broker, **Sign in** opens that same page.

## Moving from AI Accounts

Claude uses the same private sign-in folder as AI Accounts (`wizard-ai-accounts-claude`), so if you were connected there you are connected here. Install Claude, check it shows Ready, then you can uninstall AI Accounts; the sign-in stays because Claude still uses it.

## How it works

- The original sign-in is done by **Anthropic's official Claude Code** (pinned version, auto-update off), running inside this app. Claude Code itself renews it when an agent (or **Test**) uses it.
- Added subscriptions sign in inside your agent with **Hermes' own Claude sign-in** (`hermes auth add anthropic`) and live in its credential pool, which moves to the next subscription when one hits its limit. This app only starts the sign-in and passes the code you paste; it never holds those tokens.
- Plan and usage come from Anthropic's usage service, asked at most once a minute.

## Privacy and access

Keep this app on your private network (Tailscale). Public domain exposure is off. The status and usage answer is box-only: requests that arrive through Tailscale Serve, a tunnel or a proxy are refused. Subscription changes are accepted only from this page itself. On a server with a public IP, block port 8799 at the provider firewall. You can also set an optional page password at install.

## Personal use only

This is for using **your own** Claude subscriptions on **your own** server, through Anthropic's official sign-in. If you build something for customers, use API keys instead.

## Uninstalling

Uninstalling Claude keeps every sign-in: the original one stays in its shared folder while Hermes Agent (or AI Accounts) is installed, and added subscriptions stay in your agent. To remove one, use **Remove** (added subscriptions) or **Disconnect** on the original sign-in page first.
