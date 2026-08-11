#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
value() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["payload_dumper"][sys.argv[2]])' "$baseline" "$1"
}

version=$(value version)
url=$(value url)
archive_sha=$(value archive_sha256)
destination=${PAYLOAD_DUMPER_DIR:-"$HOME/toolchains/payload-dumper-$version"}
archive="$destination/payload-dumper.tar.gz"
binary="$destination/payload-dumper"

mkdir -p "$destination"
if ! echo "$archive_sha  $archive" | sha256sum --check --status 2>/dev/null; then
  curl --fail --location --silent --show-error "$url" --output "$archive"
fi
echo "$archive_sha  $archive" | sha256sum --check --status

temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
tar -xzf "$archive" -C "$temporary"
mapfile -d '' candidates < <(find "$temporary" -type f -name 'payload-dumper*' -print0)
((${#candidates[@]} == 1))
install -m 0755 "${candidates[0]}" "$binary"
printf '%s\n' "$binary"
