# Claude

Connect your Claude subscription (Pro or Max) to this Wizard server once. Your agents use it from here, and you can see how much of your usage is left.

## Connect Claude

1. Open Claude and press **Connect**.
2. Press the link it shows. It opens Claude's own sign-in page; use your phone or computer.
3. Sign in. Claude shows you a code. Copy it, paste it into the page, and press **Finish connecting**.
4. Press **Test**. It asks Claude for a one-word answer with the smallest model and shows OK or the error.

**Disconnect** signs this server out of Claude. Every agent using it stops until you connect again.

## Moving from AI Accounts

Claude uses the same private sign-in folder as AI Accounts (`wizard-ai-accounts-claude`), so if you were connected there you are connected here. Install Claude, check it shows Connected, then you can uninstall AI Accounts; the sign-in stays because Claude still uses it.

## How it works

- The sign-in is done by **Anthropic's official Claude Code** (pinned version, auto-update off), running inside this app. The app only starts its login and passes it the code you paste.
- Your plan and usage come from Anthropic's usage service, asked at most once a minute. The app never renews or copies the sign-in; Claude Code itself renews it when an agent (or **Test**) uses it.
- **Hermes Agent** (Wizard build) mounts the same folder. Its built-in **Claude Subscription DirectSDK (Experimental)** plugin by Nous Research runs the same official Claude Code. Pick it in Hermes' model picker to use your subscription.

## Privacy and access

Keep this app on your private network (Tailscale). Public domain exposure is off. The status and usage answer is box-only: requests that arrive through Tailscale Serve, a tunnel or a proxy are refused. On a server with a public IP, block port 8799 at the provider firewall. You can also set an optional page password at install.

## Personal use only

This is for using **your own** Claude subscription on **your own** server, through Anthropic's official app. If you build something for customers, use API keys instead.

## Uninstalling

Uninstalling Claude while Hermes Agent (or AI Accounts) is still installed keeps the sign-in. To remove it completely, press **Disconnect** first.
