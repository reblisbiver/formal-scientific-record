# Formal Scientific Record (FSR)

A source-first, minimal-complete scientific reporting Skill. It reads a local research project folder, retains evidence-backed definitions, hypotheses (when present), computational mechanisms, procedures, measurements, results, verification boundaries and limitations, then compiles a sourced English LaTeX report as a PDF.

## Install

Copy the contents of this repository into your Codex Skill directory, for example:

```bash
mkdir -p ~/.codex/skills/formal-scientific-record
cp -R SKILL.md assets references scripts tests ~/.codex/skills/formal-scientific-record/
```

Install a working LaTeX/XeTeX or Tectonic environment and Python dependencies including PyMuPDF. The renderer's command-line interfaces are available via `python3 scripts/render.py --help`, `python3 scripts/verify.py --help`, and `python3 scripts/finalize.py --help`.

## Use

Ask Codex to execute the complete workflow in `SKILL.md` with an explicit `SOURCE_DIR`. The default output folder is `SOURCE_DIR/fsr_record`.

The Skill is designed to **read the source without changing the research**, and it must not rerun scientific experiments, manufacture hypotheses, add unsupported scientific interpretations or claim that a source experiment was independently validated.

- Keep each original scientific claim linked to its source evidence.
- Give defining algorithms, state transitions and measured features the mathematical prominence they need.
- When the original project states hypotheses, preserve a hypothesis-to-observation-to-bounded-status chain in the main text.
- Distinguish recomputed numerical checks from source-only or unavailable results.
- Verify the rendered PDF visually; `final_status.json = PASS` is mechanical report integrity, not proof of the underlying scientific findings.

## Contents

- `SKILL.md` — execution contract and workflow.
- `references/` — locked scientific baseline, composition protocol, quality gates and three typesetting exemplars.
- `scripts/` — generation, rendering, numeric and integrity validation.
- `assets/fsr.sty` — LaTeX presentation style.
- `tests/` — bundled regression tests.

## Tests

```bash
python3 -m unittest discover -s tests -p 'test*.py' -q
```

The frozen references are scientific-format examples, not actual research findings. Any scientific report created with this Skill should be independently reviewed before publication.
