export type ParsedGithub = {
  ok: true;
  owner: string;
  repo: string;
  ref: string | null;
  subpath: string;
  blob: boolean;
  url: string;
  installCommand: string;
};

export type ValidateError = {
  ok: false;
  error: string;
};

const NAME_RE = /^[A-Za-z0-9_.-]+$/;
const REF_RE = /^[A-Za-z0-9._~+-]+$/;

export function parseGithubUrl(rawInput: string): ParsedGithub | ValidateError {
  const raw = rawInput.trim();
  if (!raw || /[\n\r\t\\ ]/.test(raw)) {
    return { ok: false, error: "Invalid URL" };
  }
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    return { ok: false, error: "Invalid URL" };
  }
  if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "github.com") {
    return { ok: false, error: "Only https://github.com/owner/repo URLs are allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, error: "URL must not include query, hash, or credentials" };
  }
  const segs = parsed.pathname.split("/").filter(Boolean);
  if (segs.length < 2) {
    return { ok: false, error: "Missing owner or repo" };
  }
  let owner = segs[0];
  let repo = segs[1];
  if (repo.endsWith(".git")) {
    repo = repo.slice(0, -4);
  }
  if (!NAME_RE.test(owner) || !NAME_RE.test(repo)) {
    return { ok: false, error: "Invalid owner or repo name" };
  }
  if (owner === "." || owner === ".." || repo === "." || repo === "..") {
    return { ok: false, error: "Invalid path" };
  }

  let ref: string | null = null;
  let subpath = "";
  let blob = false;

  if (segs.length > 2) {
    const kind = segs[2];
    if (kind !== "tree" && kind !== "blob") {
      return { ok: false, error: "Unsupported GitHub URL path" };
    }
    if (segs.length < 4) {
      return { ok: false, error: "Incomplete tree/blob URL" };
    }
    blob = kind === "blob";
    ref = segs[3];
    if (!REF_RE.test(ref) || ref === "." || ref === "..") {
      return { ok: false, error: "Invalid ref" };
    }
    const rest = segs.slice(4);
    if (rest.some((seg) => !seg || seg === "." || seg === "..")) {
      return { ok: false, error: "Invalid subpath" };
    }
    subpath = rest.join("/");
    if (blob && !subpath) {
      return { ok: false, error: "blob URL needs a file path" };
    }
  }

  const installCommand = `gh-install "${raw}"`;
  return {
    ok: true,
    owner,
    repo,
    ref,
    subpath,
    blob,
    url: raw,
    installCommand,
  };
}