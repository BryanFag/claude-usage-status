# Claude Usage Status (unofficial)

See how much of your Claude plan you have used without leaving VS Code. The status bar shows two progress bars, one for the 5-hour session limit and one for the weekly limit:

`✻ 5h ▕██░░░░░░▏ 14%   7d ▕███████▏ 98%`

> This is an unofficial extension. It is not affiliated with, endorsed by, or supported by Anthropic. Claude is a trademark of Anthropic.

## Features

- **Two bars in the status bar**: the 5-hour session and the 7-day window, each with its exact percentage.
- **Details on hover**: a larger bar for each limit, how long until it resets, and the local reset time.
- **Automatic refresh** every 3 minutes. Click the status bar item, or run **Claude Usage: Refresh**, to refresh right away.
- **English and Portuguese**: follows the VS Code display language.

## Requirements

- Claude Code signed in with a Claude subscription (Pro or Max) on the same machine.
- Linux or Windows. On macOS, Claude Code keeps the login in the Keychain instead of `~/.claude/.credentials.json`, so this extension cannot read it yet.

## How it works

The extension reads the access token Claude Code saves in `~/.claude/.credentials.json` and sends it to `https://api.anthropic.com/api/oauth/usage`, the same request the `/usage` command makes. The response has the utilization and reset time of each limit.

- The token is read again on every refresh, used only in that request, and never stored, logged, or sent anywhere else.
- The extension never renews the token. Renewing it could sign you out of Claude Code, so when the token expires the bar keeps the last values, adds a ⚠ and waits for Claude Code to renew it.
- No telemetry.

## Caveats

- `/api/oauth/usage` is not a documented API. Anthropic can change or remove it at any time, and the bars will stop working until the extension is updated.
- Anthropic states that the OAuth login of Claude subscriptions is meant for Claude Code and Anthropic's own apps. This extension only reads usage numbers and sends no prompts, but it still uses that login outside Claude Code. Review [Anthropic's terms](https://code.claude.com/docs/en/legal-and-compliance) and decide for yourself before using it.

## License

[MIT](LICENSE)
