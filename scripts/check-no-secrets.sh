#!/usr/bin/env bash
# Block commits that would publish API keys or .env files.
# Invoked from scripts/git-hooks/pre-commit (see make install-hooks).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

fail=0

# Never commit env files with secrets (examples are OK).
forbidden_paths=(
  .env
  config/.env
  config/api-keys.json
  cesium-ion-token.txt
  secrets/
)
for path in "${forbidden_paths[@]}"; do
  if git diff --cached --name-only | grep -Fx "$path" >/dev/null 2>&1; then
    echo "ERROR: refusing to commit secret file: $path" >&2
    fail=1
  fi
done

# Scan staged text for non-empty API key assignments (skip examples/docs).
while IFS= read -r -d '' file; do
  case "$file" in
    config/.env.example|.env.example|config/api-keys.example.json|*.md|scripts/check-no-secrets.sh)
      continue
      ;;
  esac
  if git diff --cached -- "$file" | grep -E '^\+[^#+].*(API_KEY|ACCESS_TOKEN|_SECRET|_PASSWORD)=[^[:space:]]{8,}' \
       | grep -vE 'your_|YOUR_|TESTKEY|xxx'; then
    echo "ERROR: possible secret in staged diff: $file" >&2
    git diff --cached -- "$file" | grep -E '^\+.*(API_KEY|ACCESS_TOKEN|_SECRET|_PASSWORD)\s*=\s*.{8,}' \
      | grep -vE '=\\s*$' | head -3 >&2
    fail=1
  fi
done < <(git diff --cached --name-only -z --diff-filter=ACM 2>/dev/null || true)

if (( fail )); then
  echo "Remove secrets from staged files or use .env (gitignored) at project root." >&2
  exit 1
fi

exit 0
