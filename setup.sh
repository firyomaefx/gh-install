#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
TOOL_DIR="$(pwd)"

echo ""
echo " gh-install setup"
echo " ================="
echo ""

MISSING=0
if ! command -v python3 >/dev/null 2>&1; then
  echo " [X] python3 not found on PATH."
  MISSING=1
else
  python3 --version | sed 's/^/ [OK] /'
fi

if ! command -v git >/dev/null 2>&1; then
  echo " [X] git not found on PATH."
  MISSING=1
else
  git --version | sed 's/^/ [OK] /'
fi

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo " Fix missing tools, then run ./setup.sh again."
  exit 1
fi

if [ ! -f hosts.json ]; then
  python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('gh_install', 'gh-install.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.seed_config()
print(' [OK] Created hosts.json from hosts.example.json')
"
else
  echo " [OK] hosts.json already exists"
fi

echo ""
echo " Detect installed apps (local disk only, no AI tokens):"
python3 gh-install.py --scan
echo ""
echo " Install from a GitHub link:"
echo "   python3 gh-install.py --dry-run <url>"
echo "   python3 gh-install.py <url>"
echo ""
echo " Tool folder: $TOOL_DIR"
echo ""