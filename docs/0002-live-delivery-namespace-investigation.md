# MIX live-delivery namespace investigation

Date: 2026-09-01

Status: corrected candidate built and unit-tested; authenticated loopback and
Tailnet browser clients have passed sender live delivery on OTP 28.5. A
BeagleIM account also delivered a message live to the browser. Reverse visible
delivery in BeagleIM and the remaining boundary tests are still pending before
inclusion in `patches/series`.

## Scope and pinned versions

- ejabberd tag `26.07`, commit
  `413e7faee111028b7630523db82f7812ae285261`
- bundled `xmpp` codec `1.13.4`
- XEP-0369 MIX-CORE `0.14.6`, namespace `urn:xmpp:mix:core:1`
- XEP-0405 MIX-PAM `0.5.3`, namespace `urn:xmpp:mix:pam:2`
- browser client using Strophe over WebSocket
- BeagleIM 6.0.1 as a secondary interoperability client

Both XEPs are Experimental. This work is therefore an interoperability pilot,
not a claim that MIX is production-stable.

## Observed problem

A client could authenticate, create `factoidal@mix.foafmixer.test`, join it via
MIX-PAM, and send a groupchat message. The channel archived the message, so it
became visible after a client resynchronized or rejoined, but neither the sender
nor another online participant received the message live.

This separated history success from live-delivery failure: channel acceptance
and channel MAM storage worked, while participant-server forwarding did not.

## Expected delivery path

XEP-0405 section 2.2 says that a channel sends a groupchat message to the
participant's bare JID. The participant server then replaces that bare JID with
the full JID of each applicable online MIX client and forwards a copy. See:

- <https://xmpp.org/extensions/xep-0405.html#usecase-messages-from-mix>
- <https://xmpp.org/extensions/xep-0369.html>

In ejabberd, `mod_mix_pam:bounce_sm_packet/1` is the hook that recognizes this
bare-JID MIX message, verifies that the account joined the sending channel, and
routes copies to online resources.

## Evidence that isolates the namespace defect

The following were observed against the isolated patched-test server:

1. The channel accepted sent messages and assigned archive identifiers.
2. The messages were recoverable through history after reconnect/rejoin.
3. Runtime tracing showed the channel multicast a bare-JID message toward each
   participant account.
4. With an explicitly namespaced MIX record, the participant-server hook
   returned its original `bounce` accumulator rather than the `pass` result
   used after successful forwarding.
5. A direct lookup using the exact message `to` and `from` JIDs returned the
   stored MIX-PAM channel mapping. Argument order and the loaded BEAM code were
   also checked, excluding a missing mapping or stale module.
6. For the decoded message record, the runtime predicates returned:

   ```erlang
   xmpp:has_subtag(Message, #mix{})
   %% false

   xmpp:has_subtag(Message,
                   #mix{xmlns = <<"urn:xmpp:mix:core:1">>, ...})
   %% true
   ```

7. The pinned codec implementation shows why. `xmpp:has_subtag/2` obtains the
   template element's name **and namespace**, and `match_tag` requires both to
   match. A bare `#mix{}` record has `xmlns = <<>>`; it is not a wildcard for a
   decoded Core 0 or Core 1 element. See the pinned codec source:
   <https://github.com/processone/xmpp/blob/1.13.4/src/xmpp.erl> and
   <https://github.com/processone/xmpp/blob/1.13.4/src/xmpp_codec.erl#L123-L128>.

The failing ejabberd predicate was:

```erlang
xmpp:has_subtag(Msg, #mix{})
```

Valid decoded MIX records carry their actual namespace. Consequently this
predicate prevents live forwarding for explicitly namespaced Core 0 and Core 1
records.

A second trace exposed an equally important status-quo constraint. The local
`mod_mix` channel constructs a `#mix{}` record and routes it in memory, without
an XML codec round trip. That record retains `xmlns = <<>>`, and the original
predicate correctly matches it. An early candidate that replaced the original
predicate with only explicit Core 0/1 checks therefore regressed local channel
delivery. The corrected candidate retains the old check and extends it.

## Minimal correction

