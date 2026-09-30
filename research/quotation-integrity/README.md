# Quotation-integrity operator guide

## Status and boundary

The source-pinned core and quotation-report CLI are implemented. The final combined Synoptics scoped regression run passed **272 tests**; the separate unchanged Sweetbrier consumer suite passed **14 tests**. Real producer/consumer CLI checks and the frozen synthetic conformance run passed. **Independent reviewer-agent code reviews passed for the recorded source hashes. The report-only software milestone is verified; this is not a production-security certification or live enforcement integration.**

`src/models/quotation_verifier.py` compares quoted text with a pinned local source snapshot. `src/pipeline/quotation_review.py` wraps results in the existing `synoptics-defense/0.1` report envelope. Sweetbrier's standalone `synoptics_review.py` accepts that envelope only as untrusted, human-review-required metadata. No database, network client, autonomous orchestrator, or promotion hook is involved in this route.

A textual match does not establish contextual support, source authenticity, source truth, safe instructions, or deployment permission. Every receipt retains `semantic_support="not_assessed"`, `source_truth="not_assessed"`, `deployment_authorized=false`, and `requires_human_review=true`.

## Prepare inputs

The operator explicitly selects a local UTF-8 source file and two local JSON files. Paths are not taken from imported peer text. Use trusted local paths; spelling checks and bounded reads are **not an OS sandbox** against network mounts, junctions or hostile filesystem races.

A staged paper's `paper.txt` is a suitable source. Copy its expected text digest from a separately trusted intake record; use the literal source version. The quotation adapter does not independently authenticate an intake record, retrieve a URL, validate a PDF extraction, or endorse a paper's claims.

`claims.json` is a nonempty array, at most 64 records:

```json
[
  {
    "claim_id": "claim-1",
    "swarm_id": "own-lab",
    "agent_id": "worker-1",
    "quote_text": "The exact text to check.",
    "quote_kind": "direct",
    "parent_evidence_refs": ["intake:source-v1"]
  }
]
```

- `quote_kind`: exactly `direct` or `paraphrase`. Neither permits semantic approval.
- IDs and parent references: ASCII letters/digits plus `_ . : -`, 1–128 characters. Claim IDs must be unique in the request; parent references are unique, at most 16 per claim.
- Optional `source_span: [start, end]`: half-open **Unicode codepoint** offsets into the original decoded source, not bytes, graphemes, or JavaScript UTF-16 indexes. The complete selected span is compared; it is not searched for a more convenient subspan.
- Each quote is at most 20,000 codepoints. Empty quote/source/selection abstains.
- Parent references are preserved as `lineage_status="declared_only"`. This does not verify their existence, independence, chronology, graph acyclicity, or authorship.

`quotation-manifest.json` must contain exactly these fields:

```json
{
  "schema_version": 1,
  "source_ref": "source:independently-identified-artifact",
  "source_version": "v1",
  "scope": "own",
  "evidence_kind": "observed",
  "authorization_ref": "operator:local-review",
  "analysis_allowed": true,
  "source_sha256": "<exact lowercase SHA256 of source bytes>",
  "claims_sha256": "<exact lowercase SHA256 of claims.json bytes>",
  "normalization": "none"
}
```

The angle-bracket strings are documentation placeholders, not valid hashes. The caller separately supplies the exact SHA256 of the final manifest bytes. Do not silently recompute a supposedly independent pin from an untrusted replacement and call that verification.

Allowed scope/evidence pairs: `own/observed`, `authorized_external/observed`, `synthetic/synthetic`. `analysis_allowed` must be the boolean `true`. An authorization reference is an operator assertion, **not a cryptographic signature or independent proof of consent**. Constructed claims/intentional mutations, including tests against a real paper, remain labelled synthetic.

Metadata labels (`source_ref`, `source_version`, `authorization_ref`) must be unmodified, nonblank strict UTF-8 strings of at most 512 codepoints, with no Unicode control (`Cc`), format (`Cf`), line-separator (`Zl`) or paragraph-separator (`Zp`) characters. These label restrictions do not strip or reject those characters in quoted/source bodies.

Normalization is `none` by default in the core, but must be explicit in the manifest. The only alternative is `ascii_whitespace`: collapse runs of ASCII space/tab/CR/LF to a single space, with no trimming. There is no case folding, punctuation removal, dehyphenation, NFC/NFKC, or Unicode-whitespace folding.

## Run the producer

From `C:/Users/Vivian/Desktop/Synoptics`, using the dedicated interpreter:

```bash
"C:/Users/Vivian/AppData/Local/hermes/research/synoptics-defense/venv/Scripts/python.exe" -B -m src.pipeline.quotation_review \
  --source "C:/path/to/paper.txt" \
  --claims "C:/path/to/claims.json" \
  --manifest "C:/path/to/quotation-manifest.json" \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --output "C:/path/to/new-report.json"
```

Use exact option names; abbreviations are rejected. The output parent must exist and the report must be a new file. Successful execution returns JSON with `report_sha256`; malformed/tampered input or an existing output returns exit 2 with a bounded generic rejection. Source, claims and manifest are read once into bounded snapshots. Limits are 2,000,000 source bytes, 524,288 claim-file bytes, 65,536 manifest bytes, and 64 JSON container levels. Duplicate keys, nonfinite numbers and invalid UTF-8 are rejected.

The report excludes quote/source bodies and decoded payloads. It retains identifiers, source labels, hashes and offsets, which can still disclose information. Treat these reports as potentially sensitive; they are not an anonymization guarantee. Source-code hashes identify files on disk, not authenticated execution.

