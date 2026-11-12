# FSR Final Verification Contract (v0.5)

The immutable frozen Baseline v1.1 and three approved reference PDFs outrank this engineering contract. This contract defines *workflow state*, not a new scientific reporting requirement.

## The four distinct outcomes

1. **FSR report compliance**: source-grounded representation, composition audit, PDF mechanics and final visual reading quality.
2. **Saved-data numeric scope**: `REAGGREGATED` (arithmetic from existing data), `SOURCE_ONLY` (reported values have no computable backing data), `UNAVAILABLE` (raw values absent/cannot be parsed), or `NOT_CHECKED` (must not be accepted). Document exactly what was computed.
3. **Original research acceptance**: e.g. `NOT_ACCEPTED` / `ACCEPTED` / `UNKNOWN` *only when the source establishes it*. This is informational: it never overrides the FSR report verdict. Do not infer acceptance.
4. **Original model / algorithm scientific rerun**: `OUT_OF_SCOPE`. The FSR Skill explicitly prohibits new training, scientific simulations and algorithm evaluation jobs. Not rerunning them is NOT a failed step.

There is **no additional mandatory human-approval phase**. An interactive reviewer may later audit results, but do not create an undefined `PENDING HUMAN REVIEW` gate. The agent must independently inspect the final rendered PDF and truthfully report whether it checked all pages. Automated mechanical checks cannot substitute.

## Bounded saved-data verification

- Prefer deterministic arithmetic on existing saved CSV/JSON/predictions, never run a source model or algorithm. For simple grouped sums/means use `scripts/reaggregate_csv.py --source-dir SOURCE_DIR --csv RELATIVE_CSV --value NUMERIC_COLUMN --group-by GROUP_COLUMN --output OUTPUT_DIR/reaggregated.csv.json`, then compare the computed values to the displayed report values and record exact checks. This helper is bounded and does not determine scientific interpretation.
- Use local stdlib or installed Python tools, read-only source access, cap processing to 50 MB per input and approximately 60 seconds per audit script. If inputs exceed this, stream rows or scope an explicit reproducible sample rather than scanning unboundedly.
- Save a reproducible, project-specific calculation script or exact command and a `numeric_audit.json`:
```json
{
  "status": "REAGGREGATED",
  "record_sha256": "current record.json SHA-256",
  "sources": ["results.csv"],
  "checks_passed": 3,
  "checks_failed": 0,
  "checked_quantities": ["mean NLL", "per-fold denominators", "delta"],
  "method": "Exact CSV reaggregation; no model execution",
  "original_science_status": "UNKNOWN"
}
```
- For missing data, choose `SOURCE_ONLY` or `UNAVAILABLE`, include `reason` and `sources` (if any) and keep the PDF's main scientific status accurate. Do not create artificial extra metrics or prerequisites.
- All numeric audit files must bind to the current `record.json` SHA-256; do not reuse stale audit results after changing the scientific record.
- If a desired comparison cannot be calculated from saved files, disclose **that specific limitation** only. Do not list irrelevant unperformed model training or algorithm experiments as failures of this Skill.

## Deterministic final visual review

1. Generate PDF from `record.json` using `render.py`. NEVER manually patch the generated `report.tex` and then keep the validator from a prior version. If formatting fails, fix the reusable renderer/style and run it again.
2. Run `verify.py`. Its page rasterization uses a fallback ladder: PyMuPDF, then pdftoppm, then mutool. It checks overflow, evidence leakage, minimum body glyph size and basic content extent. It does **not** claim visual review automatically. If an agent cannot *view* the first PNG through its remote image reader, retry the saved PNG with another available image-read route, render a PDF page directly, or use the alternate rasterizer and reopen the new image. Do not steal foreground application focus; do not block on a single screenshot method or falsely claim inspection. Record attempted routes if all fail, then choose `NOT_VERIFIED`.
3. Open ALL resulting final PDF page images; inspect content hierarchy, cuts, chart axis units and tick readability, table/plot correspondence, whitespace imbalance and source appendix. Fix errors, then rebuild, rerender, reinspect all pages.
4. Save `visual_qa.json` with the **current final PDF hash**:
```json
{
  "status": "PASS",
  "pdf_sha256": "actual final report.pdf SHA-256",
  "pages_inspected": [1, 2, 3],
  "method": "Read every page_renders/page-XX.png at legible scale",
  "issues": [],
  "notes": ["Scientific content legible; table/graph axes inspected."]
}
```
If pages could not actually be read, set `NOT_VERIFIED`; never claim `PASS`. If `validation.json.layout_warnings` contains a seriously underfilled body page, change the semantic grouping/layout and rerender. An exception is allowed only for a scientifically necessary break, documented as `"layout_resolution":{"decision":"JUSTIFIED","reason":"...at least 50 characters explaining the source-specific necessity..."}`. Boilerplate excuses are not a valid review.
5. Run `finalize.py OUTPUT_DIR` **last**. It writes the single authoritative `final_status.json` with FSR report verdict, numeric scope, original-study status as informational metadata and the PDF hash. The final PDF hash must match the compile validation and final visual review. Any later PDF edit invalidates this status and requires a full recheck. If `finalize.py` returns nonzero, report a candidate, not an accepted artifact.

The frozen report output is always **English**, collaborative discussion may be **Chinese**.

## Metric registry for new FSR runs (legacy outputs remain compatible)

The installed-compatible finalizer reads `OUTPUT_DIR/metric_registry.json` when present. New full Skill runs that display scientific metrics must author it; legacy report artifacts without it remain backward compatible.
This is an optional provenance gate, not a new scientific-report requirement;
without the file, the existing finalizer contract and output shape remain in
force. The supported registry is the verified Track-D v1 shape only. Its
`record_projection.metric_ids`, `declared_metric_ids`, and `metrics[].id` must
be exact sets with no duplicates, and the canonical projection hash,
mechanical attestation, and every declared source hash must match current
bytes. Any mismatch makes the report `CANDIDATE` and propagates the affected
metric as `UNVERIFIED`.

Keep two definitions separate. A source-code definition establishes the
construction, unit, denominator, class coding, or other semantics that the
source actually states; it is represented by `definition_status: DEFINED` and
does not by itself establish a saved-trial numeric recomputation. A saved-trial
numeric status is `REAGGREGATED` only when bounded arithmetic on existing saved
rows has a passing reported-versus-recomputed check. `SOURCE_ONLY` means the
source or historical audit reports a value without a current trial-level
reconstruction; `UNAVAILABLE` means the named quantity or raw backing values
are absent and must not be converted to zero; `NOT_CHECKED` remains an explicit
limitation. Valid `SOURCE_ONLY` and `UNAVAILABLE` markers do not block a
faithful report, while stale hashes, missing required limitations, or a
reaggregated metric without a source-grounded definition do.

Information selection is accepted only when every metric displayed in a
result table, figure, caption, or appendix summary has a stable registry ID,
source locator/hash, definition status, numeric status, scope/limitation, and
an emitted final marker. The readable report may select the minimum sourced
question, design, metric/denominator, observation, and validity boundary;
moving redundant detail to the appendix is allowed, but it may not remove the
status or scope needed to prevent a source-only or unavailable value from
being read as a fresh trial result. Registry support remains developer-copy
only until the real record schema, renderer, Stage-4 visual review, and live
installed Skill are separately approved and verified.
