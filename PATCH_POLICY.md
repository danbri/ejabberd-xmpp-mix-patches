# Patch documentation and interoperability policy

This repository carries protocol patches, so a locally successful test is not
enough. A change can make one client work while silently breaking a legacy MIX
client, message archiving, multi-resource delivery, or another XMPP server's
expectations. Each patch therefore has to explain both its intended correction
and the compatibility boundary it creates.

## Required patch record

Before adding a patch to `patches/series`, record all of the following in its
commit message and, when more space is useful, in a linked investigation note:

1. **Observed problem and evidence** — the concrete failing stanza or behavior,
   affected versions, and the trace, test, or source inspection that isolates
   the cause. Distinguish facts from hypotheses.
2. **Protocol expectation** — the relevant XEP revision and namespace or server
   contract. State whether the behavior is required, recommended, optional, or
   an implementation choice.
3. **Exact change** — which control flow, data, or stanza changes, including
   what remains deliberately unchanged.
4. **Status-quo compatibility** — behavior before and after the patch for both
   the failing case and previously working cases.
5. **Interoperability and operational risks** — legacy namespace handling,
   other clients and servers, MAM/archive effects, duplicate or lost delivery,
   multi-resource behavior, persistence, performance, security, and rollback,
   as applicable. Explicitly write `none identified` only after considering
   these categories.
6. **Verification** — focused regression tests plus an end-to-end matrix with
   named server/client versions. Include negative tests that guard the boundary
   of any newly accepted input.

## Inline source comments

Add a concise comment beside code when the interoperability reason would not be
obvious from the Erlang alone. The comment should say why the branch or explicit
namespace is necessary and which compatibility behavior it preserves. Do not
turn comments into a history log; put lengthy evidence and alternatives in the
investigation note.

## Scope and review rules

- Keep one independently reviewable protocol correction per patch. Split
  archive-policy changes from routing fixes even if both were discovered in the
  same trace.
- Do not broaden namespace matching beyond namespaces that the module actually
  advertises and supports.
- Preserve a previously supported legacy path unless the patch explicitly
  documents its removal and migration consequences.
- Keep discarded hypotheses in the investigation note so temporary workarounds
  do not survive after their premise has been disproved.
- Do not submit upstream merely because a downstream patch works. Upstream
  submission is a separate decision after the patch record and interoperability
  matrix are complete.
- Keep live deployment identity and state out of review artifacts. Patch files,
  tests, Docker/Compose files, documentation, and build contexts must not carry
  account names, JIDs, credentials, transcripts, password hashes, or database
  exports from a running pilot. Synthetic source-level fixtures must be plainly
  non-live and contain no reusable secret.

## Commit-message template

```text
Short description of the observable correction

Problem and evidence:
...

Protocol expectation:
...

Change:
...

Status-quo compatibility:
...

Interoperability and operational risks:
...

Verification:
...
```
