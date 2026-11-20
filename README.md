# gh-install

Paste a public **GitHub URL** and install plugins, skills, or MCP configs into **DeepSeek Harness**, **Claude Desktop**, **Grok**, or **ChatGPT**—with **no AI model in the loop**. The tool shallow-clones the repo and copies files using manifest names only, so you do not spend tokens asking a chatbot to “install this repo.”

## Quick start

1. Install **Python 3** and **git** on your PATH.
2. Clone this repository (or copy the folder) and run:

   ```bat
   gh-install.cmd --dry-run --host claude https://github.com/anthropics/skills/tree/main/skills/skill-creator
   ```

3. If the preview looks right, install:

   ```bat
   gh-install.cmd --host claude https://github.com/anthropics/skills/tree/main/skills/skill-creator
   ```

4. On first run, `hosts.json` is created from `hosts.example.json`. Edit paths if your apps live elsewhere.

Optional: add the folder containing `gh-install.cmd` to your user `PATH` so you can run `gh-install` from any terminal.

### One-liners per host

```bat
gh-install --host deepseek https://github.com/org/harness-plugin
gh-install --host claude     https://github.com/org/skill-repo
gh-install --host grok       https://github.com/org/grok-plugin
gh-install --host chatgpt    https://github.com/org/chatgpt-plugin
```

## Supported hosts

| Host | What it installs | Typical folders (Windows) |
|------|------------------|-------------------------|
| `deepseek` | Harness **plugins** (tree with `plugin.json` / marker), **skills** (`SKILL.md`), optional profile link | Plugins: `%USERPROFILE%\Documents\deepseek-harness\default-workspace\plugins`; skills: `%USERPROFILE%\.agents\skills` |
| `claude` | **Skills** (`SKILL.md`), **plugin** trees (`.cursor-plugin/plugin.json`), **MCP** (`mcp.json` merged into config) | Skills: `%USERPROFILE%\.claude\skills`; MCP: `%APPDATA%\Claude\claude_desktop_config.json` |
| `grok` | **Plugins**, **skills**, **MCP** (TOML merge) | `%USERPROFILE%\.grok\installed-plugins`, `%USERPROFILE%\.grok\skills`, `%USERPROFILE%\.grok\config.toml` |
| `chatgpt` | **Plugins**, **skills**, **MCP** (documented defaults) | `%APPDATA%\ChatGPT\plugins` (only if the desktop app is installed) |

The first successful run on your machine can record real paths in `hosts.json` so later installs skip rediscovery.

## GitHub URLs

Only `https://github.com/owner/repo` URLs are accepted.

Optional path suffixes:

- `/tree/<ref>` or `/tree/<ref>/<subdir>`
- `/blob/<ref>/<path>` (treated like a tree path for checkout)

Other hosts (GitLab, raw zip links, etc.) are rejected.

## Command-line flags

| Flag | Effect |
|------|--------|
| `--host <name>` | Required. One of: `deepseek`, `claude`, `grok`, `chatgpt`. |
| `--dry-run` | Print destination and file list; do not copy or merge configs. |
| `--replace` | Overwrite an existing destination folder without prompting. |

**Exit codes**

| Code | Meaning |
|------|---------|
| `0` | Success (or dry-run completed). |
| `1` | Error (bad URL, missing tool, install failure). |
| `2` | Destination already exists and `--replace` was not set (non-interactive). |

If the destination folder already exists and stdin is a TTY, the tool asks before replacing. In scripts, pass `--replace`.

## How detection works

The installer **does not** send repository source to a language model. After a shallow `git clone`, it looks only at **manifest file names**:

- `SKILL.md` → skill layout for the host’s skills directory
- `.cursor-plugin/plugin.json` or `plugin.json` → plugin layout
- `mcp.json` → MCP server entries

File bytes are copied as-is except for **MCP config**: `mcp.json` is read to **merge** new servers into the host’s existing MCP config (JSON for Claude/ChatGPT, TOML tables for Grok). Existing servers are not removed.

`.git` is never copied to the destination.

## `hosts.json`

- **Committed template:** `hosts.example.json` (portable `%USERPROFILE%` / `%APPDATA%` placeholders).
- **Local overrides:** `hosts.json` (gitignored). Created on first run; you can edit paths and the `why` notes.

## Requirements

- **Python 3** (stdlib only; no pip packages required)
- **git** (`git clone --depth 1`)

## License

MIT — see [LICENSE](LICENSE).