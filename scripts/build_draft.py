#!/usr/bin/env python3
"""Deterministic pre-LaTeX preview of source-grounded FSR record objects.

Not a scientific author. Shows the selected scientific objects/relationships and
their exact current wording to permit a content-only review before typography.
"""
import argparse
import json
from pathlib import Path

def preview(record, audit=None):
    lines = ["# " + record["title"], "", "**Recorded question(s):**"]
    for question in record["questions"]:
        lines.append("- " + question["text"])
    if audit is not None:
        lines.extend(["", "## Scientific relation plan (checkpoint 2)"])
        for r in audit.get("relations", []):
            deps=", ".join(r.get("depends_on", [])) or "none"
            refs=", ".join(r.get("expression_ids", []))
            lines.append(f"- {r['id']} / {r['question_id']} / {r['role']}: "
                         f"{r['statement']}  → {refs}; prerequisites: {deps}")
    lines.extend(["", "## Main scientific composition"])
    for block in record["blocks"]:
        if block.get("tier", "main") != "main":
            continue
        lines.extend(["", "### " + block["title"] + " — " + block["kind"]])
        for index, element in enumerate(block.get("elements", []), 1):
            eid = f"{block['id']}.{index}"
            typ = element["type"]
            if typ == "text":
                lines.append(f"**{eid} / {element.get('role','undefined')}**  {element['text']}")
            elif typ == "equation":
                lines.extend([f"**{eid} / equation**", "$$", element["latex"], "$$"])
                for symbol in element.get("symbols", []):
                    lines.append(f"- \\({symbol['symbol']}\\): {symbol['meaning']}")
            elif typ == "table":
                head = element["headers"]
                lines.append(f"**{eid} / comparison table**")
                lines.append("| " + " | ".join(map(str, head)) + " |")
                lines.append("| " + " | ".join(["---"] * len(head)) + " |")
                for row in element["rows"]:
                    lines.append("| " + " | ".join(map(str, row)) + " |")
            elif typ == "chart":
                ch = element["chart"]
                lines.append(f"**{eid} / measured chart**: {ch.get('kind')}; "
                             f"x={ch.get('xlabel')}; y={ch.get('ylabel')}; "
                             f"source columns={ch.get('y')}. {element.get('caption','')}")
            else:
                raise ValueError("Unrecognized expression type: " + str(typ))
    lines += ["", "## Content review (not PDF layout)",
              "This preview intentionally excludes source paths, record IDs beyond local audit references, and typesetting decisions.",
              "Review controlled variables, all symbols, denominators, formula equivalence, observation correspondence, and redundancy before rendering."]
    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record")
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit", help="Optional scientific relation plan JSON")
    args = parser.parse_args()
    record = json.loads(Path(args.record).read_text())
    audit = json.loads(Path(args.audit).read_text()) if args.audit else None
    Path(args.output).write_text(preview(record, audit), encoding="utf-8")
    print(args.output)

if __name__ == "__main__":
    main()
