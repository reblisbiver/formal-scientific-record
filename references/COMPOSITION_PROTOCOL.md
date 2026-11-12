# FSR v0.6.2 candidate — Four-stage scientific compilation protocol

**Implementation protocol, not a frozen-rule amendment.** The locked Baseline v1.1 and three approved English PDF exemplars remain authoritative and immutable. Do not change them. Reports are written in English; conversation stays in Chinese.

## Stage 1 — Scientific Extraction

**Input:** the selected SOURCE_DIR, excluding any prior fsr_record output.

**Goal:** extract only source-recorded questions, objects, conditions, model/method definitions, measurement units and denominators, observed values, and evidence. Identify which values are available and which are missing. Do not make up scientific hypotheses, interpretations, or unperformed experiments.

**Checkpoint 1 (source fidelity):** each claimed scientific fact must have a source file and locator. Distinguish directly recorded facts, deterministic arithmetic, and absent/unknown values. Source research acceptance is a source fact, not a judgment by FSR.

**Deliverable:** question and fact inventory that will become the question list and evidence-linked elements of record.json. Do not write narrative report prose yet.

## Stage 2 — Scientific Composition (the critical checkpoint)

First establish a **scientific relation plan**; only then choose the exact mathematical/textual expression for each relation.

- Identify the necessary relations answering each source-recorded research question: definition, constraint, contrast, model, objective, measurement, observation, verification, scope.
- Every relation must specify its scientific statement, exact source evidence, and prerequisites (if any). A relation must not become an invented causal claim or new hypothesis.
- Choose a representation: equation for a source-supported precise relationship, compact comparison for aligned conditions and values, chart for a distinct empirical pattern, brief prose for non-equational conditions or exceptions.
- Define quantities and denominators once. Put only conditions necessary to understand comparisons in the readable body. Move engineering/reproducibility detail to the source appendix or machine record.
- A table and a chart may both be retained if they convey distinct necessary scientific relations (e.g., exact values vs paired spread). Do not delete the chart just to save space.
- Do not invent mathematics to replace irreducible procedural conditions. Use concise source-grounded natural language instead.
- A scoring convention is not evidence for class membership or class-event meaning; require source-defined labels, feature construction and objective when necessary to understand the research, or state the source-bounded absence once. Do not promote source-audit mechanics or the internal fact pack name into the human-readable main body.

**Checkpoint 2 (coverage and deletion):** in composition_audit.json record an explicit mapping
`research question → sourced scientific relation → exact main-body element`.
The checker rejects orphan expressions, incorrect source/question mapping, missing prerequisites, and elements that could be removed without losing any uniquely mapped relation. This is a structural check; a separate content-only reading of body_draft.md is still required to catch semantic errors, invented claims and awkward organization.

Do **not** produce a prose-justification essay for every paragraph. A mapped scientific relation is the unit of validation, not an author's self-attested reason to keep a sentence.

**Required composition_audit.json shape** (small schematic, replace example facts with source evidence):

```json
{
  "composition_schema": "relation-map-v1",
  "relations": [
    {
      "id": "R1",
      "question_id": "Q1",
      "role": "definition",
      "statement": "RAW3 is the recorded input feature subset of FULL7.",
      "evidence": [{"path":"protocol.md","locator":"input feature section"}],
      "expression_ids": ["B1.1"],
      "depends_on": []
    },
    {
      "id": "R2",
      "question_id": "Q1",
      "role": "observation",
      "statement": "Paired held-out NLL per recorded fold.",
      "evidence": [{"path":"results.csv","locator":"fold,NLL columns"}],
      "expression_ids": ["B2.1"],
      "depends_on": ["R1"]
    }
  ],
  "removed_redundancies": [],
  "reviewed_by": "AI execution; no independent human science approval claimed"
}
```

Relation IDs are machine-only, never displayed in the PDF body. Every main element Bn.m needs at least one uniquely represented relation; when a table and chart convey different aspects, give them distinct relation statements. A relation's evidence path and locator must match at least one source reference in the mapped element. Dependencies must reference already-defined relations. The one-to-one element/relation check is a **necessary bookkeeping check, not proof** that the relation is scientifically indispensable; the content-only reading must still ask whether the relations themselves duplicate facts.

