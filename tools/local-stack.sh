#!/usr/bin/env bash
# Run the reviewer image on loopback and manage accounts interactively.
# The named volume is deliberately retained by `down`.
set -euo pipefail

repo_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
config="$repo_dir/docker/ejabberd.yml"
container=${MIX_CONTAINER:-ejabberd-mix-review}
image=${MIX_IMAGE:-localhost/foafmixer/ejabberd-mix:26.07-pilot}
volume=${MIX_VOLUME:-ejabberd-mix-review-state}
domain=${MIX_DOMAIN:-localhost}
bind_address=${MIX_BIND_ADDRESS:-127.0.0.1}
c2s_port=${MIX_C2S_PORT:-5222}
websocket_port=${MIX_WEBSOCKET_PORT:-5281}

usage() {
  echo "usage: $0 {up|down|status|logs|register}" >&2
}

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

validate_runtime() {
  case "$bind_address" in
    127.0.0.1|::1) ;;
    *)
      if [ "${MIX_ALLOW_NON_LOOPBACK:-}" != yes ]; then
        echo "Refusing non-loopback bind '$bind_address'. Set MIX_ALLOW_NON_LOOPBACK=yes only after a security review." >&2
        exit 1
      fi
      ;;
  esac
  case "$domain" in
    ''|*[!A-Za-z0-9.-]*)
      echo "MIX_DOMAIN must be a DNS-style domain name." >&2
      exit 1
      ;;
  esac
  case "$c2s_port:$websocket_port" in
    *[!0-9:]*) echo "Review ports must be decimal numbers." >&2; exit 1 ;;
  esac
}

container_exists() {
  "$engine" container inspect "$container" >/dev/null 2>&1
}

wait_ready() {
  local attempt
  for _ in $(seq 1 30); do
    if "$engine" exec "$container" ejabberdctl status >/dev/null 2>&1; then
      "$engine" exec "$container" ejabberdctl status
      return
    fi
    sleep 1
  done
  echo "ejabberd did not become ready; recent logs follow." >&2
  "$engine" logs --tail 80 "$container" >&2 || true
  exit 1
}

engine=$(detect_engine)

case "${1:-}" in
  up)
    validate_runtime
    "$engine" image inspect "$image" >/dev/null 2>&1 || {
      echo "Image not found: $image" >&2
      echo "Run tools/build-image.sh first." >&2
      exit 1
    }
    if container_exists; then
      running=$("$engine" inspect --format '{{.State.Running}}' "$container")
      if [ "$running" != true ]; then
        "$engine" start "$container" >/dev/null
      fi
    else
      published_address=$bind_address
      if [ "$published_address" = ::1 ]; then
        published_address="[$published_address]"
      fi
      "$engine" volume create "$volume" >/dev/null
      "$engine" run -d \
        --name "$container" \
        --restart unless-stopped \
        --label io.foafmixer.purpose=ejabberd-mix-review \
        -e "EJABBERD_MACRO_HOST=$domain" \
        -p "$published_address:$c2s_port:5222" \
        -p "$published_address:$websocket_port:5281" \
        -v "$volume:/opt/ejabberd" \
        -v "$config:/opt/ejabberd/conf/ejabberd.yml:ro" \
        "$image" >/dev/null
    fi
    wait_ready
    echo "XMPP domain: $domain"
    echo "C2S: $bind_address:$c2s_port (plaintext, loopback only)"
    echo "WebSocket: ws://$bind_address:$websocket_port/xmpp"
    echo "Create a review account with: $0 register"
    ;;
  down)
    if container_exists; then
      "$engine" stop "$container" >/dev/null
      "$engine" rm "$container" >/dev/null
      echo "Removed container $container; retained volume $volume."
    else
      echo "Container does not exist: $container"
    fi
    ;;
  status)
    if ! container_exists; then
      echo "Container does not exist: $container"
      exit 1
    fi
    "$engine" inspect --format '{{.Name}} {{.State.Status}} {{.Config.Image}}' "$container"
    "$engine" exec "$container" ejabberdctl status
    ;;
  logs)
    "$engine" logs "$container"
    ;;
  register)
    validate_runtime
    container_exists || {
      echo "Start the review server first: $0 up" >&2
      exit 1
    }
    read -r -p "Account localpart: " localpart
    case "$localpart" in
      ''|*[!A-Za-z0-9._-]*)
        echo "Use only letters, digits, dot, underscore, and hyphen." >&2
        exit 2
        ;;
    esac
    read -r -s -p "Password (input hidden): " password
    printf '\n'
    if [ -z "$password" ]; then
      echo "Password must not be empty." >&2
      exit 2
    fi
    "$engine" exec "$container" ejabberdctl register "$localpart" "$domain" "$password"
    unset password
    echo "Account registered in the local review volume; no credential was written to this repository."
    ;;
  *) usage; exit 2 ;;
esac
