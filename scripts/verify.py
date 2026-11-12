#!/usr/bin/env python3
"""Mechanical PDF QA + robust rasterizing, NOT semantic or final visual approval."""
import argparse,json
from pathlib import Path
import fitz
from render_pages import render_all

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output_dir');args=ap.parse_args()
    out=Path(args.output_dir);pdf=out/'report.pdf';doc=fitz.open(pdf)
    pages=[p.get_text() for p in doc]
    appendices=[i for i,t in enumerate(pages) if 'Source locations' in t or 'Provenance and machine audit' in t]
    if not appendices:raise SystemExit('Evidence appendix missing')
    appendix=appendices[0];body='\n'.join(pages[:appendix])
    issues=[];font_issues=[];body_extent=[];layout_warnings=[]
    for token in ['.json','.csv','sha256','/Users/','record_id','source_file']:
        if token in body:issues.append('Main-body evidence leak: '+token)
    for i,page in enumerate(doc):
        if len(pages[i].strip())<70:issues.append('Near-empty page '+str(i+1))
        for b in page.get_text('blocks'):
            x0,y0,x1,y1=b[:4]
            if x0 < -2 or y0 < -2 or x1 > page.rect.width+2 or y1 > page.rect.height+2:
                issues.append('Text overflow page '+str(i+1))
        if i>=appendix:continue
        spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b
               for line in b['lines'] for s in line['spans'] if s['text'].strip()]
        tiny=[s for s in spans if s['size']<6.5]
        if tiny:
            item={'page':i+1,'min_font_pt':round(min(s['size'] for s in tiny),2),
                  'examples':[s['text'][:35] for s in tiny[:6]]}
            font_issues.append(item)
            issues.append('Unreadable body font <6.5pt page '+str(i+1))
        # Ignore page-number footer (otherwise page density is always ~96%).
        content=[sp for sp in spans if sp['bbox'][1] < page.rect.height-55]
        if content:
            body_extent.append({'page':i+1,'used_vertical_fraction':round(max(sp['bbox'][3] for sp in content)/page.rect.height,3)})
    if appendix>1 and body_extent and body_extent[-1]['used_vertical_fraction']<0.46:
        layout_warnings.append('Last body page underfilled; reorganize table, figure and scope instead of shrinking labels')
    try:raster=render_all(pdf,out/'page_renders')
    except Exception as e:
        raster={'engine':None,'pages':0,'errors':[str(e)]}
        issues.append('All rasterization methods failed')
    if raster['pages']!=len(doc):issues.append('Raster page count mismatch')
    validation=json.loads((out/'validation.json').read_text())
    validation.update({'pdf_pages':len(doc),'appendix_page_1_based':appendix+1,'main_body_pages':appendix,
        'mechanical_page_issues':issues,'mechanical_render_checks':'PASS' if not issues else 'FAIL',
        'visual_review':'PENDING_FINAL_HASH_LINKED_VISUAL_QA','raster_engine':raster['engine'],
        'raster_failures':raster.get('errors',[]),'font_issues':font_issues,'body_extent':body_extent,'layout_warnings':layout_warnings})
    (out/'validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'pages':len(doc),'body_pages':appendix,'issues':issues,'render_engine':raster['engine']},indent=2))
    if issues:raise SystemExit(1)
if __name__=='__main__':main()
