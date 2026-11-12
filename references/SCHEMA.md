# Typed record.json contract — v0.6 (scientific elements unchanged)

One record per folder. All human-facing text must be English. The separate `composition_audit.json` must follow the `relation-map-v1` relationship schema in `references/COMPOSITION_PROTOCOL.md` rather than the retired paragraph-justification checklist. This schema is a **fact and relation representation**, not authored prose. `evidence` locations are private metadata and are rendered only in the final Appendix.

```json
{
 "title": "Literal source-grounded research title",
 "record_type": "theory | comparison | analysis | model | mixed",
 "subtitle": "optional, maximum 95 characters",
 "questions": [{"id":"Q1", "text":"Source-recorded research question", "evidence":[{"path":"PROTOCOL.md","locator":"section: aim"}]}],
 "preregistration": {"status":"not_recorded | evidenced", "evidence":[]},
 "blocks": [
  {"id":"B1", "kind":"definition | assumption | objective | method | comparison | observation | verification | scope",
   "title":"Short semantic title", "question_ids":["Q1"], "provides":["concept-id"], "requires":[], "tier":"main | appendix",
   "elements":[
    {"type":"text", "role":"definition | condition | procedure | observation | missing", "text":"Plain concise sourced statement", "evidence":[{"path":"PROTOCOL.md","locator":"section: procedure"}]},
    {"type":"equation", "latex":"y_t = f(x_t)", "symbols":[{"symbol":"x_t","meaning":"Input at trial t"}], "evidence":[{"path":"PROTOCOL.md","locator":"eqn: model"}]},
    {"type":"table", "headers":["Metric","Baseline","Treatment","Delta"], "rows":[["Accuracy","0.77","0.78","+0.01"]], "evidence":[{"path":"metrics.json","locator":"accuracy"}]},
    {"type":"chart", "chart":{"kind":"line | scatter | bar | histogram | paired_delta", "csv":"per_fold.csv", "x":"fold", "y":["accuracy_b","accuracy_t"], "xlabel":"Fold", "ylabel":"Accuracy", "title":"Matched-fold accuracy", "legend":["Baseline","Treatment"]},"caption":"Observed accuracy per fold", "evidence":[{"path":"per_fold.csv","locator":"columns fold,accuracy_b,accuracy_t"}]}
   ]}
 ],
 "audit_notes": ["Source-specific audit limitations, not model interpretations"]
}
```

- Each main block must link to at least one source-recorded question; all questions must have a substantive linked main block.
- Each element needs `evidence` (except missing placeholders with source pointers still preferred). Paths MUST resolve under SOURCE_DIR. `path` is relative, NOT absolute; `locator` denotes a section, JSON pointer, or CSV columns and row selection.
- `provides` and `requires` identify semantic dependencies among blocks; those IDs are hidden from main text. A missing dependency is a validation error.
- `verification` blocks require explicit `preregistration.status=evidenced` and evidence of source rule, or must only state `NOT EVALUATED` as a missing status.
- Charts read raw numeric columns directly from cited CSV, calculate paired deltas only when matching row IDs, and label axes/units. Never enter manually invented chart data.
- For comparison statistics tables, rows should be derived from verifiable source values. Manual aggregate values are allowed only with audit checks and precise evidence paths; do not claim reproduced if not recomputed.
- `scope` records only limitations of available input and protocol, not new science.
