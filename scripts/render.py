#!/usr/bin/env python3
"""Deterministic English scientific-record renderer. Scientific content must be source-grounded record.json.
No AI, network, or experiment execution. Python stdlib + PyMuPDF (fitz) + a real LaTeX engine.
"""
import argparse,csv,hashlib,json,math,re,shutil,subprocess,sys
from pathlib import Path

KINDS={'definition','assumption','objective','method','comparison','observation','verification','scope'}
TYPES={'text','equation','table','chart'}
ROLES={'definition','condition','procedure','observation','missing'}
FORBIDDEN=re.compile(r'\b(?:results? (?:suggest|indicat|impli)|this (?:suggests|indicates|implies)|we (?:propose|recommend|hypothesiz)|future work|further research (?:could|should)|likely because|this demonstrates that)\b',re.I)
UNSAFE_LATEX=re.compile(r'\\(?:input|include|write|openout|read|usepackage|documentclass|begin\s*\{\s*(?:document|filecontents))\b',re.I)


def sha(data):return hashlib.sha256(data).hexdigest()

def esc(s):
    table={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return re.sub(r'[\\&%$#_{}~^]',lambda m:table[m.group(0)],str(s))

def safe_path(source,path):
 if not path or Path(path).is_absolute() or '..' in Path(path).parts:raise ValueError('Unsafe evidence path: '+str(path))
 root=source.resolve();p=(source/path).resolve()
 if p!=root and root not in p.parents:raise ValueError('Evidence outside folder: '+str(path))
 if not p.is_file():raise ValueError('Source evidence file missing: '+str(path))
 return p

def validate(record, source):
 errors=[];warnings=[]; evmap=[]; all_provides=set();main=[]; qs={q.get('id') for q in record.get('questions',[])}
 if not record.get('title') or len(record['title'])>145:errors.append('Missing/long title')
 if not qs or None in qs:errors.append('No source-recorded research questions')
 for q in record.get('questions',[]):
  if len(q.get('text',''))>360 or not q.get('text'):errors.append('Question missing or too long')
  if not q.get('evidence'):errors.append('Question missing source evidence: '+str(q.get('id')))
  for ev in q.get('evidence',[]):
   try:safe_path(source,ev['path']);evmap.append((q['id'],ev))
   except Exception as e: errors.append(str(e))
 if record.get('preregistration',{}).get('status') not in ('not_recorded','evidenced'):
  errors.append('Invalid preregistration state')
 if record.get('preregistration',{}).get('status')=='evidenced' and not record.get('preregistration',{}).get('evidence'):
  errors.append('Preregistration asserted without source evidence')
 for i,b in enumerate(record.get('blocks',[])):
  ident=b.get('id',str(i))
  if b.get('kind') not in KINDS:errors.append('Invalid block kind '+ident)
  if b.get('tier','main') not in ('main','appendix'):errors.append('Invalid tier '+ident)
  if not set(b.get('question_ids',[])).issubset(qs) or not b.get('question_ids'):errors.append('Invalid/missing question link '+ident)
  if b.get('tier','main')=='main':main.append(b)
  for x in b.get('provides',[]):
   if x in all_provides: warnings.append('Duplicated provided concept '+x)
   all_provides.add(x)
  if b.get('kind')=='verification' and record.get('preregistration',{}).get('status')!='evidenced':
   for e in b.get('elements',[]):
    if e.get('role')!='missing' or 'NOT EVALUATED' not in e.get('text',''):
     errors.append('Verification cannot assert verdict without registered evidence: '+ident)
  if len(b.get('title',''))>95:errors.append('Long section title '+ident)
  for j,e in enumerate(b.get('elements',[])):
   e_id=f'{ident}.{j+1}'
   if e.get('type') not in TYPES:errors.append('Bad element type '+e_id)
   if e.get('type')=='text':
    if e.get('role') not in ROLES:errors.append('Bad prose role '+e_id)
    if len(e.get('text',''))>360:errors.append('Overlong statement '+e_id)
    if FORBIDDEN.search(e.get('text','')):errors.append('Interpretive/speculative prose '+e_id)
   if e.get('type')=='equation':
    if UNSAFE_LATEX.search(e.get('latex','')): errors.append('Disallowed TeX command '+e_id)
   if e.get('type')=='chart':
    try: safe_path(source,e['chart']['csv'])
    except Exception as ex:errors.append('Chart: '+str(ex))
    if not e.get('chart',{}).get('ylabel') or not e.get('chart',{}).get('xlabel'):
     errors.append('Chart axis labels/units missing: '+e_id)
   if not e.get('evidence') and e.get('type')!='chart':errors.append('No evidence for '+e_id)
   for ev in e.get('evidence',[]):
    try:safe_path(source,ev['path']);evmap.append((e_id,ev))
    except Exception as ex:errors.append(str(ex))
   if e.get('type')=='table':
    h=e.get('headers',[]); rows=e.get('rows',[])
    if len(h)<2 or not rows or any(len(x)!=len(h) for x in rows):errors.append('Malformed table '+e_id)
    if b.get('tier','main')=='main' and len(rows)>13:errors.append('Too many body table rows: '+e_id)
 for b in record.get('blocks',[]):
  for x in b.get('requires',[]):
   if x not in all_provides:errors.append('Unresolved scientific dependency '+x)
 for q in qs:
  if not any(q in b.get('question_ids',[]) and b.get('kind') not in ('scope','verification') for b in main):errors.append('No substantive main block for question '+str(q))
 if record.get('record_type')=='comparison' and len(qs)==1:
  main_e=[e for b in main for e in b.get('elements',[])]
  n_tables=sum(e.get('type')=='table' for e in main_e)
  n_charts=sum(e.get('type')=='chart' for e in main_e)
  prose_chars=sum(len(e.get('text','')) for e in main_e if e.get('type')=='text')
  if n_tables>2:errors.append(f'Single-question comparison overpromoted tables ({n_tables}>2). Move secondary detail to appendix tier.')
  if n_charts>2:errors.append(f'Single-question comparison has {n_charts} charts; retain only distinct necessary views.')
  repeated_matched=any(e.get('type')=='table' and sum(any(str(cell).lower().startswith(('fold ','seed ','participant ')) for cell in row[:1]) for row in e.get('rows',[]))>=3 for e in main_e)
  if repeated_matched and n_charts==0:errors.append('Repeated paired observations require one source-grounded comparison chart in the main body, not table-only compression.')
  if prose_chars>1900:errors.append(f'Single-question comparison excessive main prose ({prose_chars}>1900 characters). Compress and move secondary detail to appendix.')
 # A deletion test candidate is a main block with no unique declared semantic contribution and no downstream dependencies.
 provided_counts={x:sum(x in b.get('provides',[]) for b in main) for x in all_provides}
 used={x for b in main for x in b.get('requires',[])}
 deletion=[]
 for b in main:
  if not any(provided_counts.get(x,0)==1 or x in used for x in b.get('provides',[])):
   if sum(b.get('kind')==c.get('kind') and set(b.get('question_ids',[]))&set(c.get('question_ids',[])) for c in main)>1:
    deletion.append(b.get('id'))
 return errors,warnings,evmap,deletion

def chart_pdf(source,out,chart):
 try:import fitz
 except ImportError:raise ValueError('PyMuPDF (fitz) required for deterministic vector PDF figures')
 path=safe_path(source,chart['csv']); kind=chart['kind'];xkey=chart['x'];ys=chart['y']
 with path.open(newline='',encoding='utf-8-sig') as f:raw=list(csv.DictReader(f))
 if len(raw)<2:raise ValueError('Chart requires >=2 observed CSV records')
 if kind not in ('line','scatter','bar','histogram','paired_delta'):raise ValueError('Unsupported chart type '+kind)
 labels=[str(r[xkey]) for r in raw]; vals=[]
 for key in ys:vals.append([float(r[key]) for r in raw])
 if kind=='paired_delta':
  if len(vals)!=2:raise ValueError('Paired delta requires baseline and treatment CSV columns')
  vals=[[a-b for a,b in zip(vals[1],vals[0])]]
  legend=['Treatment - Baseline']
 else:legend=chart.get('legend',ys)
 if len(raw)>35 or len(vals)>5:raise ValueError('Chart exceeds readability budget; summarize/aggregate before charting')
 numbers=[v for series in vals for v in series];
 if not all(math.isfinite(x) for x in numbers):raise ValueError('Nonfinite chart number')
 lo=min(numbers+[0] if kind in ('bar','paired_delta') else numbers);hi=max(numbers+[0] if kind in ('bar','paired_delta') else numbers)
 pad=max((hi-lo)*.13,abs(hi)*.035,.002); lo-=pad;hi+=pad
 w,h=445,223; L,R,B,T=55,15,37,23; plotw=w-L-R;ploth=h-T-B
 d=fitz.open();page=d.new_page(width=w,height=h)
 def text(x,y,s,fontsize=8,color=(0,0,0)):page.insert_text((x,y),str(s),fontsize=fontsize,fontname='helv',color=color)
 def line(x1,y1,x2,y2,width=.65,color=(0,0,0)):page.draw_line((x1,y1),(x2,y2),color=color,width=width)
 def sy(v):return T+(hi-v)/(hi-lo)*ploth
 n=len(labels);sx=lambda i:L+(i+.5)*plotw/n
 line(L,T,L,h-B);line(L,h-B,w-R,h-B)
 ticks=([lo,lo/2,0,hi/2,hi] if lo<0<hi else [lo+(hi-lo)*j/4 for j in range(5)])
 for v in ticks:
  yp=sy(v);line(L-3,yp,L,yp);text(8,yp+3,'0' if abs(v)<1e-14 else f'{v:.3g}',8)
  line(L,yp,w-R,yp,.15,(.78,.78,.78))
 if lo<0<hi:line(L,sy(0),w-R,sy(0),.8,(.36,.36,.36))
 max_labels=10;step=max(1,math.ceil(n/max_labels))
 for i,label in enumerate(labels):
  if i%step==0:text(max(1,sx(i)-9),h-B+12,label[:9],8)
 for j,series in enumerate(vals):
  color=(.03,.03,.03) if j==0 else (.45,.45,.45) if j==1 else (.7,.7,.7)
  pts=[]
  for i,v in enumerate(series):
   xx=sx(i)+j*(4 if kind=='bar' else 0);yy=sy(v)
   if kind=='bar':line(xx,sy(0),xx,yy,4,color)
   else:page.draw_circle((xx,yy),2.1,color=color,fill=color);pts.append((xx,yy))
  if kind=='line' and len(pts)>1:page.draw_polyline(pts,color=color,width=1.1)
 text(w/2-45,h-5,chart['xlabel'],9)
 text(5,11,chart['ylabel'],9)
 if len(legend)>1:
  for j,label in enumerate(legend):text(w-170,T+9+j*11,f'{j+1}: {label[:25]}',8)
 d.save(out,garbage=4,deflate=True);d.close();return {'csv':chart['csv'],'csv_sha256':sha(path.read_bytes()),'n':len(raw),'series':len(vals),'kind':kind}

def render(record,source,out):
 import itertools
 pieces=['\\documentclass[11pt]{article}',r'\usepackage{fsr}',r'\begin{document}',r'\fsrtitle{'+esc(record['title'])+'}{'+esc(record.get('subtitle',''))+'}']
 pieces+=['\\noindent\\textbf{Research question'+('s' if len(record['questions'])>1 else '')+'.} '+ '; '.join(esc(q['text']) for q in record['questions'])+r'\par\medskip']
 ctr=0;mapping=[];charts=[]
 for b in record['blocks']:
  if b.get('tier','main')=='appendix':continue
  ctr+=1; pieces+=['\\section{'+esc(b['title'])+'}']
  active_hypothesis_group=None
  for j,e in enumerate(b.get('elements',[])):
   eid=f"{b['id']}.{j+1}";mapping.append((eid,b['title'],e.get('evidence',[])))
   t=e['type']
   if t=='text':
    if e.get('presentation')=='hypothesis':
     group=e.get('hypothesis_group','')
     if not re.fullmatch(r'H[1-9][0-9]*',group) or not re.fullmatch(r'[A-Za-z0-9 ()/-]+',e.get('group_title','')):
      raise ValueError('Invalid hypothesis display group or title')
     if group!=active_hypothesis_group:
      if active_hypothesis_group is not None:pieces.append(r'\end{list}')
      pieces += [r'\medskip\noindent\textbf{'+esc(group)+r'}\enspace{\small\textsc{'+esc(e['group_title'])+r'}}\par',
                 r'\begin{list}{}{\setlength{\leftmargin}{2.4em}\setlength{\labelwidth}{1.5em}\setlength{\labelsep}{.4em}\setlength{\topsep}{.3em}\setlength{\itemsep}{.35em}\setlength{\parsep}{0pt}}']
      active_hypothesis_group=group
     marker=e.get('hypothesis_marker','')
     assert marker=='' or re.fullmatch(r'[a-z]',marker)
     pieces.append(r'\item['+(r'\textbf{('+marker+')} ' if marker else '')+r'] {\itshape '+esc(e.get('text',''))+'} ')
    else:
     if active_hypothesis_group is not None:
      pieces.append(r'\end{list}');active_hypothesis_group=None
     pieces += [esc(e.get('text',''))+r'\par']

   elif t=='equation':
    if active_hypothesis_group is not None:pieces.append(r'\end{list}');active_hypothesis_group=None
    pieces += ['\\begin{equation}',e['latex'],'\\end{equation}']
    if e.get('symbols'):
     symbols=e['symbols']
     if len(symbols)>=3:
      pieces += [r'{\small\begin{tabularx}{\linewidth}{@{}p{.17\linewidth}L@{}}']
      for q in symbols:
       pieces += ['$'+q['symbol']+'$ & '+esc(q['meaning'])+'\\\\']
      pieces += [r'\end{tabularx}}\par']
     else:
      pieces += [r'{\small '+r'\quad '.join('$'+q['symbol']+'$: '+esc(q['meaning']) for q in symbols)+r'}\par']
   elif t=='table':
    if active_hypothesis_group is not None:pieces.append(r'\end{list}');active_hypothesis_group=None
    headers=e['headers'];colnum=len(headers)
    if colnum>6:raise ValueError('More than 6 table columns not human-readable')
    pieces+=[r'\begin{center}\small',r'\begin{tabularx}{\linewidth}{@{}'+('L'*colnum)+r'@{}}',r'\toprule',' & '.join(r'\textbf{'+esc(x)+'}' for x in headers)+r'\\',r'\midrule']
    prev_group=''
    for row in e['rows']:
     if e.get('presentation')=='hypothesis_status':
      match=re.match(r'^(H[0-9]+(?:\([a-z]\))?)',str(row[0]))
      group=match.group(1) if match else ''
      if prev_group and group and group!=prev_group:pieces.append(r'\addlinespace[.42em]')
      prev_group=group
      first=esc(str(row[0]))
      if match:first=r'\textbf{'+esc(match.group(1))+'}'+esc(str(row[0])[len(match.group(1)):])
      last=esc(str(row[-1]))
      for prefix in ['NOT ESTABLISHED','NOT TESTED / UNDETERMINED','Descriptively observed']:
       if str(row[-1]).startswith(prefix):
        last=r'\textbf{'+esc(prefix)+'}'+esc(str(row[-1])[len(prefix):])
        break
      cells=[first]+[esc(x) for x in row[1:-1]]+[last]
      pieces+=[' & '.join(cells)+r'\\']
     else:pieces+=[' & '.join(esc(x) for x in row)+r'\\']
    pieces += [r'\bottomrule',r'\end{tabularx}',r'\end{center}']
   elif t=='chart':
    if active_hypothesis_group is not None:pieces.append(r'\end{list}');active_hypothesis_group=None
    pdf=f'chart_{b["id"]}_{j+1}.pdf';meta=chart_pdf(source,out/pdf,e['chart']);charts.append(dict(file=pdf,**meta))
    pieces += [r'\begin{center}',r'\includegraphics[width=.90\linewidth]{'+pdf+'}',r'\captionof{figure}{'+esc(e.get('caption','Observed measurements.'))+'}',r'\end{center}']
  if active_hypothesis_group is not None:pieces.append(r'\end{list}')
 # APPENDIX only evidence: do not inject paths before this point.
 pieces += [r'\clearpage',r'\appendix',r'\raggedright\footnotesize',
            r'\section{Source locations}',r'\noindent Evidence for displayed scientific statements.\par\medskip']
 for eid,title,evidence in mapping:
  pieces += [r'\noindent\textrm{'+esc(eid)+'}: '+esc(title)+r'\par']
  for ev in evidence:
   path=ev.get('path','')
   if any(ch in path for ch in '{}\\'): raise ValueError('Unsafe LaTeX path metadata')
   pieces += [r'\noindent\hspace*{1em}\url{'+path+'}; '+esc(ev.get('locator','unspecified'))+r'\par']
 for q in record['questions']:
  for ev in q.get('evidence',[]):
   path=ev['path']
   if any(ch in path for ch in '{}\\'): raise ValueError('Unsafe LaTeX question path')
   pieces += [r'\noindent Question '+esc(q['id'])+r': \url{'+path+'}; '+esc(ev.get('locator','unspecified'))+r'\par']
 pieces += [r'\end{document}']
 return '\n'.join(pieces)+'\n',charts

def main():
 ap=argparse.ArgumentParser();ap.add_argument('record');ap.add_argument('--source-dir',required=True);ap.add_argument('--output-dir',required=True);ap.add_argument('--tectonic',default='');a=ap.parse_args()
 source=Path(a.source_dir).expanduser().resolve();out=Path(a.output_dir).expanduser().resolve(); out.mkdir(parents=True,exist_ok=True)
 record=json.loads(Path(a.record).read_text());errors,warnings,ev,deletion=validate(record,source)
 status={'validated_source_dir':str(source),'record_sha256':sha(Path(a.record).read_bytes()),'errors':errors,'warnings':warnings,'deletion_candidates':deletion,'source_files':{},'science_numeric_audit':'NOT AUTOMATICALLY VERIFIED for user-supplied aggregate table cells','visual_review':'NOT YET PERFORMED'}
 for _,e in ev:
  p=safe_path(source,e['path']);status['source_files'][e['path']]=sha(p.read_bytes())
 (out/'validation.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n')
 if errors:raise ValueError('Semantic validation failed: '+'; '.join(errors))
 code,charts=render(record,source,out)
 (out/'fsr.sty').write_bytes((Path(__file__).resolve().parent.parent/'assets/fsr.sty').read_bytes())
 (out/'report.tex').write_text(code)
 exe=a.tectonic or shutil.which('tectonic') or '/private/tmp/tectonic-017/tectonic'
 if not Path(exe).exists(): raise RuntimeError('Real TeX engine unavailable; no PDF substitute allowed')
 env=dict(__import__('os').environ)
 cache=env.get('TECTONIC_CACHE_DIR') or '/private/tmp/tectonic-cache'
 if Path(cache).is_dir():
  env['TECTONIC_CACHE_DIR']=cache
  args=[exe,'--only-cached','--untrusted','--keep-logs','--outdir',str(out),str(out/'report.tex')]
 else:
  args=[exe,'--outdir',str(out),str(out/'report.tex')]
 # An earlier PDF must never satisfy validation of the current LaTeX build.
 previous_pdf=out/'report.pdf'
 if previous_pdf.exists(): previous_pdf.unlink()
 proc=subprocess.run(args,cwd=out,env=env,capture_output=True,text=True,timeout=150)
 status['tectonic_exit_code']=proc.returncode;status['tectonic_log_tail']=(proc.stdout+'\n'+proc.stderr)[-4000:];status['charts']=charts
 if proc.returncode!=0 or not (out/'report.pdf').exists():
  (out/'validation.json').write_text(json.dumps(status,indent=2)+'\n')
  raise RuntimeError('LaTeX compilation failed: '+status['tectonic_log_tail'][-1200:])
 status['pdf_sha256']=sha((out/'report.pdf').read_bytes());status['report_tex_sha256']=sha((out/'report.tex').read_bytes());status['render_status']='COMPILED; PENDING VISUAL/SCIENCE AUDIT'; (out/'validation.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'report_pdf':str(out/'report.pdf'),'report_tex':str(out/'report.tex'),'validation':str(out/'validation.json'),'status':status['render_status'],'errors':errors,'warnings':warnings,'deletion_candidates':deletion},indent=2))
if __name__=='__main__':main()
