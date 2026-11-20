const NAME_RE = /^[A-Za-z0-9_.-]+$/;
const REF_RE = /^[A-Za-z0-9._~+-]+$/;

export function parseGithubUrlClient(rawInput) {
  const raw = rawInput.trim();
  if (!raw || /[\n\r\t\\ ]/.test(raw)) {
    return { ok: false, error: "Invalid URL" };
  }
  let parsed;
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
  if (repo.endsWith(".git")) repo = repo.slice(0, -4);
  if (!NAME_RE.test(owner) || !NAME_RE.test(repo)) {
    return { ok: false, error: "Invalid owner or repo name" };
  }
  const installCommand = `gh-install "${raw}"`;
  return { ok: true, owner, repo, url: raw, installCommand };
}

export function detectDevice() {
  const ua = navigator.userAgent || "";
  if (/iPhone|iPad|iPod/i.test(ua)) return { kind: "ios", label: "iOS" };
  if (/Android/i.test(ua)) return { kind: "android", label: "Android" };
  if (/Macintosh|Mac OS X/i.test(ua)) return { kind: "desktop", platform: "mac", label: "Mac" };
  if (/Windows/i.test(ua)) return { kind: "desktop", platform: "windows", label: "Windows" };
  if (/Linux/i.test(ua)) return { kind: "desktop", platform: "linux", label: "Linux" };
  return { kind: "unknown", platform: "windows", label: "your device" };
}

export function isMobileDevice(kind) {
  return kind === "ios" || kind === "android";
}

export async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.left = "-9999px";
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(ta);
  return ok;
}

export function showToast(root, message = "Copied") {
  const toast = root.querySelector("#toast") || document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => toast.classList.add("hidden"), 2000);
}

export async function shareHandoff(payload) {
  if (!navigator.share) return false;
  try {
    await navigator.share({
      title: "Easy GitHub Install",
      text: payload.text,
      url: payload.url,
    });
    return true;
  } catch {
    return false;
  }
}

export function handoffPageUrl(repoUrl, origin) {
  const u = new URL("/go", origin);
  u.searchParams.set("url", repoUrl);
  return u.toString();
}

function desktopSetupLines(platform, installCommand) {
  const cmd =
    platform === "windows" ? installCommand : installCommand.replace(/^gh-install/, "python3 gh-install.py");
  const base = {
    windows: [
      "git clone https://github.com/firyomaefx/gh-install.git",
      "cd gh-install",
      "setup.cmd",
      "gh-install --scan",
      cmd,
    ],
    mac: [
      "git clone https://github.com/firyomaefx/gh-install.git",
      "cd gh-install",
      "chmod +x setup.sh && ./setup.sh",
      "python3 gh-install.py --scan",
      cmd,
    ],
    linux: [
      "git clone https://github.com/firyomaefx/gh-install.git",
      "cd gh-install",
      "chmod +x setup.sh && ./setup.sh",
      "python3 gh-install.py --scan",
      cmd,
    ],
  };
  return base[platform] || base.windows;
}

function renderDesktopSteps(root, platform, installCommand) {
  const stepsEl = root.querySelector("#desktop-steps");
  if (!stepsEl) return;
  const lines = desktopSetupLines(platform, installCommand);
  stepsEl.innerHTML = lines
    .map((line) => `<li><code class="mono">${escapeHtml(line)}</code></li>`)
    .join("");
}

