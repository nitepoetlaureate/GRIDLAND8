#!/usr/bin/env bash
# Symlink scripts/git-hooks/* into .git/hooks/ so commit-msg, post-commit,
# and pre-push fire automatically.
set -e
cd "$(dirname "$0")/.."
hooks_src=scripts/git-hooks
hooks_dst=.git/hooks

if [[ ! -d "$hooks_dst" ]]; then
  echo "no .git/hooks/ — is this a git checkout?" >&2
  exit 1
fi

for h in commit-msg post-commit pre-push; do
  src="../../$hooks_src/$h"
  dst="$hooks_dst/$h"
  ln -sf "$src" "$dst"
  chmod +x "$hooks_src/$h"
  echo "installed: $dst -> $src"
done
