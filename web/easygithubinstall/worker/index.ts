import QRCode from "qrcode";
import { parseGithubUrl } from "./validate";

export interface Env {
  ASSETS: Fetcher;
}

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
};

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...JSON_HEADERS, ...CORS_HEADERS },
  });
}

async function handleValidate(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const target = url.searchParams.get("url");
  if (!target) {
    return json({ ok: false, error: "Missing url parameter" }, 400);
  }
  const result = parseGithubUrl(target);
  return json(result, result.ok ? 200 : 400);
}

async function handleRepo(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const owner = url.searchParams.get("owner");
  const repo = url.searchParams.get("repo");
  if (!owner || !repo) {
    return json({ ok: false, error: "Missing owner or repo" }, 400);
  }
  const gh = await fetch(`https://api.github.com/repos/${owner}/${repo}`, {
    headers: {
      Accept: "application/vnd.github+json",
      "User-Agent": "easygithubinstall-worker",
    },
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  if (!gh.ok) {
    return json({ ok: false, error: "Repository not found or rate limited" }, gh.status);
  }
  const data = (await gh.json()) as { full_name?: string; description?: string | null };
  return json({
    ok: true,
    fullName: data.full_name ?? `${owner}/${repo}`,
    description: data.description ?? null,
  });
}

async function handleQr(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const data = url.searchParams.get("data");
  if (!data || data.length > 2048) {
    return new Response("Bad request", { status: 400 });
  }
  const svg = await QRCode.toString(data, {
    type: "svg",
    margin: 1,
    width: 280,
    errorCorrectionLevel: "M",
  });
  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (url.pathname === "/api/validate" && request.method === "GET") {
      return handleValidate(request);
    }
    if (url.pathname === "/api/repo" && request.method === "GET") {
      return handleRepo(request);
    }
    if (url.pathname === "/api/qr" && request.method === "GET") {
      return handleQr(request);
    }

    if (url.pathname === "/go" && !url.pathname.endsWith(".html")) {
      const goUrl = new URL("/go.html", url);
      goUrl.search = url.search;
      return env.ASSETS.fetch(new Request(goUrl.toString(), request));
    }

    return env.ASSETS.fetch(request);
  },
} satisfies ExportedHandler<Env>;