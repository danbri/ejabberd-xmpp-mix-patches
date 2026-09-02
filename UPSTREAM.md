# Upstream baseline

Patch series `26.07` applies to:

- upstream: `https://github.com/processone/ejabberd.git`
- tag: `26.07`
- resolved commit: `413e7faee111028b7630523db82f7812ae285261`
- XMPP codec dependency: `xmpp` 1.13.4

Apply only the acceptance-gated series in a clean upstream checkout:

```sh
git clone --branch 26.07 https://github.com/processone/ejabberd.git ejabberd
cd ejabberd
while IFS= read -r patch; do
  git am "/path/to/ejabberd-xmpp-mix-patches/patches/$patch"
done < /path/to/ejabberd-xmpp-mix-patches/patches/series
```

The local container workflow intentionally uses `patches/reviewer-series`,
which also includes downstream candidates that have not passed every upstream
acceptance gate. Keeping the two lists distinct prevents a successful demo
image from silently promoting a candidate patch.

The patches are GPL-2.0-or-later compatible because they modify GPL-2.0-or-later
ejabberd source. They do not alter the licence of the separate portable MIX
specification or conformance work.

## Compatibility baseline

The 26.07 image is current, and its bundled `xmpp` codec already recognises
`urn:xmpp:mix:core:1`. The gap is feature completeness: `mod_mix` only
negotiated `messages` and `participants` subscriptions, and rejected retrieval
of the standard `info` node. It also rebuilt the PAM `client-join` response
with the core namespace, rather than preserving `urn:xmpp:mix:pam:2`.
Both behaviours match the 2023 report in
[ejabberd issue 4006](https://github.com/processone/ejabberd/issues/4006),
which its reporter closed without a fix; this series has not yet been
reported or submitted upstream. XEP-0369 version 0.14.6 documents `info` in
the join and discovery flows.

The patch series records only observed, testable corrections. Do not advertise
features merely because a namespace can be decoded.
