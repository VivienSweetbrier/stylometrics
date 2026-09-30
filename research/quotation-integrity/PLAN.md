# Quotation-integrity conformance plan

## Scope

This directory holds constructed local fixtures, not observed swarm behavior. `synthetic-cases.json` contains 24 cases grouped into 8 document families. It is a conformance/regression set, not an unseen statistical holdout. Its frozen SHA256 is `5e36a57df4bd146da7438f7d8a460e8290af1744198d576fc1e7f7ff2dd91cb1`.

Expected outcomes were fixed before the cross-component benchmark run. `not_a_text_match` permits `approximate_candidate`, `not_found`, or `insufficient_data`, but never an exact/normalized match. An exact quote embedded in misleading context is deliberately still a textual match; semantic support must remain `not_assessed`.

## Comparison

Compare the inspected pre-change quotation module, deterministic exact matching, and the new source-pinned receipt interface on these same fixtures. Do not treat differences on these constructed cases as estimated real-world error rates. Record input, code and environment digests, per-case outputs, actual runtimes, false match acceptance, rejection of expected textual matches, abstention and conformance failures. Keep a declared-normalization match distinct from byte-for-byte/verbatim matching.

Do not edit expected results to obtain a pass. A discovered fixture error requires a separately versioned correction and retained original results. Keep all derived cases from a document/conversation in the same split when a separately reviewed empirical benchmark is later designed.

## Intended report-only boundary

An operator-authored quotation manifest binds source bytes, claim bytes, source identity/version, scope, normalization and analysis attestation. The CLI caller separately pins the exact manifest bytes. These pins establish content identity only; metadata does not prove origin, authorship, consent, execution history or semantic truth.

The report preserves source/quote digests, codepoint offsets, declared parent references, matching status, coverage and review requirements. Raw quotation/source bodies are excluded. Parent links remain `declared_only`; this is not an authenticated contribution DAG. Nothing in a quoted instruction can grant permissions.

## Status

The source-pinned core and quotation-report CLI are implemented and their scoped regression, frozen synthetic conformance and real local producer/consumer handoff checks passed. The scoped independent code reviews passed on the recorded source versions. See `README.md` for the executable operator guide and exact verified scope; none of these checks establishes empirical effectiveness or authorizes live enforcement.
