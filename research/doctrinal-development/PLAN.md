# Newman, doctrinal development, and auditable agent communication

**Status: research plan, not a finding of continuity or rupture.** No historical claim set has yet been adjudicated and no doctrinal classifier has been validated. This is an additive research track; it does not change Synoptics runtime behavior or authorize live agent experiments.

## 1. Research aim

Reconstruct the argument and evidence of John Henry Newman's *An Essay on the Development of Christian Doctrine*, then test an explicit adaptation of his method against a concrete question:

> In what senses, on which propositions, and under which documented interpretations are the Roman Catechism (Catechism of Trent), the texts of Vatican II, and the Catechism of the Catholic Church mutually compatible? Which changes qualify as faithful development under Newman's criteria, and which remain tensions or possible contradictions?

Use the resulting evidence-and-revision discipline as an experimental model for transparent, consensual agent-to-agent communication. The transfer is a hypothesis to test, not a claim that religious institutions and software agents are equivalent.

The user supplied the connection between historical doctrinal development and agent communication, and the Trent–CCC comparison as a route into the Vatican II question. This document proposes an operational research design for those ideas.

### Separate questions; do not collapse them into a score

1. **Textual fidelity:** Does the quotation occur in the identified source/version, and what surrounding context was omitted?
2. **Historical transmission:** Is there evidence of citation, borrowing, reception, or an intermediate source? Similar wording alone does not establish direct dependence.
3. **Logical compatibility:** Can the relevant propositions jointly hold under the same evidenced meanings, qualifications, and circumstances?
4. **Development:** Does the later account preserve or change the earlier principles, and what warrants that classification?
5. **Theological authority:** What authority does each passage claim or receive, and which framework supplies that assessment?
6. **Reception and practice:** What happened after a teaching was issued? This is a different study from compatibility of promulgated texts.

Historical descent does not by itself establish logical compatibility. Compatibility does not by itself establish entailment, truth, or legitimate authority. Newman himself illustrates development within a system by calling Eunomianism a development, rather than a corruption, of Arianism; continuity and truth therefore must not be identical labels in our model.[11]

## 2. Why the two catechisms are not sufficient

The Vatican's explanatory dossier identifies the Roman Catechism as the catechism published in 1566, and explicitly distinguishes the CCC from a catechism mandated by Vatican II.[6]

Accordingly, keep these source layers separate:

- **Council of Trent:** actual decrees and canons, with session, chapter/canon, and promulgation metadata.
- **Roman Catechism:** the catechetical exposition, with its own edition, intended audience, and textual history.
- **Intervening teaching:** sources needed to evaluate a particular claimed continuity, including preconciliar material rather than a jump from the sixteenth to the twentieth century.
- **Vatican II:** the promulgated documents themselves, not merely later descriptions of the council.
- **CCC:** a later synthesis with multiple textual versions.
- **Later interpretation and practice:** separate evidence, never silently attributed back to Vatican II.

*Dei Verbum* explicitly discusses development of apostolic tradition; its account is part of the evidence being examined, not an automatic answer to our research question.[8]

**Primary inferential limit:** agreement between the catechisms cannot prove continuity of every Vatican II teaching; disagreement cannot automatically identify Vatican II as its cause. A council-wide conclusion requires an explicit document/topic coverage inventory and examination of the strongest counterexamples.

## 3. Corpus and edition policy

| Layer | Proposed starting material | Required control |
|---|---|---|
| Newman | Chapter V and selected worked arguments in the revised Essay; acquire the first edition for comparison | Distinguish original argument, revision, illustration, quotation, and our operationalization |
| Earlier baseline | Roman Catechism plus the relevant Trent decrees/canons | Do not treat the catechism and council decrees as interchangeable documents |
| Bridge sources | Sources selected by the controversy and citation chain, not only sources favorable to continuity | Record omissions and rival source selections |
| Vatican II | Start with Eucharistic/liturgical and religious-freedom passages; expand to revelation, ecclesiology, ecumenism, and other religions | Bind every proposition to a document and paragraph; retain footnotes and qualifications |
| CCC | Original publication, Latin typical edition, and later revisions as distinct versions | No silently updated web page may stand in for an earlier edition |
| Reception | Official explanations and serious continuity/rupture arguments | Separate an interpretation from the primary text it interprets |