Patch 0002 changes only the recognition predicate. It keeps the status-quo
check for locally constructed records and adds the two explicit MIX-CORE
namespaces already supported by ejabberd's bundled codec:

```erlang
xmpp:has_subtag(Msg, #mix{}) orelse
xmpp:has_subtag(Msg, #mix{xmlns = ?NS_MIX_CORE_0}) orelse
xmpp:has_subtag(Msg, #mix{xmlns = ?NS_MIX_CORE_1})
```

It deliberately does not:

- change the namespace emitted by the MIX channel;
- change MIX-PAM mappings or cache behavior;
- add or change MAM storage;
- change which resources the existing forwarding branch selects;
- change joins, leaves, roster behavior, or WebSocket handling; or
- accept an unknown namespace.

Those boundaries make the cause and rollback independently reviewable.

## Status-quo compatibility and risks

### Preserved behavior

- The empty namespace used by locally constructed `mod_mix` records remains
  accepted, preserving existing local delivery.
- Explicit Core 0 becomes accepted, matching ejabberd's legacy wire support.
- Core 1 becomes accepted, matching the current XEP and codec support.
- An account still needs an existing MIX-PAM mapping for the sending channel.
- Malformed, unrelated, and unknown namespace elements do not enter the MIX
  forwarding branch.
- Message output, persistence, cache, and MAM behavior are unchanged.

### Behavior intentionally activated

Before the patch, valid namespaced MIX messages could not reach the existing
resource-forwarding branch. After the patch, they can. That branch sends to all
online resources returned by `ejabberd_sm:get_user_resources/2`.

XEP-0405 says forwarding should be limited to online clients that advertise MIX
capability. ejabberd's existing branch does not perform that filtering. This is
a pre-existing conformance gap that becomes observable once forwarding works.
It should be investigated as a separate patch rather than hidden inside this
namespace fix. For the pilot, accounts should be used only by MIX-aware clients.

Multiple resources are expected to receive one copy each. This can expose
client-side duplicate-display bugs or multiple simultaneous sessions, but the
patch does not itself duplicate a message to the same resource.

### Archive behavior remains separate

XEP-0405 contains wording that needs careful treatment: its overview and
message-flow text describe participant-server MAM storage, while section 2.11
describes local archive support as optional and associates it with the
`urn:xmpp:mix:pam:2#archive` feature. The current ejabberd module does not
advertise that archive feature. Adding participant-account MAM storage is
therefore a separate policy and conformance patch with duplicate/history risks;
it is not required to prove this routing predicate correction.

### Emitted Core namespace remains separate

The codec's empty `#mix.xmlns` encoding fallback selects its first supported
namespace, Core 0. Updating `mod_mix` to explicitly emit Core 1 is desirable for
the current XEP but may affect Core-0-only clients. That output change is kept
out of patch 0002 so it can receive its own compatibility analysis and test. It
is now candidate patch 0003; see
[0003-core-1-message-emission.md](0003-core-1-message-emission.md).

### Operational risk and rollback

The runtime cost is at most two additional namespace predicates in a narrow
groupchat hook. No new external input is trusted beyond two already-supported
namespaces, and the existing channel-membership check remains in place.
Rollback is a single-patch revert and restores the original locally constructed
record behavior while removing explicit-namespace support.

## Discarded hypotheses

These were useful leads but do not explain the server hook's proven bounce:

- the unregistered `foafmixer.test` DNS name;
- Tailscale routing, TLS, or the WebSocket proxy;
- authentication or account passwords;
- the browser UI's stale visual connection/join state;
- BeagleIM rendering, delayed history, or its separate dispatch crash;
- an old ejabberd container tag;
- a stale loaded BEAM module;
- reversed channel-mapping lookup arguments;
- a missing MIX-PAM mapping;
- stale `mod_mix_pam` cache data; and
- the channel MAM hook return value.

In particular, the cache-bypass workaround tried during diagnosis has been
removed. Direct backend lookup and loaded-bytecode inspection showed the
mapping was present and the branch was never reached because namespace
recognition failed first.

## Prior upstream reports and history

