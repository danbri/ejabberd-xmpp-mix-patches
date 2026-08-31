# ejabberd XMPP MIX patches

GPL-2.0-compatible modernization patches and interoperability checks for
ejabberd's experimental MIX implementation.

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

`patches/0001-mix-core-1-info-node.patch` is the first narrow correction. It
preserves the required `urn:xmpp:mix:pam:2` namespace in `client-join`
responses, updates the module's declared XEP revision to MIX-CORE 0.14.6, and
implements the mandatory `urn:xmpp:mix:nodes:info` retrieval/subscription path
that the existing module omitted. It is not a claim of complete MIX support.

The test sequence is:

1. build a custom ejabberd 26.07 image with the patch;
2. run it on separate local ports and a separate Podman volume;
3. create and join a channel with BeagleIM 6.0.1;
4. retrieve participants and channel information; and
5. exchange a groupchat message between two pilot accounts.

The existing live pilot is not replaced until that sequence succeeds.

## Layout

```
patches/       Ordered patches for the pinned upstream source
docs/          Reproducible compatibility notes and protocol observations
```

See [UPSTREAM.md](UPSTREAM.md) for the exact source baseline and how to apply
the series.
GPL-2.0-compatible ejabberd MIX core:1 modernization patches and interoperability tests