Newman's revised edition acknowledges changes in arrangement and text. Reproducing the original historical argument requires a first-edition witness; the revised online text is not a substitute for that witness.[12]

*Laetamur magnopere* identifies the 1997 Latin typical edition and the earlier 1992 French-language publication. Use these as distinct baseline versions; translations and subsequent updates also require independent version identifiers.[31]

The 2018 explanatory letter concerns a new revision of CCC 2267. Death-penalty teaching is therefore a useful later version-control stress test, but must not be counted as a Vatican II change merely because it appears in today's CCC.[10]

The Fordham Roman Catechism witness explicitly says that its divisions and headings were supplied by the translators. Its headings must not become evidence that the original text asserted a particular proposition or used a particular category.[30]

### Required metadata per textual witness

- Work identity; document kind; issuing body/attributed author; publication/promulgation date; edition/revision date; retrieval date.
- Language; translator; publisher; edition title page or authoritative bibliographic witness; rights/analysis permission.
- Source URL/archive identifier; original-byte digest; extracted-text digest; extraction procedure/version.
- Paragraph/page/section locator; Unicode-codepoint offsets into the exact decoded snapshot; context window; footnotes.
- Editorial additions, translation variants, OCR uncertainty, uncertain dating, disputed attribution, and missing pages.
- Document-level authority metadata **and** passage-level authority assessments with their sources and reviewer disagreements. Do not assume every sentence in a document has an identical theological status.

Retain raw witnesses unchanged. Put normalization and segmentation in derived layers with reversible offset maps. Verify decisive passages against an authoritative original-language edition or scan; an English retrieval hit is only a lead. Metadata and digests establish identification and byte stability, not authenticity or truth by themselves.

## 4. Reproduce Newman before extending him

For each selected argument, construct:

`Newman passage → proposition → cited witness → verified quotation → surrounding context → inferential step → stated conclusion → strongest objection`

Record whether the reconstruction faithfully represents Newman before asking whether it persuades us. Do not silently replace his historical argument with modern premises or treat a model's preferred interpretation as Newman's own.

The seven headings below come from Chapter V. Newman describes the notes as having varying cogency, independence, and applicability; do not turn them into equally weighted, independent numerical tests.[11]

| Newman's note | Proposed historical inquiry | Proposed agent-communication analogue |
|---|---|---|
| Preservation of type | Which defining commitments remain recognizable despite altered expression? | Preserve the declared task and role, not a writing style |
| Continuity of principles | Which underlying principles remain, and which genuinely change? | Make policy/constraint changes explicit and separately authorized |
| Power of assimilation | How are external concepts incorporated without simply replacing the earlier system? | Add evidence with its origin and a documented integration step |
| Logical sequence | What argument connects the earlier commitments to the later formulation? | Attach premises, warrants, assumptions, and counterarguments to a derived claim |
| Anticipation of its future | Are relevant antecedents actually present in earlier witnesses? | Require dated parent evidence; test temporal leakage and hindsight bias |
| Conservative action upon its past | Does the later account preserve, explain, restrict, or undo the earlier commitments? | Keep a readable revision history, with explicit supersession or retraction |
| Chronic vigour | What continuing capacity does the system display, and what competing explanations exist? | Evaluate robustness over repeated authorized handoffs; persistence is not truth |

**Interpretive boundary:** the middle and right columns are our proposed operationalization, not quotations from Newman. Report a qualitative evidence profile for each note: supporting evidence, counterevidence, applicability, assumptions, and unresolved questions. Do not output a single "Newman score" or a probability that a doctrine is true.

## 5. First comparative cases

### A. Eucharistic teaching — proposed baseline

Compare Roman Catechism passages and relevant Trent decrees with *Sacrosanctum Concilium* and corresponding CCC passages. Start with a small set of claims about presence, sacrifice, and participation, not the entire theology of worship.

This is a baseline selection, **not a preassigned continuity verdict**. Keep doctrinal statements separate from disciplinary provisions, ceremonial form, pastoral emphasis, and later liturgical implementation. Those distinctions must themselves be argued from sources, not invoked whenever a difficult case appears.

### B. Religious freedom — proposed hard case

Study the relevant Roman Catechism material, earlier teaching on religion and public authority, *Dignitatis humanae*, and the corresponding CCC passages. Acquire the relevant passages of *Quanta cura* and the *Syllabus* with their context; extend the bridge corpus where the actual arguments require it. These bridge sources and their exact locators remain an acquisition task, not a completed comparison.

