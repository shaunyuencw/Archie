#!/usr/bin/env bash
# Prefer the active supported Node; fall back only to an already installed runtime.
archie_node_supported() {
  command -v node >/dev/null 2>&1 && node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit((a===20&&b>=19)||(a>=22&&(a!==22||b>=12))?0:1)' 2>/dev/null
}
if ! archie_node_supported; then
  for archie_node in "$HOME"/.nvm/versions/node/v22.*/bin/node "$HOME"/.nvm/versions/node/v24.*/bin/node /opt/homebrew/opt/node/bin/node; do
    if [ -x "$archie_node" ]; then
      PATH="$(dirname "$archie_node"):$PATH"
      export PATH
      if archie_node_supported; then break; fi
    fi
  done
fi
if ! archie_node_supported; then echo 'ARCHIE needs Node 20.19+ or 22.12+ (even-numbered LTS recommended).' >&2; return 1; fi
