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
and the browser pilot. They are not a claim of complete MIX support, and `0002`
and `0003` remain outside `patches/series` while their remaining compatibility
matrix is completed.

The test sequence is:

1. build a custom ejabberd 26.07 image with the patch;
2. run it on separate local ports and a separate Podman volume;
3. create and join a channel with BeagleIM 6.0.1 and the browser client;
4. retrieve participants and channel information; and
5. exchange and render live groupchat messages in both directions between two
   pilot accounts, without reconnecting into MAM history.

The existing live pilot is not replaced until that sequence succeeds.

## Layout

```
patches/       Ordered patches for the pinned upstream source
docs/          Reproducible compatibility notes and protocol observations
```

See [UPSTREAM.md](UPSTREAM.md) for the exact source baseline and how to apply
the series.
GPL-2.0-compatible ejabberd MIX core:1 modernization patches and interoperability tests
