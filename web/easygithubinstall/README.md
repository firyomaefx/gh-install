# easygithubinstall (mobile web)

Mobile-first site for **Easy GitHub Install**: paste a GitHub URL on iOS/Android, get a QR/copied `gh-install` command for your desktop.

## Develop

```bash
cd web/easygithubinstall
npm install
npm run dev
```

## Deploy (Cloudflare Workers)

```bash
npm run deploy
```

Worker name: `easygithubinstall`

**Live (demo):** https://easygithubinstall.stump-vinyl.workers.dev

**Live (account `firyomaefx@gmail.com`, workers.dev subdomain `ipo-hunter`):** https://easygithubinstall.ipo-hunter.workers.dev — run `npm run deploy` with `wrangler login` or `CLOUDFLARE_API_TOKEN` to publish the full build (static assets + API).

**Custom domain (optional):** In Cloudflare Dashboard → Workers → `easygithubinstall` → Triggers → Add Custom Domain (e.g. `easygithubinstall.com`).

## API

| Route | Description |
|-------|-------------|
| `GET /api/validate?url=` | Parse GitHub URL (same rules as `gh-install.py`) |
| `GET /api/repo?owner=&repo=` | Optional GitHub repo metadata (cached) |
| `GET /api/qr?data=` | SVG QR for handoff URLs |