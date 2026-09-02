# Work queue

## Mandatory gate for every patch

- [ ] Explain inline and in the patch record what the patch actually changes.
- [ ] Name the observed problem and evidence it solves; do not preserve guesses
      as conclusions.
- [ ] Cite the protocol behavior and supported namespace boundary.
- [ ] Describe compatibility with the unpatched status quo, including behavior
      that already worked and must remain working.
- [ ] Describe interoperability and operational risks, including legacy clients,
      other servers, MAM/history, live delivery, multi-resource delivery,
      duplication, loss, performance, security, and rollback where relevant.
- [ ] Add focused positive and negative regression tests.
- [ ] Complete an end-to-end test against the pinned server and named clients.
- [ ] Audit the patch, container files, fixtures, and notes for live account
      names, JIDs, credentials, transcripts, or copied database state; none may
      enter this repository.

The checklist is defined in detail by [PATCH_POLICY.md](PATCH_POLICY.md). A
patch is not ready for `patches/series` while any applicable item is unresolved.

## Patch 0001 (information node and PAM namespace)

- [x] Patch record rewritten under the PATCH_POLICY headings.
- [x] Info node readable during discovery on non-hidden channels; hidden
      channels answer participants only.
- [x] Form carries FORM_TYPE, Name and Contact; Description omitted because
      `mod_mix` stores none.
- [x] EUnit `mod_mix_info_test`: 5 tests, 0 failures.
- [ ] Decide whether to add a stored channel description so the form can
      carry the XEP-0369 Description field.

## Current live-delivery investigation

- [x] Package the MIX namespace recognition fix as a narrow candidate patch that preserves
      locally constructed empty-namespace records, accepts explicit Core 0 and
      Core 1, and rejects unknown or unrelated namespaces. Keep it out of
      `patches/series` until the remaining acceptance boundary is complete.
- [x] Record the runtime proof that `xmpp:has_subtag(Message, #mix{})` does not
      match a decoded `#mix{xmlns = <<"urn:xmpp:mix:core:1">>}` element.
- [x] Record the runtime proof that the same predicate does match the
      empty-namespace record locally constructed by `mod_mix`.
- [x] Keep the disproved cache hypothesis and removal of its workaround in the
      investigation note.
- [x] Run focused EUnit tests for local empty-namespace, Core 0, Core 1, unknown
      namespace, and non-MIX messages.
- [x] Separate live-routing correction from any participant-copy MAM/archive
      policy change so each can be reviewed and rolled back independently.
- [x] Isolate BeagleIM 6.0.1's missing live-message display to the channel
      server's Core 0 output versus Martin 3.2.4's exact Core 1 input filter.
- [x] Package explicit Core 1 channel-message emission as separate patch 0003,
      with its legacy Core-0-only client risk stated inline and in the patch.
- [x] Prove immediate, visible web-to-BeagleIM and BeagleIM-to-web delivery
      between distinct accounts after patch 0003.
- [x] Prove one fresh browser message fans out live to BeagleIM on macOS and
      Siskin IM on iOS after promotion to the normal client ports.
- [ ] Record the exact Siskin IM version and repeat its named-client test for
      versioned acceptance evidence.
- [ ] Complete the remaining live-delivery matrix: exact multi-resource copy
      count, no-mapping rejection, and an end-to-end legacy Core 0 check remain.
- [x] Keep all work downstream for now; do not open an upstream issue or pull
      request without a separate decision.
- [x] CI: apply both series on the pinned commit, check policy headings on
      accepted patches, build and run the patch EUnit modules, ShellCheck the
      tooling.
