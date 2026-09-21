#!/usr/bin/env bash
# Compatibility name retained for old notes; CK3's sole entry point is run_stage.sh.
set -Eeuo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run_stage.sh" "$@"
