# Patch 0003: emit MIX Core 1 channel metadata

Status: downstream candidate; deliberately not yet in `patches/series`.

## Observed failure

With patches 0001 and 0002, BeagleIM 6.0.1 could discover and join the test
channel. Live routing also worked: a message sent by Beagle arrived immediately
in the connected browser, and a browser submission received its server echo.
Nevertheless, Beagle showed no new live messages and only exposed older content
after a history/rejoin path.

The server trace isolated the protocol boundary. It reflected otherwise valid
groupchat messages with:

```xml
<mix xmlns='urn:xmpp:mix:core:0'>...</mix>
```

even though the client had joined with Core 1 inside PAM 2.

## Client-source evidence

BeagleIM 6.0.1 build 196 resolves Martin 3.2.4 at revision
`1d70e9e7eb51a7faa500832be6400a39f86083f7`.

In that exact revision:

- `MixModule.CORE_XMLNS` is `urn:xmpp:mix:core:1`;
- the module's stanza criteria require a groupchat message with a direct
  `<mix>` child in that exact namespace;
- `Message.mix` searches only that exact namespace; and
- Beagle stores and displays channel messages received through Martin's MIX
  `messagesPublisher`.

The Core 0 server stanza therefore cannot enter Beagle's MIX message publisher.
This is a source-and-wire match, rather than an inference from its UI.

## Protocol basis

[XEP-0369 version 0.14.6](https://xmpp.org/extensions/xep-0369.html) defines
Core 1 as `urn:xmpp:mix:core:1`. Its message archive and participant-reflection
examples qualify the `<mix>` metadata with Core 1 (examples 28 and 29), and a
MIX service advertises Core 1 as its required service feature.

Ejabberd already advertises and handles Core 1. The incompatible output came
from constructing `#mix{}` without an `xmlns`: the bundled xmpp codec then used
its legacy first-namespace/default encoding, Core 0.

## Exact change

Patch 0003 adds a small `channel_mix/2,3` constructor and uses it at the two
existing `process_mix_message/1` construction sites:

- the archived/ordinary recipient metadata; and
- the sender copy, which additionally retains `submission_id`.

Both constructors set `xmlns = ?NS_MIX_CORE_1`. No routing, membership, archive,
fan-out, address, or body logic changes.

## Compatibility and risk

Status quo before the patch:

- tolerant clients such as the pilot web UI displayed Core 0 messages;
- Core 1-only Beagle/Martin accepted the join but discarded live messages;
- MAM still contained the content, which made reconnect/history symptoms
  misleading.

After the patch, modern Core 1 clients recognize the channel metadata. The
intentional risk is that a legacy Core-0-only client may now discard messages.
Ejabberd does not currently persist the Core revision negotiated by each
participant, so choosing output per recipient would be a larger storage and
routing design. Patch 0003 makes the current XEP path interoperable and leaves
that legacy strategy visible for follow-up.

Rollback is a single-patch revert. It restores Core 0 output without changing
database state.

## Verification

- Focused EUnit: ordinary and sender-copy constructors both produce Core 1;
  sender copy retains `submission_id`. Result: `2 tests, 0 failures`.
- Clean application: the mail patch applies to candidate patch 0002 commit
  `4b96f51d031bab456cff62d1a8b6876fa9304742`.
- Production container build: passes on pinned Erlang/OTP `28.5.0.4`.
- Authenticated raw probe: PAM 2/Core 1 join, immediate server echo containing
  Core 1, and MAM retrieval of the same unique message containing Core 1 all
  pass.
- Named-client test: BeagleIM 6.0.1 and the browser rejoined as distinct
  accounts and rendered new messages immediately in both directions without a
  reconnect/history fallback.
- Default-port fan-out test: one fresh browser submission appeared immediately
  in both BeagleIM on macOS and Siskin IM on iOS. The Siskin build number still
  needs to be recorded before treating it as versioned acceptance evidence.

OMEMO remained disabled during these tests. End-to-end encryption is a
separate client and device-state interoperability layer; these results isolate
MIX routing and Core 1 metadata behavior.

Remaining before series/upstream consideration: exact multi-resource fan-out,
negative no-mapping delivery, and an end-to-end legacy Core 0 client/probe.
