#!/usr/bin/env python3
"""Bounded read-only arithmetic on saved CSV records. Does NOT rerun a model.

Output is a computational aid, not an independently accepted scientific verdict.
"""
import argparse,csv,hashlib,json,time,math,sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-dir',required=True)
    ap.add_argument('--csv',required=True,help='Path relative to source folder')
    ap.add_argument('--value',required=True,help='Source-recorded numeric column')
    ap.add_argument('--group-by',default='',help='Optional source grouping column')
    ap.add_argument('--weight',default='',help='Optional nonnegative weight column')
    ap.add_argument('--output',required=True)
    ap.add_argument('--seconds',type=float,default=60.0)
    a=ap.parse_args()
    root=Path(a.source_dir).resolve()
    path=Path(a.csv)
    if path.is_absolute() or '..' in path.parts:raise ValueError('CSV path must be source-relative')
    p=(root/path).resolve()
    if root not in p.parents or not p.is_file():raise ValueError('CSV source unavailable/outside root')
    if p.stat().st_size>50_000_000:raise ValueError('CSV exceeds 50 MB cap: use a scoped source subset')
    groups={};row_count=0;start=time.monotonic()
    with p.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle)
        for key in [a.value,a.group_by,a.weight]:
            if key and key not in (reader.fieldnames or []):raise ValueError('Missing source CSV column: '+key)
        for row in reader:
            if time.monotonic()-start>a.seconds:raise TimeoutError('Saved CSV audit exceeded time budget')
            row_count+=1
            if row_count>1_000_000:raise ValueError('CSV audit row cap exceeded')
            group=row[a.group_by] if a.group_by else 'ALL'
            value=float(row[a.value])
            weight=float(row[a.weight]) if a.weight else 1.
            if not(math.isfinite(value) and math.isfinite(weight) and weight>=0):raise ValueError('Invalid/nonfinite numeric value or weight')
            item=groups.setdefault(group,{'rows':0,'weight':0.,'weighted_sum':0.})
            item['rows']+=1;item['weight']+=weight;item['weighted_sum']+=value*weight
    out={'scope':'Existing saved CSV only, no model rerun','source':a.csv,
         'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
         'column':a.value,'group_by':a.group_by or None,'weight':a.weight or None,
         'total_rows':row_count,'groups':{key:{'rows':z['rows'],'sum':z['weighted_sum'],
            'mean':z['weighted_sum']/z['weight'] if z['weight'] else None,
            'weight_sum':z['weight']} for key,z in sorted(groups.items())}}
    Path(a.output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'groups':len(groups),'rows':row_count,'saved_to':a.output}))
if __name__=='__main__':main()
