# 🛠️ Troubleshooting

Need the quick path? See the [main README](../README.md).

## ❌ Python or git not found

Run `setup.cmd` once. It checks both tools and prints download links.

- **Python**: https://www.python.org/downloads/ (check **Add python.exe to PATH**)
- **Git**: https://git-scm.com/download/win

Open a **new** terminal after installing.

## ❌ `gh-install` is not recognized

Either:

1. Run from the repo folder: `gh-install.cmd https://github.com/owner/repo`
2. Or run `setup.cmd` and answer **Y** to add this folder to your user PATH, then open a new terminal.

**Undo PATH change (Windows):** Settings → System → About → Advanced system settings → Environment Variables → edit **User** `Path` → remove the `gh-install` folder entry.

## ❌ git clone failed (private repo)

This tool only installs **public** `https://github.com/...` repos. For private repos, use SSH or a personal access token yourself, then point `gh-install` at the local folder (dry-run only for local dirs in some builds) or clone manually into the destination.

## ❌ Destination exists / exit code 2

An install folder with the same name is already on disk.

- Interactive terminal: answer the prompt to replace.
- Scripts / Cursor agents: pass `--replace`.

## ❌ `--host is required` in CI

When stdin is not a terminal, you must pass `--host deepseek|claude|grok|chatgpt`.

## 📂 Wrong install folder

Edit `hosts.json` next to `gh-install.py` (copy from `hosts.example.json` if missing). Paths support `%USERPROFILE%` and `%APPDATA%`.

Run `gh-install --where` to print resolved folders.

## 🔄 App does not see the new plugin or skill

Quit and reopen the desktop app after install (see `gh-install --help-hosts` for per-app hints).