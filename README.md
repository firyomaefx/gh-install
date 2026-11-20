# gh-install — GitHub plugin & skill installer (no AI tokens)

Also known as **easygithubinstall** — use the [mobile web handoff](web/easygithubinstall/README.md) on iPhone/Android to paste a link and get a QR/command for your desktop.

**Paste a public GitHub link** and install **plugins**, **skills**, or **MCP servers** into **Claude Desktop**, **Grok**, **DeepSeek Harness**, or **ChatGPT**—without burning tokens in chat. This Windows CLI shallow-clones the repo and copies files using **manifest names only** (`SKILL.md`, `plugin.json`, `mcp.json`).

| Repo | Link |
|------|------|
| GitHub | https://github.com/firyomaefx/gh-install |
| Cursor Origin | https://origin.cursor.com/ttrg/gh-install |

---

## 📍 Run where?

| Step | **Where you run it** | Example |
|------|----------------------|---------|
| **One-time setup** | Inside the cloned `gh-install` folder | Double-click `setup.cmd` or `setup.cmd` in cmd |
| **Install a repo** | Any **PowerShell**, **cmd**, or **Windows Terminal** (after PATH) | `gh-install https://github.com/org/repo` |
| **From repo folder** | Same folder as `gh-install.cmd` | `gh-install.cmd --host claude <url>` |
| **Do not run** | Inside Claude, Grok, ChatGPT, or DeepSeek chat windows | Use a real terminal instead |

See exact disk paths: `gh-install --where`

---

## 📱 Use on your phone

Open **Easy GitHub Install** on iOS or Android: [easygithubinstall.stump-vinyl.workers.dev](https://easygithubinstall.stump-vinyl.workers.dev) (demo) or [easygithubinstall.ipo-hunter.workers.dev](https://easygithubinstall.ipo-hunter.workers.dev) (your account). Paste your GitHub URL, then scan the QR or copy `gh-install "…"` on your computer. Redeploy: `cd web/easygithubinstall && npm run deploy` (requires `wrangler login` or `CLOUDFLARE_API_TOKEN`).

---

## ⚡ Paste-and-go flow (no AI tokens)

```bat
git clone https://github.com/firyomaefx/gh-install.git
cd gh-install
setup.cmd          :: Windows
# ./setup.sh       :: macOS / Linux (chmod +x setup.sh first)
```

**`setup` runs `gh-install --scan`** — checks your disk for Claude, Grok, DeepSeek, and ChatGPT desktop folders. **No chat model is called.**

Then paste a link. The menu lists **only detected apps** (press `a` to see all):

```bat
gh-install --scan
gh-install <paste GitHub URL>
```

## ⚡ Install in 60 seconds

Then paste a link (interactive host menu):

```bat
gh-install --dry-run https://github.com/anthropics/skills/tree/main/skills/skill-creator
gh-install https://github.com/anthropics/skills/tree/main/skills/skill-creator
```

Or name the host up front:

```bat
gh-install --host claude https://github.com/org/your-skill-repo
gh-install --host deepseek https://github.com/org/harness-plugin
gh-install --host grok https://github.com/org/grok-plugin
gh-install --host chatgpt https://github.com/org/chatgpt-plugin
```

---

## 🧩 Supported hosts

| | Host | Open this app after | Installs | Typical folder on PC |
|---|------|---------------------|----------|----------------------|
| 🐋 | **deepseek** | DeepSeek Harness | Harness **plugins**, **skills**, profile link | `%USERPROFILE%\Documents\deepseek-harness\default-workspace\plugins` · skills: `%USERPROFILE%\.agents\skills` |
| 🟤 | **claude** | Claude Desktop | **Skills**, plugin trees, **MCP** merge | `%USERPROFILE%\.claude\skills` · MCP: `%APPDATA%\Claude\claude_desktop_config.json` |
| ⚡ | **grok** | Grok | **Plugins**, **skills**, **MCP** (TOML) | `%USERPROFILE%\.grok\installed-plugins` |
| 💬 | **chatgpt** | ChatGPT desktop | **Plugins**, **skills**, **MCP** | `%APPDATA%\ChatGPT\plugins` (if app installed) |

Details per app: `gh-install --help-hosts`

First run creates **`hosts.json`** from [`hosts.example.json`](hosts.example.json). Edit paths if your apps live elsewhere.

---

## 🔗 Paste GitHub links

- Only **`https://github.com/owner/repo`**
- Optional: `/tree/<ref>`, `/tree/<ref>/<subdir>`, `/blob/<ref>/<path>`
- **Several URLs** in one command install in order
- GitLab, zip links, and other hosts are **rejected**

---

## 🎛️ Flags & exit codes

| Flag | What it does |
|------|----------------|
| `--host <name>` | Target app (`deepseek`, `claude`, `grok`, `chatgpt`). Optional on an interactive terminal—shows a menu. |
| `--dry-run` | List destination + files; no writes |
| `--replace` | Overwrite existing folder without asking |
| `--where` | Print install folders for every host |
| `--scan` | Detect installed desktop apps; update `hosts.json` (local only, **no tokens**) |
| `--help-hosts` | Per-host install types and restart hints |

| Exit | Meaning |
|------|---------|
| `0` | OK (including dry-run) |
| `1` | Bad URL, missing git/python, install error |
| `2` | Destination exists; use `--replace` in scripts |

If a folder already exists and you are at a real terminal, the tool asks before replacing.

**Scripts / CI:** always pass `--host` and use `--replace` when overwriting.

---

## ❓ FAQ

**How do I install a DeepSeek harness plugin from GitHub?**  
Clone gh-install, run `setup.cmd`, then `gh-install --host deepseek https://github.com/owner/repo`.

**How do I add a Claude Desktop skill from a GitHub repo?**  
`gh-install --host claude https://github.com/owner/repo/tree/main/skills/my-skill`

**Can I avoid pasting repos into ChatGPT and paying token costs?**  
Yes—this tool never sends repo source to an LLM. It only clones with git and copies files.

**Where do files land on my PC?**  
`gh-install --where` (paths come from `hosts.json`).

**Does this work on Mac or Linux?**  
Yes: use `setup.sh` and `python3 gh-install.py`. Paths are chosen from [`hosts.example.json`](hosts.example.json) for `windows`, `darwin`, or `linux`.

**Can it install into Chrome or a browser chat?**  
No. This targets **desktop app folders** only, not browser extensions.

**ChatGPT host does nothing?**  
Install the ChatGPT **desktop** app first, or edit `hosts.json` to match your layout.

More: [docs/INSTALL.md](docs/INSTALL.md) · [Token verification](docs/VERIFY.md)

---

## 🔬 How it works

1. **`git clone --depth 1`** into a temp folder  
2. Detect layout from **file names only** (`SKILL.md`, `plugin.json`, `.cursor-plugin/plugin.json`, `mcp.json`, DeepSeek `cordis.patch.yml`)  
3. **Copy** bytes as-is (no summarizing, no model)  
4. **MCP:** merge new servers into existing JSON/TOML configs—existing servers stay  

`.git` is never copied to your app folders.

---

## 📦 Requirements

- **Windows** (cmd / PowerShell)
- **Python 3** (stdlib only)
- **git** on PATH

---

## 📄 License

MIT — see [LICENSE](LICENSE).