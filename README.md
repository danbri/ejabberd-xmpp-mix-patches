# ejabberd XMPP MIX patches

[![CI](https://github.com/danbri/ejabberd-xmpp-mix-patches/actions/workflows/ci.yml/badge.svg)](https://github.com/danbri/ejabberd-xmpp-mix-patches/actions/workflows/ci.yml)

GPL-2.0-compatible modernization patches and interoperability checks for
ejabberd's experimental MIX implementation (XEP-0369 MIX Core and XEP-0405
MIX-PAM). Target: ejabberd 26.07 with the bundled `xmpp` codec 1.13.4.

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

| Patch | Corrects | In `series` | Remaining gate |
| --- | --- | --- | --- |
| `0001` | Serves and negotiates the `urn:xmpp:mix:nodes:info` node; client-join result keeps `urn:xmpp:mix:pam:2` | yes | none open |
| `0002` | Participant server forwards live channel messages whose `<mix>` element carries an explicit Core 0 or Core 1 namespace | no | multi-resource copy count, no-mapping rejection, wire-level Core 0 check |
| `0003` | Channel emits `urn:xmpp:mix:core:1` metadata instead of the codec's Core 0 default | no | same matrix as `0002`, plus an end-to-end legacy Core 0 client check |

With all three applied, BeagleIM 6.0.1, Siskin IM on iOS and the browser
pilot in `foafmixer-mix` exchange live groupchat messages immediately in
both directions without falling back to MAM history. This is not complete
MIX support: presence, channel configuration and administration,
subscription updates and per-participant Core revision selection are not
implemented. Patch `0003` deliberately changes the wire namespace for
Core-0-only clients; its record states that risk.

CI applies `patches/series` with `git apply --check`, applies
`patches/reviewer-series` with `git am` on the pinned upstream commit, checks
that every accepted patch record carries the PATCH_POLICY headings, builds
ejabberd on Erlang/OTP 28 and runs the EUnit modules the patches add
(`mod_mix_info_test`, `mod_mix_pam_test`, `mod_mix_test`). Live-client
checks are manual and are recorded in each patch's Verification section.

The manual acceptance sequence is:

1. build a custom ejabberd 26.07 image from the pinned commit and ordered
   reviewer patch list;
2. run it on loopback with a dedicated Docker or Podman volume;
3. create and join a channel with BeagleIM 6.0.1 and the browser client;
4. retrieve participants and channel information; and
5. exchange and render live groupchat messages in both directions between two
   pilot accounts, without reconnecting into MAM history.

That sequence has passed for the current three-patch reviewer stack.

## Upstream

No issue or pull request has been opened against processone/ejabberd for
this series. The closest prior report,
[ejabberd issue 4006](https://github.com/processone/ejabberd/issues/4006),
described the missing PAM namespace and info node in 2023 and was closed by
its reporter without a fix. Upstream submission is a separate decision once
the `0002` and `0003` gates close; see [UPSTREAM.md](UPSTREAM.md).

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
patches/           Ordered patches for the pinned upstream source
patches/series     Acceptance-gated list (upstream candidates)
patches/reviewer-series  Full downstream stack used by the local image
docs/              Investigation notes per patch and the container review guide
docker/            Generic loopback-only reviewer configuration and Compose file
tools/             Pinned image builder and local lifecycle helper
.github/workflows  CI: apply, policy headings, EUnit, ShellCheck
```

See [UPSTREAM.md](UPSTREAM.md) for the exact source baseline and how to apply
the series.
GPL-2.0-compatible ejabberd MIX core:1 modernization patches and interoperability tests
