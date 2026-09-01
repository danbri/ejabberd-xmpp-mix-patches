# ejabberd XMPP MIX patches

GPL-2.0-compatible modernization patches and interoperability checks for
ejabberd's experimental MIX implementation.

## Patch acceptance rule

**No patch enters `patches/series` until a reader can tell, without reconstructing
the investigation, what it changes, which observed failure it fixes, why the
protocol permits or requires the change, and how it can affect interoperability
with existing deployments.**

Every patch must follow [PATCH_POLICY.md](PATCH_POLICY.md). In particular, its
commit message and accompanying notes must cover the problem and evidence, the
exact behavior change, protocol basis, compatibility with the status quo,
interoperability and operational risks, and verification. Non-obvious protocol
decisions must also have concise comments beside the relevant source code.

See [TODO.md](TODO.md) for the work queue. The documentation and compatibility
review there are release gates, not cleanup to defer until after implementation.

## Scope

This repository is intentionally separate from the Apache-2.0
[`foafmixer-mix`](https://github.com/danbri/foafmixer-mix) project. It carries
only downstream changes derived from, and intended for eventual discussion
with, ejabberd.

The first target is ejabberd **26.07**, which is the version used by the
Foafmixer pilot. The goal is practical interoperability with current
MIX-capable clients, beginning with BeagleIM 6.0.1, while preserving
server-neutral protocol tests upstream in `foafmixer-mix`.

## Status

Three narrow corrections are under test:

1. `0001` preserves PAM 2 responses and implements the missing Core 1
   information-node path.
2. `0002` recognizes the locally constructed, Core 0, and Core 1 MIX metadata
   forms when the participant server routes live messages.
3. `0003` emits Core 1 metadata explicitly instead of allowing the codec's Core
   0 default to make BeagleIM 6.0.1 discard live messages.

Together they now support immediate two-way messages between BeagleIM 6.0.1
and the browser pilot. After the default-port cutover, one browser submission
also appeared immediately in both BeagleIM on macOS and Siskin IM on iOS. They
are not a claim of complete MIX support, and `0002` and `0003` remain outside
`patches/series` while their remaining compatibility matrix is completed.

The test sequence is:

1. build a custom ejabberd 26.07 image from the pinned commit and ordered
   reviewer patch list;
2. run it on loopback with a dedicated Docker or Podman volume;
3. create and join a channel with BeagleIM 6.0.1 and the browser client;
4. retrieve participants and channel information; and
5. exchange and render live groupchat messages in both directions between two
   pilot accounts, without reconnecting into MAM history.

That sequence has passed for the current three-patch reviewer stack. The same
image now backs the private pilot on its normal client ports.

## Local Docker or Podman review

The repository includes a repeatable, pinned-source local container workflow.
It clones the exact upstream commit into a temporary build directory, applies
`patches/reviewer-series`, and invokes upstream's own Dockerfile:

```sh
make image
make up
make register
```

See [docs/local-container-review.md](docs/local-container-review.md) for ports,
engine selection, lifecycle, provenance, and security boundaries.

The repository and image build context contain no live deployment account
names, JIDs, passwords, transcripts, or database state. The generic container
configuration declares no users; reviewer accounts are entered interactively
at runtime and persist only in the local named volume.

## Layout

```
patches/       Ordered patches for the pinned upstream source
docs/          Reproducible compatibility notes and protocol observations
docker/        Generic loopback-only reviewer configuration and Compose file
tools/         Pinned image builder and local lifecycle helper
```

See [UPSTREAM.md](UPSTREAM.md) for the exact source baseline and how to apply
the series.
GPL-2.0-compatible ejabberd MIX core:1 modernization patches and interoperability tests
