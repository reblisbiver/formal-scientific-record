#!/usr/bin/env python3
"""Bounded, reproducible page-rendering ladder (does not itself approve visual quality)."""
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path

def render_all(pdf, directory, *, zoom=1.6):
    directory.mkdir(parents=True,exist_ok=True)
    for file in directory.glob('page-*.png'):
        file.unlink()
    failures=[]
    try:
        import fitz
        doc=fitz.open(pdf)
        if len(doc)<1: raise ValueError('empty PDF')
        for i,page in enumerate(doc):
            page.get_pixmap(matrix=fitz.Matrix(zoom,zoom),alpha=False).save(directory/f'page-{i+1:02}.png')
        return {'engine':'pymupdf','pages':len(doc),'errors':failures}
    except Exception as e: failures.append('pymupdf: '+repr(e))
    if shutil.which('pdftoppm'):
        cp=subprocess.run(['pdftoppm','-png','-r',str(int(72*zoom)),str(pdf),str(directory/'tmp')],capture_output=True,text=True,timeout=70)
        if cp.returncode==0:
            generated=sorted(directory.glob('tmp-*.png'))
            if generated:
                for i,f in enumerate(generated,1):f.rename(directory/f'page-{i:02}.png')
                return {'engine':'pdftoppm','pages':len(generated),'errors':failures}
        failures.append('pdftoppm: '+cp.stderr[-400:])
    if shutil.which('mutool'):
        cp=subprocess.run(['mutool','draw','-q','-r',str(int(72*zoom)),'-o',str(directory/'page-%02d.png'),str(pdf)],capture_output=True,text=True,timeout=70)
        generated=sorted(directory.glob('page-*.png'))
        if cp.returncode==0 and generated:return {'engine':'mutool','pages':len(generated),'errors':failures}
        failures.append('mutool: '+cp.stderr[-400:])
    raise RuntimeError('All three PDF rasterization methods unavailable/failed: '+'; '.join(failures))

def main():
    a=argparse.ArgumentParser()
    a.add_argument('pdf')
    a.add_argument('--output-dir',required=True)
    opts=a.parse_args()
    p=Path(opts.pdf)
    result=render_all(p,Path(opts.output_dir))
    result['pdf_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
