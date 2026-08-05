#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
exec "$root/scripts/dragonkernel/build_kernel.sh" sukisu "$@"
