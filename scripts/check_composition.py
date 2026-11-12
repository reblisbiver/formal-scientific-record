#!/usr/bin/env python3
"""FSR checkpoint 2: verify the scientific relation-to-expression map.

Mechanical validation of traceable relationships and deletion counterfactuals.
A PASS does not prove semantic equivalence to source material.
"""
import argparse
import json
import re
from pathlib import Path

ROLES = {"definition", "constraint", "contrast", "model", "objective",
         "measurement", "observation", "verification", "scope"}
SCHEMA = "relation-map-v1"

def check(record, audit):
    errors = []
    if audit.get("composition_schema") != SCHEMA:
        return ["Missing composition_schema=relation-map-v1; old prose-justification audits are not accepted"]
    questions = {q.get("id") for q in record.get("questions", [])}
    main_blocks = [b for b in record.get("blocks", [])
                   if b.get("tier", "main") == "main"]
    main_elements = {}
    element_questions = {}
    element_positions = {}
    position_counter = 0
    for b in main_blocks:
        for n, e in enumerate(b.get("elements", []), 1):
            eid = f"{b['id']}.{n}"
            main_elements[eid] = e
            element_positions[eid] = position_counter
            position_counter += 1
            element_questions[eid] = set(b.get("question_ids", []))
    if not questions or not main_elements:
        errors.append("Record must have source-recorded questions and main scientific expressions")

    relations = audit.get("relations")
    if not isinstance(relations, list) or not relations:
        return errors + ["Missing nonempty relations mapping"]
    by_id = {}
    statement_keys = {}
    linked = {e: set() for e in main_elements}
    question_links = {q: set() for q in questions}
    for index, relation in enumerate(relations):
        rid = relation.get("id")
        qid = relation.get("question_id")
        role = relation.get("role")
        statement = str(relation.get("statement", "")).strip()
        exprs = relation.get("expression_ids", [])
        if not isinstance(rid, str) or not re.fullmatch(r"R[1-9][0-9]*", rid) or rid in by_id:
            errors.append(f"Invalid or duplicate relation ID: {rid}")
            continue
        by_id[rid] = (index, relation)
        semantic_key = (qid, " ".join(statement.casefold().split()))
        if semantic_key in statement_keys:
            errors.append(f"Identical scientific relation statement duplicated: {rid} and {statement_keys[semantic_key]}")
        statement_keys[semantic_key] = rid
        if qid not in questions:
            errors.append(f"Relation {rid} refers to unknown source question {qid}")
        else:
            question_links[qid].add(rid)
        if role not in ROLES:
            errors.append(f"Relation {rid} has invalid scientific role: {role}")
        if len(statement) < 14 or any(token in statement.lower() for token in
                                      ["required component of", "this report summarizes",
                                       "important information", "not applicable by default"]):
            errors.append(f"Relation {rid} lacks a concrete, source-grounded scientific statement")
        if not isinstance(exprs, list) or not exprs or len(set(exprs)) != len(exprs):
            errors.append(f"Relation {rid} has empty or duplicate expression_ids")
            continue
        evidence = relation.get("evidence", [])
        if not isinstance(evidence, list) or not evidence or not all(
                isinstance(item, dict) and item.get("path") and item.get("locator")
                for item in evidence):
            errors.append(f"Relation {rid} lacks path + locator scientific evidence")
        ev_pairs = {(z.get("path"), z.get("locator")) for z in evidence
                    if isinstance(z, dict)}
        for eid in exprs:
            element = main_elements.get(eid)
            if element is None:
                errors.append(f"Relation {rid} points to nonexistent main expression {eid}")
                continue
            linked[eid].add(rid)
            if qid not in element_questions[eid]:
                errors.append(f"Relation {rid} question {qid} not linked to expression {eid}")
            if not ev_pairs.intersection(
                    (z.get("path"), z.get("locator")) for z in element.get("evidence", [])
                    if isinstance(z, dict)):
                errors.append(f"Relation {rid} evidence cannot be matched to mapped expression source {eid}")
    for rid, (position, rel) in by_id.items():
        deps = rel.get("depends_on", [])
        if not isinstance(deps, list) or len(set(deps)) != len(deps):
            errors.append(f"Relation {rid} invalid dependency list")
            continue
        for dep in deps:
            if dep not in by_id:
                errors.append(f"Relation {rid} missing prerequisite {dep}")
            elif by_id[dep][0] >= position:
                errors.append(f"Relation {rid} prerequisite {dep} does not precede it")
            else:
                earlier = [element_positions[e] for e in by_id[dep][1].get("expression_ids", [])
                           if e in element_positions]
                later = [element_positions[e] for e in rel.get("expression_ids", [])
                         if e in element_positions]
                if earlier and later and min(earlier) >= min(later):
                    errors.append(f"Relation {rid} appears before prerequisite {dep} in human reading order")
    for q, refs in question_links.items():
        if not refs:
            errors.append(f"Source question {q} has no scientific relation")
    for eid, refs in linked.items():
        if not refs:
            errors.append(f"Main expression {eid} is not necessary to any source-question relation")
        elif not any(len(by_id[r][1].get("expression_ids", [])) == 1 for r in refs if r in by_id):
            errors.append(f"Deletion test: {eid} has no independently lost scientific relation")
    for block in main_blocks:
        prefix = block["id"] + "."
        refs = [e for e in linked if e.startswith(prefix)]
        if not refs:
            errors.append(f"Main scientific block {block['id']} has no expression")
    if not isinstance(audit.get("removed_redundancies"), list):
        errors.append("removed_redundancies must be a list (may be empty)")
    if not audit.get("reviewed_by"):
        errors.append("Audit must identify its AI reviewer status")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record")
    parser.add_argument("audit")
    opts = parser.parse_args()
    rec = json.loads(Path(opts.record).read_text())
    audit = json.loads(Path(opts.audit).read_text())
    errors = check(rec, audit)
    print(json.dumps({"status": "PASS" if not errors else "FAIL",
                      "type": "SOURCE-RELATION-EXPRESSION STRUCTURE ONLY",
                      "errors": errors}, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