*Dignitatis humanae* explicitly distinguishes immunity from coercion in civil society from the moral duty toward true religion and claims to leave that duty untouched.[9]

Make that distinction a testable interpretation, not a shortcut to the result. Ask whether the earlier and later claims address the same subject, kind of right, coercive authority, public/private activity, religious duty, conditions, and limits. Preserve both the strongest sourced reconciliation and the strongest sourced contradiction argument. A source's assertion of its own continuity is evidence of intent/self-description, not independent proof of compatibility.

### Expansion queue after the pilot

- Revelation, Scripture, tradition, and development: *Dei Verbum* and its predecessors.
- Church membership, salvation, and ecclesial identity: *Lumen gentium* and relevant antecedents.
- Ecumenism: *Unitatis redintegratio* and earlier teaching.
- Other religions: *Nostra aetate* and its actual doctrinal antecedents.
- Church authority and episcopal collegiality, including necessary Vatican I bridge texts.
- Postconciliar revisions such as CCC 2267, explicitly outside automatic attribution to Vatican II.
- Earlier centuries and Newman's wider case set, following source chains back through patristic and medieval witnesses.

## 6. The unit of comparison: an argument dossier

Do not compare whole books using one embedding or style distance. One dossier should contain:

1. Exact passages, versioned source identifiers, stable locators, and surrounding context.
2. Quote-match receipts that remain separate from contextual-support judgments.
3. A minimal proposition extraction preserving negation, quantifiers, modality, exceptions, and conditions.
4. Speaker/issuer, addressee, referent, time, jurisdiction, disputed technical terms, and proposition type.
5. Earlier/later/bridge passages and typed relationships: `quotes`, `paraphrases`, `reaffirms`, `clarifies`, `qualifies`, `extends`, `revises`, `contradicts_candidate`, `no_clear_counterpart`.
6. A continuity interpretation, a rupture interpretation, the evidence and assumptions each requires, and the strongest objection to each.
7. Newman's seven-note evidence profile, with `not_applicable` and `undetermined` available.
8. Independent reviewer annotations and an adjudication record that preserves disagreement.

### Verdict vocabulary

- Equivalent or reaffirmed within the declared scope.
- Compatible clarification or extension, with the additional premises stated.
- Changed discipline/application/emphasis, with evidence for that classification.
- Apparent contradiction explained by an evidenced difference of meaning or scope.
- Unresolved tension.
- Candidate substantive contradiction under explicitly matched meanings and scope.
- No clear counterpart / insufficient evidence.

A proposed contradiction must identify the incompatible propositions under the same relevant senses and conditions. A proposed reconciliation must document its distinctions in historical evidence; adding arbitrary qualifications until every pair agrees is not a valid method. Silence or omitted treatment is not a negation. Literal quotation is not endorsement, and historical description is not necessarily a prescription.

## 7. Synoptics reuse and technical boundaries

The current [quotation-integrity operator guide](../quotation-integrity/README.md) describes the source-pinned core, bounded report CLI, exact/declared-normalization receipts, and explicit abstentions. The [existing conformance plan](../quotation-integrity/PLAN.md) separates textual match from semantic support. These are the starting interfaces, not the broader claims in the root README.

- Reuse source pinning, complete-scope exact matching, declared normalization, offsets, and review-required reports for direct quotations.
- Keep `semantic_support="not_assessed"` until a separate contextual review supplies a sourced interpretation. Never relabel a lexical similarity as doctrinal faithfulness.
- Use alignment/fuzzy candidates only to locate possible parallels. Preserve differences in negation, modality, punctuation, translation, and omission.
- Treat stylometry as a secondary tool for author/editor/translator/genre effects, **not** as a measure of theological compatibility. A style change may reflect a translator or genre; a similar style can express contradictory propositions.
- Use graph utilities, where suitable, for declared citation/revision relationships. Do not infer direct historical influence or independent corroboration from graph centrality or shared wording.
- Original-language historical texts require separately validated tokenization/features. Do not apply an English agent-style feature set indiscriminately to Latin or Greek.
- A semantic extraction/review layer, a historical claim graph, and a validated doctrinal-development benchmark remain new work. This planning session does not claim they exist.