A GitHub issue, pull-request, code, and commit search found no existing report
for the exact `xmpp:has_subtag(Msg, #mix{})` namespace-match defect. The closest
relevant upstream material is:

- [ejabberd #2958](https://github.com/processone/ejabberd/issues/2958) records
  the same bare-JID message drop when `mod_mix_pam` or a PAM join was absent.
  This pilot has the module enabled and its mapping was verified, so that
  report confirms the expected route but does not explain this defect.
- [ejabberd #4006](https://github.com/processone/ejabberd/issues/4006) records
  the incorrect PAM namespace and missing subscription nodes addressed
  separately by patch 0001.
- [ejabberd #4132](https://github.com/processone/ejabberd/issues/4132) is an
  open, unanswered request to update ejabberd's MIX XEP support.
- [ejabberd #4208](https://github.com/processone/ejabberd/issues/4208) records
  delivery blocked by `mod_block_strangers`; that module is not enabled in the
  pilot.
- [ejabberd commit 648245e](https://github.com/processone/ejabberd/commit/648245e974b142e6d9f3c4fd40771c87fadc6c9b)
  added Core 0/1 and PAM 0/2 IQ handling in 2022, while leaving the bare-message
  hook predicate unchanged.
- [processone/xmpp PR #64](https://github.com/processone/xmpp/pull/64) added
  namespace retention so replies can use the request protocol version, and
  [PR #84](https://github.com/processone/xmpp/pull/84) later made participant
  items emit Core 1. These changes support treating explicit namespaces as a
  normal codec representation rather than an unknown extension.

This search is evidence about prior reporting, not proof of correctness; the
runtime and regression tests above remain the basis for the candidate patch.

## Verification record

Focused EUnit tests on Erlang/OTP 29.0.5, applied after patch 0001:

- locally constructed empty-namespace MIX record: accepted;
- Core 0 MIX element: accepted;
- populated Core 1 MIX element: accepted;
- the old bare-record predicate against that Core 1 element: demonstrably
  false;
- unknown MIX namespace: rejected; and
- unrelated subtag: rejected.

Result: `5 tests, 0 failures` (the Core 1 test includes both the old-predicate
regression assertion and the corrected-predicate assertion).

The complete candidate image also compiled successfully using the repository's
pinned Erlang/OTP `28.5.0.4` container build.

An authenticated plaintext-loopback client then connected to the isolated
server, bound a resource, joined `factoidal@mix.foafmixer.test` through
MIX-PAM, sent a unique `livefix-auto-*` message, and received the reflected
channel message immediately without reconnecting. It then queried the channel
through MAM with an RSM newest-page request and recovered that same message,
including the expected MAM, forwarding, delay, and MIX Core 1 namespaces. This
proves the corrected candidate preserves the local in-memory representation
through live routing without breaking channel archive retrieval.

The browser client then connected over Tailnet WebSocket to the same isolated
server on port 15281, joined through PAM, sent `livefix-browser-1`, and displayed
the server-delivered echo immediately in its Live Messages pane. No reconnect
or history reload was needed.

Finally, BeagleIM 6.0.1 sent `bloop` as a different account and the connected
browser displayed it live. BeagleIM did not display its own message in its
conversation pane while the server emitted Core 0 metadata. Candidate patch
0003 changed that output separately. With patches 0001-0003, BeagleIM 6.0.1
and the browser subsequently rendered fresh messages immediately in both
directions without reconnecting or falling back to history.

End-to-end acceptance still requires:

- [x] sender receives its reflected message live without reconnecting;
- [x] a distinct MIX-aware account receives a message live (BeagleIM to browser
      direction);
- [x] web-to-BeagleIM delivery is displayed live by BeagleIM with patch 0003;
- [ ] each active resource receives exactly one copy;
- [ ] no delivery occurs for an account without the channel mapping;
- [x] channel MAM history remains queryable and includes the newly sent message;
- [ ] Core 0 input remains deliverable; and
- [x] the existing join/info behavior from patch 0001 remains working in the
      combined 0001-0003 test image.

## Upstream status

This is downstream patch work only. No issue comment, pull request, or other
upstream submission should be made until the patch record and end-to-end matrix
are complete and there is a separate decision to submit it.
