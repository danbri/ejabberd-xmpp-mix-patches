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
- Raw loopback probe (`tools/mix-probe.py`), 2026-09-02, against the image
  built from `reviewer-series` at this revision (upstream 413e7fa, Erlang/OTP
  28.5.0.4 in the container): all 9 checks pass, including the pre-join info
  read on a non-hidden channel, the `urn:xmpp:mix:pam:2` client-join result
  listing the info node, and the form fields FORM_TYPE, Name, Contact. The
  same probe against the image built from the previous 0001 revision fails
  at the pre-join info read, as expected.
- Not yet re-run for this revision: BeagleIM 6.0.1 join and info display.
  The earlier revision passed that check; the wire format of the join and
  echo is unchanged by this revision, only the info form and its access.