Build:

```sh
python3 scripts/build_draft.py OUTPUT_DIR/record.json --audit OUTPUT_DIR/composition_audit.json --output OUTPUT_DIR/body_draft.md
python3 scripts/check_composition.py OUTPUT_DIR/record.json OUTPUT_DIR/composition_audit.json
```

If either fails, revise the scientific relation plan or record, not merely formatting. Do not proceed to TeX compilation with an invalid relationship map.

### Stage-2 micro-checkpoint: relation selection before expression

For a targeted trial (without generating a full report), run **only** Stage 1 extraction for the named source-recorded question, then output a source-grounded `relation_plan.json` prior to any prose draft or `record.json`. This is an internal Stage 2 test artifact, not an extra mandatory output for full reports.

- **One scientific function per relation.** A joint design vector, a formula with its defining symbols, or one coherent measurement comparison may remain one relation. Do not combine an emission-model definition, fitting protocol, acceptance thresholds and observed results merely because they appear in one paragraph. Do not split every parameter into its own relation purely to inflate the count.
- **True dependencies only.** Declare `depends_on` only when the downstream statement requires the predecessor for mathematical definition, units/denominator, experimental comparability or protocol applicability. A preceding paragraph, an adjacent table, or another observation of the same experiment is not automatically a scientific prerequisite. Independent recovery results and prediction results may share common definitions without depending on each other.
- **Scientific sufficiency test:** for the selected question, trace object → indispensable model/conditions → metric → observation → source-recorded verdict/scope (when available); no steps need be fabricated.
- **Explicit information promotion for micro-tests:** assign `tier: main` only to relations without which the chosen research question, its observable answer, or a crucial validity limit would be ambiguous. Keep all other accurate context as `tier: appendix` (or omit it from this narrow question's plan if it is not needed). Do **not** turn every recorded stress condition, auxiliary result or project-wide status into a body relation by default. A main relation cannot depend on an appendix-only prerequisite. One conceptual equation may package several symbols, and one condition table may package shared experimental settings; atomicity is about unique *scientific function*, not about the number of nouns or digits.
- **Information minimization test:** inspect the `main` subset on its own and answer the selected question; if the core model/denominator/observed contrast remains interpretable after moving a relation to appendix, prefer appendix. Do not optimize merely for relation count or omit source-defined validity boundaries.
- **Minimization test:** compare the relation list as a set, not a chapter sequence. Merge equivalent statements; delete one relation and check whether a unique source-grounded scientific fact or required link disappears. A simple relabeling of old paragraphs does not pass this semantic check.
- **Faithfulness:** retain the source mathematical notation if exact and available. Do not invent transition equations, estimator formulas, causal interpretations or numeric thresholds absent from records.
- **Bounded iteration:** in targeted Stage 2 tests, read only the explicitly identified source files and target question. Run `python3 scripts/check_relation_plan.py SOURCE_DIR/trial/relation_plan.json --source-dir SOURCE_DIR` and inspect its warnings. Don't need to regenerate PDF, calculate metrics or traverse unrelated subprojects for a relation-plan test.

This small checkpoint is used to improve the **content selector** before spending time on PDF aesthetics. It does not replace the full-process evidence/record validator.

### Stage-2 micro-checkpoint: expression compilation after relation selection

Given a vetted relation plan, compile only its `main` relationships into a compact human-readable scientific composition draft before any TeX. This is a *different* local target from relation selection. Keep appendix-tier relations in a clearly separated auxiliary section, not intermixed with main science.

- **Single information owner:** for each factual relation choose one primary display: equation and symbol key, aligned comparison table, empirical distribution/figure (if source data), or indispensable condition prose. After an equation/table defines or displays the fact, do not repeat the same values or definitions in a paragraph merely to narrate them.
- **Model first, not narration first:** place source-backed model equations directly after the minimal object definition and define symbols exactly once. If the source equation contains ambiguous/underspecified notation, preserve it and state the precise missing definition *once* in a compact scope statement; no invented derivation.
- **Source-grounded unified tables:** when one set of recorded acceptance thresholds is checked against two comparable conditions, show threshold and observed values in the same table. A separate prose list of those same thresholds or a repeated PASS paragraph is redundant; retain a concise source-verdict label when needed.
- **Scientific status granularity:** distinguish synthetic recovery gate PASS from overall project NOT_ACCEPTED, but do not scatter this distinction across model, methods and conclusion prose. Keep the status boundary only where it modifies an otherwise misleading result claim.
- **Minimal scope:** reserve a short clearly scoped note for unknown aggregation/denominators, source-only verification and model-symbol ambiguity. Do not repeat a missing-data notice in each section. Avoid machine-report meta-text such as 'the permitted sources do not specify' except where essential for accurate scientific interpretation.
- **Compression check:** read main composition alone. For each sentence ask which unique *scientific* relation it conveys not already in the adjacent formula, table, caption or compact scope note. Delete redundant prose without deleting a scientific prerequisite, observable, valid condition or source-stated limit. Do not target a fixed word count or require equations for genuinely non-algebraic conditions.

In a narrow expression-only Codex test, use the source allowlist and the given relation plan, output just a `scientific_draft.md` under its trial folder; no PDF, model rerun or secondary metric recomputation. This stage should not regenerate the relation plan unless a concrete inconsistency is found.

### Stage-2 micro-checkpoint: deletion-only independent edit (optional local test)

When a content-only expression draft remains long after source-grounded construction, **do not add more generative writing rules**. Use an isolated, fresh-context review pass, given the existing draft, the same bounded source files, and the relation plan. Its only goal is subtractive scientific editing:
1. Identify complete scientific statements or duplicated symbol definitions that restate an adjacent equation/table or belong exclusively in the appendix; remove or merge them without dropping a unique relation.
2. Preserve every original model equation, essential term/condition, outcome metric/denominator, result and required scope limitation. No new scientific facts, new hypotheses, new formula derivations, or unrecorded acceptance rules.
3. Treat descriptive evidence scope once. Do not place tool/report-generation/process commentary in the human-readable scientific body.
4. Save both the revised human-readable draft and a **short deletion log** referencing original passages. The log is machine-only, not part of the report.
5. Compare the revised draft against the source-backed main relation list. A shorter draft is not automatically better: if any essential source relation disappears, reject the edit.

This is a focused experimentation technique, **not an additional mandatory full-report agent or approval step**.

## Stage 3 — Scientific Verification

Independently reaggregate **already saved** numerical data when available. Verify the reported contrasts/units and the source-backed mathematical relations wherever checking is possible. A non-computable claim must be identified as source-only or unverified; do not infer it.

Preserve v0.5's bounded arithmetic, record hash binding, `numeric_audit.json` and precisely scoped status. Do not rerun training, experimental simulations, search algorithms or scientific experiments. Do not invent an independent Codex/human approval step.

**Checkpoint 3:** saved-data recomputations are reproducible and match stated quantities within stated precision, or limitations are explicitly scoped. The *original study's* scientific acceptance status is separate from the *FSR report's* validation.

## Stage 4 — Scientific Publication

Render only the verified record with existing `render.py` and LaTeX style. Use the approved frozen PDF examples for aesthetic discipline (serif hierarchy, aligned math, concise captions and typography); do not copy a fixed chapter sequence.

Run `verify.py`, view each final PDF page using available background renderers and their fallbacks, examine figures at actual reading size, check table/figure adjacency, font legibility, and unbalanced page breaks. If scientific relations or continuity need editing, return to Stage 2; if numbers need editing, return to Stage 3. Do not manually patch generated TeX.

**Checkpoint 4:** save final-hash-bound visual_qa.json and run `finalize.py` LAST. final_status.json is the only overall artifact verdict. An automated PASS is not proof of formal semantic sufficiency or professor-level scientific writing.

## General exclusions and safeguards

- Never add interpretation, scientific hypotheses or recommendations to the report.
- Never elevate experiment logs or source paths into the human-facing body.
- Do not generate a 'no preregistered hypothesis' paragraph when no source hypothesis is being evaluated.
- Do not add mandatory "human review pending" or "Codex verification required" gates.
- No new roles, agents, extra evaluation jobs or complex scoring rubrics.
- Numerical and rendering checks from v0.5 remain unchanged unless a verified implementation defect requires correction.
- A failure should identify the exact checkpoint and relevant scientific relation; do not label all scientific uncertainty as a workflow failure.

## Algorithmic mechanism formalization priority — exact-source gate

This rule applies when the recorded question compares **procedures producing decisions**, not studies merely comparing static numerical scores.

1. Inspect implementation or authoritative code audit for the operational difference: state, selection/transition, update/backup, stopping rule and where an external model changes computation. Algorithm labels alone are not definitions.
2. Choose the **smallest exact defining relation** and put it before the observation table. Express source-backed recurrences mathematically with minimal symbols. If source behavior is incomplete, give exact known transitions plus a scope note, without inventing standard textbook formulas.
3. Rank equations by irreducible explanatory value. Remove the mechanism while keeping the observation table: if procedures are no longer distinguishable, the mechanism belongs in main. A difference obtained by subtracting already displayed columns does not outrank it.
4. Check denominator and simulation units. In search, distinguish sampled path outcomes, estimated tail count, horizon normalization, action-level return accumulator and visit increment. Do not equate leaf Value output with empirical internal-node Q.
5. Independently compare the defining relation to original code or precise audit; bounded synthetic bookkeeping may verify deterministic equations without rerunning original research. Mismatches prohibit science-fidelity PASS.

**Source-grounded regression:** In an audited Value-MCTS backup, per-visited-node simulated target outcomes plus leaf-tail target count are divided by the remaining horizon, accumulated into normalized return sum and visits. This defining computational relation belongs in main; an observed difference between mean allocated and non-allocated probability is secondary.

## Source hypothesis-to-evidence closure (conditional source-first requirement)

The locked baseline explicitly allows recorded hypotheses and their tests while forbidding the model from inventing scientific interpretations or imposing a fixed Hypotheses-Results-Conclusion chapter sequence.

- **Extract** named or otherwise explicit source hypotheses from original protocol, README, specification and study plan. Preserve the individual falsifiable predicates, including conjunctions of shape, direction, modality and group/condition comparison.
- **Promote** original hypotheses to readable MAIN text when they were part of the research question. An appendix provenance note is not a substitute. No mandatory new section; a compact hypothesis table suffices.
- **Connect** each hypothesis to its observable definition and actual saved result or explicit evidence blocker. The dependency order is necessary definitions -> hypothesis and possible test criterion -> measurement/procedure -> observed evidence -> bounded status. Interleave independent relations when useful; no universal chapter template.
- **Adjudicate conservatively:** use accepted/rejected only when the original decision criterion and matching evidence exist. Without it, report observed directional checks and NOT FORMALLY TESTED for a formal decision, or PARTIALLY OBSERVED if only some components are measured. Missing required data means NOT TESTED, not negative evidence. Descriptive peak location is not proof of unimodality or an inferential test.
- **Deletion test:** remove the source hypothesis and evidence-status link while keeping result tables/figures. If original study purpose and its adjudication cannot be recovered, the report is not source-complete. Record this in composition_audit; a mechanical mapping PASS alone is insufficient.

## Optional visual hierarchy for recorded hypotheses

For a MAIN hypothesis block, opt into the renderer's display-only text
presentation hypothesis. A text element may contain hypothesis_group
(e.g., H1, H2), group_title (e.g., Human distributions), and optional
hypothesis_marker (a, b). The renderer adds a bold group heading and uses
indented italic statements with bold subordinate markers. The source
statement remains the text value, and each independently necessary
subhypothesis remains its own evidence-linked scientific element/relation.

For a matching verification table, optional table presentation
hypothesis_status groups contiguous H1(a), H1(b), H2 rows with subtle
vertical spacing and bolds bounded status terms. These display changes
MUST NOT modify observations, acceptance criteria, scope, or numerical
results, and do not impose a mandatory chapter or concluding section.
Other report elements use the original unstyled typography.