export function setupPastePage(root) {
  const form = root.querySelector("#paste-form");
  const input = root.querySelector("#repo-url");
  const pasteBtn = root.querySelector("#paste-clipboard");
  const errEl = root.querySelector("#form-error");
  const resultEl = root.querySelector("#result");
  const bannerEl = root.querySelector("#device-banner");
  const desktopTerminal = root.querySelector("#desktop-terminal");

  const device = detectDevice();
  if (bannerEl) {
    bannerEl.classList.remove("hidden");
    if (isMobileDevice(device.kind)) {
      bannerEl.className = "device-banner device-banner--mobile";
      bannerEl.textContent = "Step 1 of 2 on this phone → Step 2 on your computer";
    } else {
      bannerEl.className = "device-banner device-banner--desktop";
      bannerEl.textContent = "Run the commands below in Terminal or PowerShell";
    }
  }

  pasteBtn?.addEventListener("click", async () => {
    errEl.textContent = "";
    try {
      const text = await navigator.clipboard.readText();
      if (text) input.value = text.trim();
    } catch {
      errEl.textContent = "Clipboard access denied — paste manually.";
    }
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    errEl.textContent = "";
    resultEl?.classList.add("hidden");
    const raw = input.value.trim();
    let data = parseGithubUrlClient(raw);
    if (!data.ok) {
      try {
        const res = await fetch(`/api/validate?url=${encodeURIComponent(raw)}`);
        data = await res.json();
      } catch {
        errEl.textContent = data.error || "Validation failed";
        return;
      }
    }
    if (!data.ok) {
      errEl.textContent = data.error;
      return;
    }

    const repoName = root.querySelector("#repo-name");
    const cmdEl = root.querySelector("#install-cmd");
    const openGo = root.querySelector("#open-go");

    if (repoName) repoName.textContent = `${data.owner}/${data.repo}`;
    if (cmdEl) cmdEl.textContent = data.installCommand;
    if (openGo) {
      openGo.href = handoffPageUrl(data.url, window.location.origin);
    }

    if (!isMobileDevice(device.kind) && desktopTerminal) {
      desktopTerminal.classList.remove("hidden");
      renderDesktopSteps(root, device.platform || "windows", data.installCommand);
    } else if (desktopTerminal) {
      desktopTerminal.classList.add("hidden");
    }

    resultEl?.classList.remove("hidden");
    resultEl?.scrollIntoView({ behavior: "smooth", block: "nearest" });

    try {
      const meta = await fetch(
        `/api/repo?owner=${encodeURIComponent(data.owner)}&repo=${encodeURIComponent(data.repo)}`,
      );
      const repoInfo = await meta.json();
      const descEl = root.querySelector("#repo-desc");
      if (descEl && repoInfo.ok && repoInfo.description) {
        descEl.textContent = repoInfo.description;
        descEl.classList.remove("hidden");
      } else if (descEl) {
        descEl.classList.add("hidden");
      }
    } catch {
      /* optional */
    }
  });

  root.querySelector("#copy-cmd")?.addEventListener("click", async () => {
    const cmd = root.querySelector("#install-cmd")?.textContent;
    if (cmd && (await copyText(cmd))) showToast(root);
  });

  root.querySelector("#share-handoff")?.addEventListener("click", async () => {
    const url = input.value.trim();
    const cmd = root.querySelector("#install-cmd")?.textContent || "";
    const go = handoffPageUrl(url, window.location.origin);
    const shared = await shareHandoff({
      text: `${cmd}\n\nSetup: https://github.com/firyomaefx/gh-install`,
      url: go,
    });
    if (!shared) {
      if (cmd && (await copyText(`${cmd}\n${go}`))) showToast(root, "Copied link & command");
      else errEl.textContent = "Share not available — use Copy command.";
    }
  });
}

export function setupGoPage(root) {
  const params = new URLSearchParams(window.location.search);
  const repoUrl = params.get("url") || "";
  const errEl = root.querySelector("#go-error");
  const content = root.querySelector("#go-content");

  if (!repoUrl) {
    if (errEl) errEl.textContent = "Missing url parameter.";
    return;
  }

  const data = parseGithubUrlClient(repoUrl);
  if (!data.ok) {
    if (errEl) errEl.textContent = data.error;
    return;
  }

  content?.classList.remove("hidden");
  const cmdEl = root.querySelector("#install-cmd");
  if (cmdEl) cmdEl.textContent = data.installCommand;

  const handoffUrl = handoffPageUrl(data.url, window.location.origin);
  const qrImg = root.querySelector("#qr-image");
  if (qrImg) {
    qrImg.src = `/api/qr?data=${encodeURIComponent(handoffUrl)}`;
    qrImg.alt = "QR code — scan with phone or open this page on your PC";
  }

  const setupByPlatform = {
    windows: desktopSetupLines("windows", data.installCommand),
    mac: desktopSetupLines("mac", data.installCommand),
    linux: desktopSetupLines("linux", data.installCommand),
  };

  const stepsEl = root.querySelector("#platform-steps");
  const tabs = root.querySelectorAll(".tab");

  function renderSteps(key) {
    const lines = setupByPlatform[key] || setupByPlatform.windows;
    if (!stepsEl) return;
    stepsEl.innerHTML = lines.map((line) => `<li><code class="mono">${escapeHtml(line)}</code></li>`).join("");
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      renderSteps(tab.dataset.platform || "windows");
    });
  });
  renderSteps("windows");

  root.querySelector("#copy-cmd")?.addEventListener("click", async () => {
    if (await copyText(data.installCommand)) showToast(root);
  });
  root.querySelector("#copy-url")?.addEventListener("click", async () => {
    if (await copyText(data.url)) showToast(root);
  });
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}