## Read the receipt states

| Status | What it establishes |
|---|---|
| `exact_source_match` | Full raw quote occurs in the supplied source, or equals the entire explicit span. Without a span only the first occurrence is reported. |
| `normalized_source_match` | Full quote matches under the explicitly selected ASCII-whitespace policy; original offsets are preserved. Not raw verbatim identity. |
| `approximate_candidate` | Bounded global raw-codepoint comparison suggests the selected scope for review. `candidate_spans` is separate from precise `source_spans`. |
| `not_found` | No precise match and no candidate under the declared strategies; not exhaustive semantic/fuzzy-substring search. |
| `insufficient_data` | Empty input/selection or comparison work exceeds its bound. Check coverage/reason; this is not evidence of safety or falsity. |

Approximation uses global raw-character Levenshtein comparison of the whole selected scope, not fuzzy substring retrieval. It abstains above 250,000 comparison cells. Exact and requested normalized lookup inspect the supplied scope without silent prefix truncation. `coverage.complete` describes the declared strategies only. Numerical similarities are lexical heuristics, not calibrated probabilities.

Legacy quotation APIs no longer produce VERIFIED/tampered/hallucinated/semantic-faithfulness conclusions. `is_faithful`, `has_foreign_interpolation`, and `interpolation_risk` are null; callers must handle them as unavailable. Interpolation exposes bounded insert/delete/replace candidates with offsets, not hidden payloads. Token alignment caps at 1,000 tokens per sequence and 250,000 cells instead of silently truncating; whitespace is not assessed by that token path. A single token exceeding 20,000 codepoints is invalid input and raises a bounded `ValueError`; it does not return the token-count/cell-budget abstention receipt. Callers of the legacy API must handle both rejected input and returned abstentions.

## Hand off to Sweetbrier

```bash
"C:/Users/Vivian/AppData/Local/hermes/research/synoptics-defense/venv/Scripts/python.exe" -B \
  "C:/Users/Vivian/Desktop/DreamLLM/synoptics_review.py" \
  --report "C:/path/to/new-report.json" --sha256 "$REPORT_SHA256"
```

Synthetic reports are rejected by default. For an intentional local fixture, add the exact `--allow-synthetic` option. This only permits review intake; it never grants deployment authority. The consumer verifies the report-byte pin and envelope, not every upstream source or the correctness of the report's analysis. Reports and quoted instructions remain untrusted data.

## Executed evidence

Evidence directory: `C:/Users/Vivian/AppData/Local/hermes/research/synoptics-defense/quotation-milestone/`.

- `combined-final.log`: final scoped Synoptics run, 272 passed. Database-writing stress tests deliberately excluded.
- `adapter-01-red.log` through `adapter-14-green.log`: original sequential producer RED/GREEN evidence (82 tests). `review-fix-1/` adds 22 Unicode-label regression cases; the corrected producer suite passed 104 tests.
- `core-evidence/`: 31 core tests, 17 RED/GREEN cycles and supplemental deterministic checks.
- `presentation-evidence/`: detector metadata and pure dashboard adapter/AST checks. No live Streamlit/chart startup was performed.
- `conformance-final.json`: all 24 frozen synthetic cases conformed. Current false text-match/verbatim acceptance and rejection of expected matches were zero on this set. The original comparator labelled 10 non-verbatim cases VERIFIED and rejected 6 expected textual matches under its faithful boolean. These are constructed-case counts, not population error rates or a held-out scientific result.
- `final-verification/end-to-end/verification.json`: actual staged paper `2609.19315v1` text digest checked against its intake; one exact excerpt and one intentional alteration produced exact/candidate receipts. Producer succeeded, default synthetic intake rejected, explicit fixture intake yielded untrusted human-review-required metadata, changed source/report pins rejected, overwrite refused. Original source/intake/report bytes remained unchanged.
- `final-verification/defense-handoff.json`: original trace producer also passed the real Sweetbrier handoff; synthetic admission remained explicit, authority/trust false, and overwrite refused.
- `final-verification/consumer-tests.log`: 14 unchanged Sweetbrier intake tests passed. `final-verification/guarded-api.json` records the actual guarded call; `protected-after.json` records 180 protected files unchanged.
- `independent-core-rereview/findings.json` and `independent-presentation-review/findings.json`: both scoped code reviews passed. The initially reported Unicode-label contract mismatch (L1) was corrected with RED/GREEN evidence and independently reproduced/rechecked. `parent-final-review-check.json` binds approval to the live source bytes.
- `final-verification/verification.json`: aggregate acceptance receipt, exact artifact/source hashes and scope exclusions.
- `run_conformance.py` and `run_end_to_end.py` are retained reproducer scripts outside the repository. They preserve results by refusing to overwrite existing output locations.

## Remaining gates

The scoped software and independent code-review gate is complete. Real-world effectiveness still requires consented/licensed, human-adjudicated cases, grouped document/conversation splits, a frozen calibration/holdout design, source-span and semantic-support scores kept separate, and independent reproduction. Later shadow-mode real-swarm analysis requires an explicit trace selection and authorization; no live collection was configured.

This patch does not repair the unrelated graph/email tooling or the permissive legacy trace ingestor/HTML report route. Use the bounded report-only CLIs above, not `swarmtrace_cli.py`, for this milestone's evidence boundary. No whole-application or operating-system sandbox claim is made.
