# Patch 0001: information node and PAM namespace

Status: in `patches/series`.

## Observed failure

Against ejabberd 26.07, a PubSub items request for
`urn:xmpp:mix:nodes:info` returned `feature-not-implemented`, a join that
listed the info node was narrowed to messages and participants, and the
client-join result carried `urn:xmpp:mix:core:1` instead of the client's
`urn:xmpp:mix:pam:2`.

## Change

See the patch record for the full PATCH_POLICY entry. In short: the info
node is negotiable and served as one item, id `current`, holding a form
with `FORM_TYPE`, `Name` and `Contact`; non-hidden channels answer any
requester, hidden channels answer participants only; mod_mix_pam threads
the client's PAM namespace through to the result.

## Verification

- EUnit `test/mod_mix_info_test.erl`: 5 tests, 0 failures (Erlang/OTP 29,
  and OTP 28 in CI).
- Clean application on the pinned upstream commit (CI, `git am`).
- Raw loopback probe (`tools/mix-probe.py`): pending for this revision; the
  record is appended below when it runs against the container image built
  from the current `reviewer-series`.
