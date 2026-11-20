#!/usr/bin/env python3
"""Install a GitHub repo into a local host by copying files.

Detection uses manifest file names only. File bytes are copied as-is.
mcp.json is the one file whose JSON is read, and only to merge server
entries into the host MCP config without dropping servers already there.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

TOOL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = TOOL_DIR / "hosts.json"
EXAMPLE_PATH = TOOL_DIR / "hosts.example.json"
HOSTS = ("deepseek", "claude", "grok", "chatgpt")
PATH_KEYS = ("plugins", "skills", "mcp_config", "profile_package")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
REF_RE = re.compile(r"^[A-Za-z0-9._~+-]+$")

DEFAULT_HOSTS = {
    "version": 1,
    "hosts": {
        "deepseek": {
            "found": False,
            "plugins": r"%USERPROFILE%\Documents\deepseek-harness\default-workspace\plugins",
            "skills": r"%USERPROFILE%\.agents\skills",
            "profile_package": r"%USERPROFILE%\.dsh\profiles\desktop\package.json",
            "marker": "cordis.patch.yml",
            "why": "Edit paths after you install DeepSeek Harness.",
        },
        "claude": {
            "found": True,
            "plugins": r"C:\Users\User\.claude\plugins\local",
            "skills": r"C:\Users\User\.claude\skills",
            "mcp_config": r"C:\Users\User\AppData\Roaming\Claude\claude_desktop_config.json",
            "mcp_format": "json",
            "why": (
                "Claude Desktop is installed. claude_desktop_config.json already "
                "has mcpServers. SKILL.md installs go to .claude\\skills, which "
                "already holds skills. A plugin.json tree is copied under "
                ".claude\\plugins\\local."
            ),
        },
        "grok": {
            "found": True,
            "plugins": r"C:\Users\User\.grok\installed-plugins",
            "skills": r"C:\Users\User\.grok\skills",
            "mcp_config": r"C:\Users\User\.grok\config.toml",
            "mcp_format": "toml",
            "why": (
                "Grok is installed. Local plugins already live in "
                ".grok\\installed-plugins and skills in .grok\\skills. MCP "
                "servers are [mcp_servers.*] tables in .grok\\config.toml."
            ),
        },
        "chatgpt": {
            "found": False,
            "plugins": r"%APPDATA%\ChatGPT\plugins",
            "skills": r"%APPDATA%\ChatGPT\skills",
            "mcp_config": r"%APPDATA%\ChatGPT\mcp_config.json",
            "mcp_format": "json",
            "why": "ChatGPT desktop default paths.",
        },
    },
}


class InstallError(Exception):
    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def expand_config_paths(hosts: dict) -> None:
    for cfg in hosts.values():
        if not isinstance(cfg, dict):
            continue
        for key in PATH_KEYS:
            value = cfg.get(key)
            if isinstance(value, str):
                cfg[key] = os.path.expandvars(value)


def seed_config() -> None:
    if EXAMPLE_PATH.exists():
        shutil.copy(EXAMPLE_PATH, CONFIG_PATH)
        return
    CONFIG_PATH.write_text(json.dumps(DEFAULT_HOSTS, indent=2) + "\n", encoding="utf-8")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        seed_config()
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    hosts = data.get("hosts")
    if not isinstance(hosts, dict) or any(name not in hosts for name in HOSTS):
        raise InstallError(f"host config is missing a host: {CONFIG_PATH}")
    expand_config_paths(hosts)
    return hosts


def parse_github_url(url: str) -> dict:
    raw = url.strip()
    if not raw or any(ch in raw for ch in "\\\n\r\t "):
        raise InstallError(f"refusing URL: {url}")
    parts = urlsplit(raw)
    if parts.scheme != "https" or parts.netloc.lower() != "github.com":
        raise InstallError(f"refusing URL: {url}")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise InstallError(f"refusing URL: {url}")
    segs = [seg for seg in parts.path.split("/") if seg]
    if len(segs) < 2:
        raise InstallError(f"refusing URL: {url}")
    owner, repo = segs[0], segs[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not NAME_RE.fullmatch(owner) or not NAME_RE.fullmatch(repo):
        raise InstallError(f"refusing URL: {url}")
    if owner in {".", ".."} or repo in {".", ".."}:
        raise InstallError(f"refusing URL: {url}")
    ref = None
    subpath = ""
    blob = False
    if len(segs) > 2:
        if segs[2] not in {"tree", "blob"} or len(segs) < 4:
            raise InstallError(f"refusing URL: {url}")
        blob = segs[2] == "blob"
        ref = segs[3]
        if not REF_RE.fullmatch(ref) or ref in {".", ".."}:
            raise InstallError(f"refusing URL: {url}")
        rest = segs[4:]
        if any(seg in {"", ".", ".."} for seg in rest):
            raise InstallError(f"refusing URL: {url}")
        subpath = "/".join(rest)
        if blob and not subpath:
            raise InstallError(f"refusing URL: {url}")
    return {
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "subpath": subpath,
        "blob": blob,
        "url": raw,
    }


def confirm(label: str, replace: bool, dry_run: bool) -> None:
    if dry_run:
        print(f"exists: {label}")
        print("dry-run: a real run stops here unless --replace is set")
        return
    if replace:
        return
    if sys.stdin.isatty():
        answer = input(f"{label} already exists. Replace it? [y/N] ")
        if answer.strip().lower() in {"y", "yes"}:
            return
        print("not replaced", file=sys.stderr)
        raise InstallError("replace declined", 2)
    print(
        f"{label} already exists. Re-run with --replace.",
        file=sys.stderr,
    )
    raise InstallError("replace required", 2)


def list_files(root: Path) -> list[str]:
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name != ".git"]
        for name in filenames:
            if name == ".git":
                continue
            full = Path(dirpath) / name
            found.append(full.relative_to(root).as_posix())
    found.sort()
    return found


def ignore_git(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name == ".git"}


def _rmtree(path: Path) -> None:
    def onerror(func, target, _exc) -> None:
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onerror=onerror)


def copy_tree(src: Path, dest: Path) -> int:
    if dest.exists():
        _rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=ignore_git, symlinks=True)
    return len(list_files(dest))


def marker_kind(rel: Path) -> str | None:
    if rel.name == "cordis.patch.yml":
        return "deepseek-plugin"
    if rel.name == "plugin.json" and rel.parent.name == ".cursor-plugin":
        return "cursor-plugin"
    if rel.name == "plugin.json":
        return "plugin"
    if rel.name == "SKILL.md":
        return "skill"
    if rel.name == "mcp.json":
        return "mcp"
    return None


def marker_root(rel: Path, kind: str) -> Path:
    if kind == "cursor-plugin":
        return rel.parent.parent
    return rel.parent


def shallowest(paths: list[Path]) -> list[Path]:
    kept: list[Path] = []
    for path in sorted(set(paths), key=lambda item: (len(item.parts), item.as_posix())):
        if any(path != earlier and earlier in path.parents for earlier in kept):
            continue
        if any(path != earlier and earlier == Path(".") for earlier in kept):
            continue
        kept.append(path)
    return kept


def is_inside(child: Path, parent: Path) -> bool:
    if parent == Path("."):
        return True
    return child == parent or parent in child.parents


def detect(root: Path) -> dict:
    plugins: list[tuple[Path, str]] = []
    skills: list[Path] = []
    mcp_files: list[Path] = []
    for rel_text in list_files(root):
        rel = Path(rel_text)
        kind = marker_kind(rel)
        if kind in {"deepseek-plugin", "cursor-plugin", "plugin"}:
            plugins.append((marker_root(rel, kind), kind))
        elif kind == "skill":
            skills.append(rel.parent)
        elif kind == "mcp":
            mcp_files.append(rel)
    by_root: dict[Path, set[str]] = {}
    for path, kind in plugins:
        by_root.setdefault(path, set()).add(kind)
    plugin_roots = shallowest(list(by_root))
    skill_roots = [
        path
        for path in shallowest(skills)
        if not any(is_inside(path, plugin) for plugin in plugin_roots)
    ]
    kinds: list[str] = []
    for path in plugin_roots:
        present = by_root[path]
        if "deepseek-plugin" in present:
            kinds.append("deepseek-plugin")
        elif "cursor-plugin" in present:
            kinds.append("cursor-plugin")
        else:
            kinds.append("plugin")
    if skill_roots:
        kinds.append("skill")
    if mcp_files:
        kinds.append("mcp")
    # Preserve first-seen order while dropping duplicates.
    ordered: list[str] = []
    for kind in kinds:
        if kind not in ordered:
            ordered.append(kind)
    return {
        "kinds": ordered,
        "plugins": [(path, _plugin_label(by_root[path])) for path in plugin_roots],
        "skills": skill_roots,
        "mcp": mcp_files,
    }


def _plugin_label(present: set[str]) -> str:
    if "deepseek-plugin" in present:
        return "deepseek-plugin"
    if "cursor-plugin" in present:
        return "cursor-plugin"
    return "plugin"


def unit_name(repo: str, rel: Path) -> str:
    if rel == Path("."):
        return repo
    name = rel.name
    if not name or name in {".", ".."} or any(ch in name for ch in '<>:"/\\|?*'):
        raise InstallError(f"refusing destination name: {name}")
    return name


def abs_unit(root: Path, rel: Path) -> Path:
    if rel == Path("."):
        return root
    return root / rel


def load_mcp_servers(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise InstallError(f"mcp.json is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InstallError("mcp.json is not a JSON object")
    if isinstance(data.get("mcpServers"), dict):
        servers = data["mcpServers"]
    elif isinstance(data.get("mcp_servers"), dict):
        servers = data["mcp_servers"]
    else:
        servers = data
    if not isinstance(servers, dict) or not servers:
        raise InstallError("mcp.json has no servers")
    for name, spec in servers.items():
        if not isinstance(name, str) or not name.strip():
            raise InstallError("mcp.json has an empty server name")
        if not isinstance(spec, dict):
            raise InstallError(f"mcp.json server {name} is not an object")
    return servers


def merge_servers(files: list[Path]) -> dict:
    merged: dict = {}
    for path in files:
        for name, spec in load_mcp_servers(path).items():
            if name in merged:
                raise InstallError(f"duplicate mcp server in repo: {name}")
            merged[name] = spec
    return merged


def toml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_value(value) -> str:
    if isinstance(value, str):
        return toml_quote(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise InstallError("mcp.json has a value this host config cannot store")


def toml_header(name: str, child: str | None = None) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", name):
        base = f"mcp_servers.{name}"
    else:
        base = "mcp_servers." + toml_quote(name)
    if child:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", child):
            raise InstallError(f"refusing mcp field name: {child}")
        return f"[{base}.{child}]"
    return f"[{base}]"


def server_toml(name: str, spec: dict) -> str:
    lines = [toml_header(name)]
    for key, value in spec.items():
        if isinstance(value, dict):
            continue
        lines.append(f"{key} = {toml_value(value)}")
    for key, value in spec.items():
        if not isinstance(value, dict):
            continue
        lines.append(toml_header(name, key))
        for child, child_value in value.items():
            if isinstance(child_value, dict):
                raise InstallError(f"mcp.json server {name} is nested too deep")
            lines.append(f"{child} = {toml_value(child_value)}")
    return "\n".join(lines) + "\n"


def toml_has_server(text: str, name: str) -> bool:
    quoted = re.escape(toml_quote(name))
    bare = re.escape(name)
    pattern = rf"(?m)^\[mcp_servers\.(?:{quoted}|{bare})\]\s*$"
    return re.search(pattern, text) is not None


def toml_remove_server(text: str, name: str) -> str:
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    skipping = False
    headers = {toml_header(name)}
    prefix = toml_header(name)[:-1] + "."
    for line in lines:
        stripped = line.strip()
        if stripped in headers or stripped.startswith(prefix):
            skipping = True
            continue
        if skipping and stripped.startswith("[") and stripped.endswith("]"):
            skipping = False
        if not skipping:
            kept.append(line)
    return "".join(kept)


def write_json_mcp(path: Path, servers: dict, replace: bool, dry_run: bool) -> None:
    if path.exists():
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise InstallError(f"MCP config is not valid JSON: {path}") from exc
        if not isinstance(document, dict):
            raise InstallError(f"MCP config is not a JSON object: {path}")
    else:
        document = {}
    current = document.get("mcpServers")
    if current is None:
        current = {}
    if not isinstance(current, dict):
        raise InstallError(f"mcpServers is not an object: {path}")
    conflicts = [name for name in servers if name in current]
    for name in conflicts:
        confirm(f"{path} server {name}", replace, dry_run)
    if dry_run:
        return
    for name, spec in servers.items():
        current[name] = spec
    document["mcpServers"] = current
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def write_toml_mcp(path: Path, servers: dict, replace: bool, dry_run: bool) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    conflicts = [name for name in servers if toml_has_server(text, name)]
    for name in conflicts:
        confirm(f"{path} server {name}", replace, dry_run)
    if dry_run:
        return
    for name in conflicts:
        text = toml_remove_server(text, name)
    block = "\n".join(server_toml(name, spec).rstrip() for name, spec in servers.items())
    if text and not text.endswith("\n"):
        text += "\n"
    if text and not text.endswith("\n\n"):
        text += "\n"
    text += block
    if not text.endswith("\n"):
        text += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dependency_state(text: str, key: str, link_value: str) -> str:
    pattern = re.compile(
        rf'^([ \t]*)"{re.escape(key)}"\s*:\s*"([^"]*)"\s*,?\s*$',
        re.M,
    )
    match = pattern.search(text)
    if not match:
        return "missing"
    current = match.group(2)
    if current.startswith("link:"):
        current = current[5:]
    if os.path.normcase(current.replace("/", "\\")) == os.path.normcase(
        link_value.replace("/", "\\")
    ):
        return "same"
    return "conflict"


def upsert_dependency(text: str, key: str, link_value: str) -> str:
    pattern = re.compile(
        rf'^([ \t]*)"{re.escape(key)}"\s*:\s*"[^"]*"(\s*,?)\s*$',
        re.M,
    )
    match = pattern.search(text)
    if match:
        indent = match.group(1) or "    "
        had_comma = match.group(0).rstrip().endswith(",")
        comma = "," if had_comma else ""
        replacement = f'{indent}"{key}": "link:{link_value}"{comma}'
        return pattern.sub(replacement, text, count=1)
    marker = re.search(r'"dependencies"\s*:\s*\{', text)
    if not marker:
        raise InstallError("profile package.json has no dependencies object")
    start = text.find("{", marker.start())
    depth = 0
    end = None
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        raise InstallError("dependencies object is not closed")
    body = text[start + 1 : end].rstrip()
    if body and not body.endswith(","):
        body += ","
    body += f'\n    "{key}": "link:{link_value}"\n  '
    return text[: start + 1] + body + text[end:]


def plan_actions(root_label: str, root: Path, host: str, host_cfg: dict) -> list[dict]:
    found = detect(root)
    if not found["kinds"]:
        raise InstallError(
            "no manifest found (looked for SKILL.md, plugin.json, "
            ".cursor-plugin/plugin.json, mcp.json, cordis.patch.yml)"
        )
    actions: list[dict] = []
    plugins_dir = host_cfg.get("plugins")
    skills_dir = host_cfg.get("skills")
    for rel, label in found["plugins"]:
        if not plugins_dir:
            raise InstallError(f"{host} has no plugin folder in {CONFIG_PATH}")
        name = unit_name(root_label, rel)
        dest = Path(plugins_dir) / name
        action = {
            "op": "copy",
            "kind": label,
            "src": abs_unit(root, rel),
            "dest": dest,
            "link": None,
        }
        if host == "deepseek" and host_cfg.get("profile_package"):
            action["link"] = {
                "package": Path(host_cfg["profile_package"]),
                "key": f"@local/{name}",
                "value": dest.as_posix(),
            }
        actions.append(action)
    for rel in found["skills"]:
        if not skills_dir:
            raise InstallError(f"{host} has no skill folder in {CONFIG_PATH}")
        name = unit_name(root_label, rel)
        actions.append(
            {
                "op": "copy",
                "kind": "skill",
                "src": abs_unit(root, rel),
                "dest": Path(skills_dir) / name,
                "link": None,
            }
        )
    if found["mcp"]:
        mcp_path = host_cfg.get("mcp_config")
        if not mcp_path:
            raise InstallError(f"{host} has no MCP config in {CONFIG_PATH}")
        actions.append(
            {
                "op": "mcp",
                "kind": "mcp",
                "files": [abs_unit(root, rel) for rel in found["mcp"]],
                "dest": Path(mcp_path),
                "format": host_cfg.get("mcp_format", "json"),
                "link": None,
            }
        )
    return actions


def kind_label(actions: list[dict]) -> str:
    labels: list[str] = []
    for action in actions:
        if action["kind"] not in labels:
            labels.append(action["kind"])
    return "+".join(labels)


def apply_action(action: dict, replace: bool, dry_run: bool) -> None:
    dest = action["dest"]
    print(f"destination: {dest}")
    if action["op"] == "copy":
        files = list_files(action["src"])
        if dest.exists():
            confirm(str(dest), replace, dry_run)
        link = action.get("link")
        link_state = None
        if link:
            package = link["package"]
            if not package.exists():
                raise InstallError(f"profile package.json is missing: {package}")
            text = package.read_text(encoding="utf-8")
            link_state = dependency_state(text, link["key"], link["value"])
            if link_state == "conflict":
                confirm(f"{package} dependency {link['key']}", replace, dry_run)
        if dry_run:
            print("files:")
            for name in files:
                print(f"  {name}")
            if link and link_state != "same":
                print(f"link: {link['key']} -> {link['value']}")
            return
        copied = copy_tree(action["src"], dest)
        print(f"copied: {copied} files")
        if link and link_state != "same":
            text = link["package"].read_text(encoding="utf-8")
            updated = upsert_dependency(text, link["key"], link["value"])
            link["package"].write_text(updated, encoding="utf-8")
            print(f"link: {link['key']} -> {link['value']}")
        return

    servers = merge_servers(action["files"])
    names = ", ".join(servers)
    if dry_run:
        print("files:")
        for path in action["files"]:
            print(f"  {path.name}")
        print(f"merge: {names}")
    if action["format"] == "toml":
        write_toml_mcp(dest, servers, replace, dry_run)
    else:
        write_json_mcp(dest, servers, replace, dry_run)
    if not dry_run:
        print(f"merged: {names}")


def clone_repo(parsed: dict, dest: Path) -> None:
    cmd = ["git", "clone", "--depth", "1", "--quiet"]
    if parsed["ref"]:
        cmd.extend(["--branch", parsed["ref"]])
    cmd.append(f"https://github.com/{parsed['owner']}/{parsed['repo']}.git")
    cmd.append(str(dest))
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "git clone failed").strip()
        raise InstallError(detail)


def source_from_clone(clone_dir: Path, parsed: dict) -> Path:
    if not parsed["subpath"]:
        return clone_dir
    candidate = clone_dir.joinpath(*parsed["subpath"].split("/"))
    if not candidate.exists():
        raise InstallError(f"subpath not in repo: {parsed['subpath']}")
    if parsed["blob"] or candidate.is_file():
        return candidate.parent
    return candidate


def install_url(url: str, host: str, host_cfg: dict, replace: bool, dry_run: bool) -> None:
    local = Path(url)
    if local.is_dir():
        if not dry_run:
            raise InstallError(f"refusing URL: {url}")
        root = local.resolve()
        repo = root.name
        print(f"repo: {repo}")
        actions = plan_actions(repo, root, host, host_cfg)
        print(f"kind: {kind_label(actions)}")
        for action in actions:
            apply_action(action, replace, dry_run)
        return

    parsed = parse_github_url(url)
    print(f"repo: {parsed['repo']}")
    parent = Path(tempfile.mkdtemp(prefix="gh-install-"))
    clone_dir = parent / "repo"
    try:
        clone_repo(parsed, clone_dir)
        root = source_from_clone(clone_dir, parsed)
        root_label = parsed["repo"] if root == clone_dir else root.name
        actions = plan_actions(root_label, root, host, host_cfg)
        print(f"kind: {kind_label(actions)}")
        for action in actions:
            apply_action(action, replace, dry_run)
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gh-install")
    parser.add_argument("--host", required=True, choices=HOSTS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("urls", nargs="+")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, OSError):
        pass
    args = build_parser().parse_args(argv)
    try:
        hosts = load_config()
        host_cfg = hosts[args.host]
        print(f"host: {args.host}")
        for url in args.urls:
            install_url(url, args.host, host_cfg, args.replace, args.dry_run)
    except InstallError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
