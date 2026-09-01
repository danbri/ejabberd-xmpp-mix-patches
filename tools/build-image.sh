#!/usr/bin/env bash
# Build the reviewer image from an exact upstream commit and the declared
# downstream patch stack. No pilot configuration, identities, or state enter
# the build context.
set -euo pipefail

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
series_file="$repo_dir/patches/reviewer-series"
upstream_url=https://github.com/processone/ejabberd.git
upstream_commit=413e7faee111028b7630523db82f7812ae285261
image=${MIX_IMAGE:-localhost/foafmixer/ejabberd-mix:26.07-pilot}

detect_engine() {
  if [ -n "${CONTAINER_ENGINE:-}" ]; then
    command -v "$CONTAINER_ENGINE" >/dev/null 2>&1 || {
      echo "Container engine not found: $CONTAINER_ENGINE" >&2
      exit 1
    }
    printf '%s\n' "$CONTAINER_ENGINE"
  elif command -v podman >/dev/null 2>&1; then
    printf '%s\n' podman
  elif command -v docker >/dev/null 2>&1; then
    printf '%s\n' docker
  else
    echo "Install Podman or Docker, or set CONTAINER_ENGINE." >&2
    exit 1
  fi
}

engine=$(detect_engine)
build_root=$(mktemp -d "${TMPDIR:-/tmp}/ejabberd-mix-build.XXXXXX")
source_dir="$build_root/ejabberd"

cleanup() {
  case "$build_root" in
    */ejabberd-mix-build.*) rm -rf -- "$build_root" ;;
    *) echo "Refusing to remove unexpected build path: $build_root" >&2 ;;
  esac
}
trap cleanup EXIT HUP INT TERM

git init -q "$source_dir"
git -C "$source_dir" remote add origin "$upstream_url"
git -C "$source_dir" fetch -q --depth=1 origin "$upstream_commit"
git -C "$source_dir" checkout -q --detach FETCH_HEAD

actual_commit=$(git -C "$source_dir" rev-parse HEAD)
if [ "$actual_commit" != "$upstream_commit" ]; then
  echo "Upstream commit mismatch: expected $upstream_commit, got $actual_commit" >&2
  exit 1
fi

# git-am needs a local committer identity. This build-only identity is not an
# XMPP account and is never written outside the temporary checkout.
git -C "$source_dir" config user.name "Local MIX image builder"
git -C "$source_dir" config user.email "noreply@invalid"

applied=
while IFS= read -r patch_name; do
  case "$patch_name" in
    ''|'#'*) continue ;;
    *[!A-Za-z0-9._-]*)
      echo "Invalid patch name in reviewer-series: $patch_name" >&2
      exit 1
      ;;
  esac
  patch_file="$repo_dir/patches/$patch_name"
  if [ ! -f "$patch_file" ]; then
    echo "Missing patch: $patch_file" >&2
    exit 1
  fi
  git -C "$source_dir" am --quiet --committer-date-is-author-date "$patch_file"
  applied="${applied}${applied:+,}${patch_name}"
done <"$series_file"

echo "Building $image"
echo "Upstream: $upstream_commit"
echo "Patches: $applied"
"$engine" build \
  --build-arg VERSION=26.07-mix-core1 \
  --label "org.foafmixer.ejabberd.upstream-commit=$upstream_commit" \
  --label "org.foafmixer.ejabberd.patch-series=$applied" \
  --tag "$image" \
  --file "$source_dir/.github/container/Dockerfile" \
  "$source_dir"

echo "Built $image with $engine."
