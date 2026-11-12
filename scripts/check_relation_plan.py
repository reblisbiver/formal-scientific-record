#!/usr/bin/env python3
"""Stage-2-only source-relation plan checker. Diagnostics are not semantic proof."""
import argparse,json,re
from pathlib import Path

ROLES={"definition","constraint","contrast","model","objective","measurement","observation","verification","scope"}
def check(plan,root):
    root=Path(root).resolve()
    errors=[];warnings=[]
    questions=plan.get("questions",[])
    if not isinstance(questions,list) or not questions:
        errors.append("No source-recorded research question")
        questions=[]
    qids={q.get("id") for q in questions if isinstance(q,dict) and isinstance(q.get("id"),str) and q["id"]}
    if len(qids)!=len(questions):
        errors.append("Invalid or duplicate source question IDs")
    relations=plan.get("relations",[])
    if not isinstance(relations,list):
        return errors+["relations must be a list"],warnings
    question_main={qid:set() for qid in qids}
    ids={}
    for idx,r in enumerate(relations):
        rid=r.get("id")
        if not isinstance(rid,str) or not re.fullmatch(r"R[1-9]\d*",rid) or rid in ids:
            errors.append("invalid/duplicate relation ID "+str(rid));continue
        ids[rid]=idx
        qid=r.get("question_id")
        if qid is None and len(qids)==1:
            qid=next(iter(qids))
        if qid not in qids:
            errors.append(rid+" invalid question_id")
        if r.get("role") not in ROLES:errors.append(rid+" invalid role")
        tier=r.get("tier")
        if tier not in ("main","appendix"):errors.append(rid+" explicit main/appendix tier required")
        if tier=="main" and qid in question_main:
            question_main[qid].add(rid)
        text_value=r.get("statement")
        txt=text_value.strip() if isinstance(text_value,str) else ""
        if not isinstance(text_value,str):errors.append(rid+" statement must be a string")
        if len(txt)<16:errors.append(rid+" lacks a scientific statement")
        if len(txt)>470 or txt.count(";")>=4:
            warnings.append(rid+" possibly combines multiple independent scientific functions: inspect atomicity")
        ev=r.get("evidence",[])
        if not ev:errors.append(rid+" missing source evidence")
        for item in ev:
            path=item.get("path",""); loc=item.get("locator","")
            target=(root/path).resolve()
            if not path or not loc or root not in target.parents or not target.is_file():
                errors.append(rid+" invalid source file/locator: "+str(path))
    edge_count=0
    for r in relations:
        rid=r.get("id");deps=r.get("depends_on",[])
        if not isinstance(deps,list):errors.append(str(rid)+" dependencies not list");continue
        if len(deps)!=len(set(deps)):errors.append(str(rid)+" duplicate dependencies")
        for dep in deps:
            edge_count+=1
            if dep not in ids:errors.append(str(rid)+" missing dependency "+str(dep))
            elif rid in ids and ids[dep]>=ids[rid]:errors.append(str(rid)+" dependency not earlier: "+dep)
            elif dep in ids and r.get("tier")=="main" and relations[ids[dep]].get("tier")=="appendix":
                errors.append(str(rid)+" main relation requires appendix-only prerequisite "+dep)
    if len(relations)>=6 and edge_count>=len(relations)-1:
        warnings.append("Dependency graph unusually dense for a question: verify each edge is a true scientific prerequisite, not paragraph order")
    if not relations:errors.append("No relations")
    for q,covered in question_main.items():
        if not covered:
            errors.append("Research question "+q+" has no main scientific relation")
    return errors,warnings

def main():
    p=argparse.ArgumentParser();p.add_argument("plan");p.add_argument("--source-dir",required=True);a=p.parse_args()
    root=Path(a.source_dir).resolve()
    obj=json.loads(Path(a.plan).read_text())
    errors,warnings=check(obj,root)
    print(json.dumps({"status":"FAIL" if errors else "STRUCTURE_PASS_NOT_SEMANTIC_ACCEPTANCE","relation_count":len(obj.get("relations",[])),"errors":errors,"warnings":warnings},indent=2))
    if errors:raise SystemExit(1)
if __name__=="__main__":main()
