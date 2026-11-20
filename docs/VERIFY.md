# Token usage verification

This document verifies that **gh-install does not use LLM tokens** for the install path, compared with asking a chatbot to install the same GitHub repo.

## Install pipeline (no model)

```text
Paste URL → git clone (shallow) → read manifest file names only → copy / MCP merge on disk
```

No HTTP calls to Claude, OpenAI, Grok, DeepSeek chat APIs, or Cursor agent APIs are made by `gh-install`.

## Token comparison

| Activity | Uses LLM tokens? |
|----------|------------------|
| `gh-install <url>` after `setup` + optional `--scan` | **No** |
| `gh-install --dry-run` | **No** |
| `gh-install --scan` (local path probes) | **No** |
| Edit `hosts.json` | **No** |
| Ask an AI to “install this GitHub repo” in chat | **Yes** (repo content + tool loops) |
| Private repo via your own `git` credentials | **No LLM** (network/git only) |

## What is read locally (not sent to any model)

| Input | Scope |
|-------|--------|
| Repo tree during clone | Git client only |
| Detection | Filenames: `SKILL.md`, `plugin.json`, `.cursor-plugin/plugin.json`, `mcp.json`, `cordis.patch.yml` |
| MCP merge | Parses `mcp.json` on disk; merges into host config |

File bytes are copied as-is. The full repo is never uploaded to an LLM.

## Non-token costs

- Network for `git clone`
- Disk space for installed copies
- Your time in a terminal (not inside chat UIs)

## Paste → pick app → install

1. Run `setup.cmd` (Windows) or `setup.sh` (macOS/Linux).
2. `gh-install --scan` sets `found` on each host by checking local paths (no AI).
3. `gh-install <github-url>` shows a menu of **detected** desktop apps (or `a` for all).
4. Install uses **zero tokens** for steps 2–4.

Browser/Chrome chat or extensions are **out of scope**; this tool targets desktop app folders only.