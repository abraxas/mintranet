#!/bin/bash
# Open the Owner egress gate first. Rewrite docker-compose.yml image lines to digests.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/docker-compose.yml"
if ! command -v docker >/dev/null; then
  echo "docker is required to pin digests." >&2
  exit 1
fi
mapfile -t images < <(awk '/image: / && $2 !~ /mintranet\// {print $2}' "$FILE" | sort -u)
for image in "${images[@]}"; do
  echo "pull $image"
  docker pull "$image"
  digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image")
  echo "$image -> $digest"
done
echo "Record those digests in docker-compose.yml before applying on the island."
