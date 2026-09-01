# Local container review

This workflow builds a disposable ejabberd image from the exact upstream
commit in [UPSTREAM.md](../UPSTREAM.md), applies
[`patches/reviewer-series`](../patches/reviewer-series) in order, and runs the
result on loopback. It supports either rootless Podman or Docker.

The build context contains source and patches only. This repository must never
contain a live deployment's account names, JIDs, credentials, transcripts,
database exports, or named-volume contents. The included configuration declares
no accounts. `register` prompts at runtime and writes only to the local named
volume.

## Quick start

Prerequisites are Git plus Podman or Docker with network access for the pinned
upstream repository and base images.

```sh
make image
make up
make register
```

`make register` asks for an account localpart and a password without echoing the
password. The default XMPP domain is `localhost`; override it at runtime with
`MIX_DOMAIN` when a client requires another local test domain.

The stack exposes:

- plaintext XMPP C2S on `127.0.0.1:5222`;
- XMPP-over-WebSocket on `ws://127.0.0.1:5281/xmpp`; and
- no public, server-to-server, web-admin, or HTTP API listener.

Plaintext C2S is safe here only because the runner rejects non-loopback binds by
default. Do not opt into a non-loopback bind without adding transport security
and reviewing authentication exposure.

Useful lifecycle commands:

```sh
make status
make logs
make down
```

`make down` removes only the review container. It intentionally preserves the
named volume so a reviewer can restart without recreating runtime accounts.
Volume deletion is left as a separate, explicit container-engine operation.

To force Docker when both engines are installed:

```sh
CONTAINER_ENGINE=docker make image up
```

The equivalent Compose entry point, after building the image, is:

```sh
docker compose -f docker/compose.yaml up -d
```

The direct runner and Compose definition use the same default image, container,
ports, configuration, and named-volume identity. Do not run both at once.

## What the image means

`patches/series` is the acceptance-gated patch list. The local image instead
uses `patches/reviewer-series`, which includes downstream candidates still
under interoperability review. Building or running this image does not promote
those candidates into the accepted series and does not imply complete MIX
support.

The builder verifies the exact upstream commit before applying any patch and
uses upstream's own container Dockerfile. The final image is labelled with the
upstream commit and ordered patch filenames so a reviewer can inspect its
provenance without trusting the local image tag.

This pins the ejabberd source, not every transitive build artifact. Upstream's
26.07 Dockerfile still references mutable base-image tags and builds one helper
from its upstream default branch. A later release artifact should pin those
digests too; this local image is for source review and interoperability testing,
not a claim of byte-for-byte reproducible supply-chain output.
