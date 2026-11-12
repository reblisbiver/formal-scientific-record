#!/usr/bin/env python3
"""Stage-2-only mechanical comparison of scientific expression drafts.

Checks literal display equations and numeric result rows; never asserts semantic
equivalence or a deletion-only character-subsequence property.
"""
import argparse,json,re
from pathlib import Path

def equations(text):
    return [re.sub(r'\s+',' ',x).strip() for x in re.findall(r'\\\[(.*?)\\\]',text,re.S)]
def numbered_table_rows(text):
    rows=[]
    for line in text.splitlines():
        if not (line.startswith('|') and line.endswith('|')):continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)<3:continue
        numbers=re.findall(r'(?<![A-Za-z])(?:\d+\.\d+|\d+)(?![A-Za-z])', '|'.join(cells[1:]))
        if len(numbers)>=2:
            label=cells[0]
            # Permit only this verified redundant definition label to be shortened.
            # Do NOT strip generic parentheticals (units, scopes, strata matter).
            if label.casefold()=="brier (mean squared probability error)":
                label="Brier"
            rows.append((label,numbers))
    return rows

def compare(old,new):
    errors=[]
    if equations(old)!=equations(new):errors.append('Display equations differ')
    left=numbered_table_rows(old);right=numbered_table_rows(new)
    for row in left:
        if row not in right:errors.append('Numeric table row missing or changed: '+row[0])
    return {'status':'PASS_MECHANICAL_ONLY' if not errors else 'FAIL',
            'old_words':len(old.split()),'new_words':len(new.split()),
            'equations':len(equations(old)),'numeric_rows_checked':len(left),
            'errors':errors,
            'limitations':'No test here proves text semantics, source fidelity, or lossless deletion.'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('original');ap.add_argument('revised')
    a=ap.parse_args()
    result=compare(Path(a.original).read_text(),Path(a.revised).read_text())
    print(json.dumps(result,indent=2))
    if result['errors']:raise SystemExit(1)
if __name__=='__main__':main()