Read-only inspection confirmed these boundaries in the current source: [quotation core, lines 113–235](../../src/models/quotation_verifier.py), [request binding and strict schema, lines 57–138](../../src/pipeline/quotation_review.py), and [English-oriented stylometry and uncalibrated distances, lines 24–91](../../src/models/swarm_delta.py). The existing guide's historical test counts are not fresh execution results from this session. No tests, databases, services, models, or live swarm analyses were started for this plan.

**Keep annotations separate:** put historical relations, authority assessments, context judgments, and Newman profiles in a separately versioned annotation layer that references the existing quotation receipts. Do not relax or repurpose the strict quotation manifest schema to accommodate theological verdicts.

### Mandatory legacy-data gate

The current [legacy ingestion script](../../src/data_loader/unpack_and_ingest.py) invokes synthetic corpus generation on archive failure (lines 16–31), contains explicit mock triggers (lines 33–112), clears an existing `words` table before replacement (lines 114–133), and engineers selected grammatical distributions (lines 237–265). These are inspected source-code facts, not results of a database-content audit.

- Do not run that ingestor for this study or treat existing database/report labels as proof of real historical witnesses.
- Stage a new provenance-controlled corpus separately; do not delete or overwrite existing datasets.
- Admit an old dataset only after tracing its actual bytes/records to an identified witness and excluding synthetic fallback or mixed provenance.
- Keep generated fixtures explicitly synthetic and outside the historical evidence set.
- Existing database contents were not opened in this planning audit; their authenticity remains undetermined.

## 8. Bias controls and evaluation

- Freeze the question, sampling rules, editions, interpretation rubric, and proposed failure criteria before assigning labels.
- Select ordinary/repeated teachings as well as controversy-driven cases; a challenge set cannot estimate the prevalence of rupture across a whole council.
- Distinguish faithful reconstruction of Newman's position from an independent evaluation of it.
- Seek independent human review from researchers able to defend competing interpretations. Several LLMs are not substitutes for independent historical expertise.
- Where feasible, mask document identity/order during initial proposition coding, then restore historical context for adjudication. Report when recognizable wording defeats masking.
- Keep quotations, translations, paraphrases, and derivative copies in the same data split. Hold out document/argument families, not random sentences from the same passage.
- Include unmistakable synthetic negation, quantifier, exception, scope, and attribution changes to test the software. Mark them synthetic; they are not historical evidence of doctrinal change.
- Measure quote/span accuracy, retrieval coverage, missed qualifications, unsupported entailment claims, false contradiction flags, false reassurance, abstention, and reviewer agreement separately.
- Fit any similarity thresholds only on a declared development/calibration set. Do not describe an uncalibrated distance as a probability.
- Keep negative results, failed reconciliations, and unresolved cases. A false appearance of certainty is itself a failure.

**Falsifiability:** report when a proposed continuity account requires an unsupported distinction, when a proposed rupture reading ignores an express qualification, when the seven-note coding is not reproducible, or when style adds no useful evidence. If the initial cases cannot be coded reliably, stop scaling and revise the method.

## 9. Agent-to-agent translation: evidence-bearing messages

The research transfer question is:

> Can an agent change, compress, or extend another agent's claim while making the preserved commitments, new assumptions, and revisions inspectable?

A proposed message record carries: claim identifier; quoted source spans and digests; parent claim identifiers; transformation type; explicit premises and assumptions; scope; uncertainty; dissent/counterevidence; review status; and separately established permissions. This is a design proposal, not an implemented schema.

- Keep direct quotation, paraphrase, inference, and revision visibly distinct.
- Preserve a revision history; allow correction and retraction rather than forcing consistency with a known error.
- Parent references are assertions until validated. Check existence, chronology, cycles, and whether apparently independent claims share the same upstream source.
- Source/claim digests identify bytes. Authentication, authorization, consent, truth, and actual execution are separate checks.
- Do not import ecclesial authority into the software permission model. An agent cannot promote a peer's claim into a controlling instruction merely because it is repeatedly cited.
- Use only owned or explicitly authorized traces for experiments; public historical text is not authorization to inspect third-party private agent logs.
- All transferred text remains data. No quoted command, attached doctrine, or graph centrality changes another agent's rules.

### Proposed comparison experiment

After the historical pilot, compare free-form relaying, citation-only relaying, and explicit claim-lineage relaying on the same authorized tasks. Hold the evidence budget and task conditions comparable; record model/version, prompts, seeds where applicable, and costs. Include paraphrase, compression, new counterevidence, warranted correction, and conflicting-source tasks.

