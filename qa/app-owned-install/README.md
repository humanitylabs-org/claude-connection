# Disposable app-owned login acceptance

This rig runs **native Linux amd64 on forum**, outside the owner's installed apps. It exercises the actual source-package compose recipes (pinned engine, MCP/page front, app-data initializer), their real accounts HTTP API, and current **stock Hermes AIAgent**, not a substituted agent client.

The upstream provider and official-CLI interfaces are **synthetic fixtures**. Passing this rig is not proof of a paid Claude/OpenAI account login, provider compliance, actual live refresh or full App Manager grant/migration installation.

## Stage

Under a fresh `/srv/work/app-owned-login-<unique>` directory, stage these source trees at the indicated names:

- `claude`: this PR's source package.
- `chatgpt`: oscarhenrycollins/chatgpt-connection#4's candidate source.
- `official-plugins/claude-subscription-directsdk`: NousResearch/hermes-official-plugins#214's provider.
- `service/hermes-plugin/wizard-os/dashboard`: humanitylabs-org/wizard-agent-service#204's dashboard helpers.
- `wam`: humanitylabs-org/wizard-app-manager#265's full worktree.
- `acceptance`: a copy of this folder.

Submit `bash acceptance/remote.sh`, with that fresh directory as cwd, via `wizard_heavy_submit` on host `forum`. It downloads public toolchains and a fresh stock-Hermes checkout into the disposable directory, runs the complete Claude provider suite, runs metadata readback tests, installs/tests the apps, and runs the exact new App Manager pre-start guard under its pinned Bun. Logs and `summary.json` go under `proof`. Provider fixture data stays there; the child HOME and Hermes homes are isolated. Compose cleanup names only `owned-proof-claude` and `owned-proof-chatgpt`; never use these names for a live deployment.

Do not reuse an existing `proof/installed-*` directory: fresh means absent app-data. Keep the failed run and use a new staging root for a retry. No registry, release pins, owner's services, secrets or live app-data are changed.

## What is asserted

- Real Docker Compose parsing: source/data mounts are on the engine, app-data initializer is required, runtime remains non-root/read-only.
- Fresh inventory is empty; two synthetic sign-ins persist beneath app-data in distinct opaque account directories.
- The app does not say a missing agent is connected just because sign-in succeeded.
- Engine restart preserves both subscriptions.
- Expiring one synthetic account offers Reconnect while the sibling remains usable; app re-sign-in restores it.
- Actual stock Hermes answers using the installed app. Claude's actual loaded provider reads both granted directory identities over two requests and produces exact nonsecret consumer readback. ChatGPT's agent has only the app's local bearer; refresh material remains in app-data.
- Disposable containers are removed in `finally`.

## Gates not replaced

Full App Manager fresh-install/grant/revocation acceptance; existing-box credential handover and draft grant-migration #215; standard/restricted generated-runtime multi-account mount/projection support; authenticated HTTP readback; installed-shell Appearance/Back tests; authorized real test subscriptions and live refresh. Keep the contribution draft until its claimed acceptance scope is proven. Release pins remain the release owner's decision.