Evaluate preservation of scoped propositions, source recoverability, unsupported additions, missed retractions, error propagation, justified revision, cost, and task usefulness. Success requires more than preserving the original wording or reaching consensus. Do not claim transfer until the experiment is actually run.

## 10. Milestones and gates

| Milestone | Deliverable | Completion gate |
|---|---|---|
| 0. Freeze the study | Source/edition manifest, questions, rubric, sampling rules, and permission/rights inventory | Versions and source kinds are explicit; unresolved acquisition gaps visible |
| 1. Reconstruct Newman | Small set of argument dossiers spanning the method and a worked example | Every quotation resolves; each premise/inference/conclusion is distinguishable; reconstruction reviewed before extension |
| 2. Run the bounded historical pilot | Eucharistic and religious-freedom dossiers with opposing interpretations | Both readings receive the same evidentiary burden; human disagreement and abstention retained |
| 3. Validate the computational layer | Frozen human-reviewed benchmark plus deterministic quote/metadata tests | No semantic or historical claim is certified by a text-match receipt; held-out evaluation is separate from development fixtures |
| 4. Expand the continuity assessment | Topic/document coverage map, decisive cases, sensitivity analysis | No council-wide conclusion from a convenient subset; later revisions/reception remain separate |
| 5. Test agent communication | Reproducible, authorized relay comparison and failure analysis | Measurable results against baselines, with no autonomous trust/permission promotion |

### Next bounded work package

Prepare a **twelve-dossier starter set**: four Newman argument reconstructions, four Eucharistic comparisons, and four religious-freedom comparisons. This is a proposed workload, not a report that cases have been collected or decided.

Start with original-source acquisition and manual coding; do not train a classifier first. Each dossier must contain a traceable quotation, version/locator, context, propositions, opposing readings, and an explicit unresolved/insufficient option. Acquire the relevant authoritative Latin witnesses before accepting a translation-sensitive conclusion. If a source or counterpart cannot be obtained, keep the gap rather than filling the slot with an invented comparison.

**Stop gate:** review that starter set for source quality, feasibility, and inter-reader disagreement before any corpus-wide inference, expensive model run, or automatic label generation.

## 11. Planning evidence and remaining limits

Public-source planning snapshots and their byte/extraction metadata are retained at:

`C:/Users/Vivian/AppData/Local/hermes/research/newman-synoptics-planning/`

`live-source-manifest.json` records direct retrievals and explicitly marks them as not corpus-certified. The source ledger is retained with this plan when finalized. Short evidence excerpts support the citations; a source's theological self-description is attributed, not adopted as a proven conclusion.

Still needed: authenticated edition selection for the working corpus; first-edition Newman acquisition; decisive Latin/scan checks; preconciliar bridge texts; full CCC version comparison; a reviewed argument codebook; independent historical/theological reviewers; and actual historical/agent experiments. No conclusion about Vatican II's continuity follows from completing this planning document.

## Sources

[6] https://press.vatican.va/roman_curia/congregations/cfaith/ccc_documents/rc_con_cfaith_doc_19920625_informative-ccc_en.html — Informative Dossier
[8] https://www.vatican.va/archive/hist%5Fcouncils/ii%5Fvatican%5Fcouncil/documents/vat-ii_const_19651118_dei-verbum_en.html — Dei verbum
[9] https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_decl_19651207_dignitatis-humanae_en.html — Dignitatis humanae
[10] https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_con_cfaith_doc_20180801_lettera-vescovi-penadimorte_en.html — Letter to the Bishops regarding the new revision of number 2267 of the Catechism of the Catholic Church on the death penalty, from the Congregation for the Doctrine of the Faith (1 August 2018)
[11] https://newmanreader.org/works/development/chapter5.html — Newman Reader - Development of Christian Doctrine - Chapter 5
[12] https://newmanreader.org/works/development — Newman Reader - Development of Christian Doctrine
[30] https://sourcebooks.fordham.edu/mod/romancat.asp — Internet History Sourcebooks: Modern History
[31] https://www.vatican.va/content/john-paul-ii/en/apost_letters/1997/documents/hf_jp-ii_apl_15081997_laetamur.html — Laetamur magnopere (August 15, 1997)
