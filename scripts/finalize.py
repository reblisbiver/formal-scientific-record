#!/usr/bin/env python3
"""Generate one final hash-bound report QA verdict. Original research state is separate."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

from metric_registry import evaluate_registry

VISUAL={'PASS','FAIL','NOT_VERIFIED'}
NUMERIC={'REAGGREGATED','SOURCE_ONLY','UNAVAILABLE','NOT_CHECKED'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def attach_registry(result,verdict):
    result['metric_registry']=verdict
    result['report_integrity_status']=verdict.get('report_integrity_status',verdict.get('status','CANDIDATE'))
    result['numeric_scope_status']=verdict.get('numeric_scope_status','NOT_VERIFIED')
    result['metric_acceptance']=verdict.get('metric_markers',{})
    result['metric_inventory']=verdict.get('metric_inventory',{
        'status':'FAIL','exact_set_equality':False
    })
    result['deployment_readiness']=verdict.get('deployment_readiness','NOT_READY')
    return result
def evaluate(out):
    errors=[];notes=[]
    registry_path=out/'metric_registry.json'
    registry_verdict=None
    if registry_path.is_file():
        try:
            registry=json.loads(registry_path.read_text())
            registry_verdict=evaluate_registry(registry,registry_path,out/'record.json')
            if registry_verdict.get('status')!='PASS':
                errors.extend('Metric registry: '+error for error in registry_verdict.get('errors',[]))
                if not registry_verdict.get('errors'):
                    errors.append('Metric registry: integrity gate is CANDIDATE')
        except (OSError,UnicodeError,json.JSONDecodeError) as exc:
            errors.append('Metric registry: metric_registry.json could not be parsed: '+str(exc))
            registry_verdict={
                'status':'CANDIDATE',
                'schema':None,
                'registry_sha256':digest(registry_path),
                'errors':['metric_registry.json could not be parsed: '+str(exc)],
                'warnings':[],
            }
    req=['report.pdf','report.tex','record.json','composition_audit.json','validation.json','visual_qa.json','numeric_audit.json']
    for f in req:
        if not (out/f).is_file(): errors.append('Missing artifact: '+f)
    if errors:
        result={'report_status':'CANDIDATE','errors':errors}
        if registry_verdict is not None: attach_registry(result,registry_verdict)
        return result
    validation=json.loads((out/'validation.json').read_text())
    visual=json.loads((out/'visual_qa.json').read_text())
    numeric=json.loads((out/'numeric_audit.json').read_text())
    current=digest(out/'report.pdf')
    if validation.get('pdf_sha256')!=current:errors.append('Rendered PDF hash differs from validation.json; rebuild and reverify')
    if validation.get('report_tex_sha256')!=digest(out/'report.tex'):errors.append('Generated TeX differs from renderer output; no manual TeX edits')
    if validation.get('record_sha256')!=digest(out/'record.json'):errors.append('Record changed since PDF render; regenerate from record')
    if validation.get('layout_warnings'):
        resolution=visual.get('layout_resolution')
        if not isinstance(resolution,dict) or resolution.get('decision')!='JUSTIFIED' or len(str(resolution.get('reason','')).strip())<50:
            errors.append('Unresolved body-page imbalance: '+str(validation['layout_warnings']))
    if validation.get('tectonic_exit_code')!=0:errors.append('LaTeX compile not PASS')
    if validation.get('mechanical_render_checks')!='PASS':errors.append('PDF mechanical check not PASS')
    if validation.get('errors'):errors.append('Semantic record validator has errors')
    if visual.get('pdf_sha256')!=current:errors.append('Visual QA has no matching FINAL PDF hash')
    state=visual.get('status')
    if state not in VISUAL:errors.append('Unrecognized visual status')
    if state!='PASS':errors.append('Final visual pages not verified PASS')
    page_count=validation.get('pdf_pages',0)
    inspected=visual.get('pages_inspected',[])
    if sorted(set(inspected))!=list(range(1,page_count+1)): errors.append('Not every final PDF page visually reviewed')
    if not visual.get('method'):errors.append('Visual QA method omitted')
    for finding in visual.get('issues',[]):
        if finding.get('severity','blocking')=='blocking' and not finding.get('resolved',False):
            errors.append('Unresolved visual defect: '+str(finding.get('description')))
    if numeric.get('record_sha256')!=digest(out/'record.json'):
        errors.append('Numeric audit not tied to current scientific record; rerun saved-data checks')
    if numeric.get('status') not in NUMERIC:errors.append('Unrecognized numeric audit scope')
    if numeric.get('status')=='NOT_CHECKED':errors.append('Saved-data numeric reaggregation not attempted or scoped')
    if numeric.get('status') in ('SOURCE_ONLY','UNAVAILABLE') and not numeric.get('reason'):
        errors.append('Uncomputed numeric outcome lacks explanation')
    if numeric.get('status')=='REAGGREGATED':
        if not numeric.get('sources') or numeric.get('checks_passed',0)<1:
            errors.append('Reaggregation lacks source/checked quantities')
        if numeric.get('checks_failed',0):errors.append('Numeric check failures present')
    proc=subprocess.run([sys.executable,str(Path(__file__).parent/'check_composition.py'),str(out/'record.json'),str(out/'composition_audit.json')],capture_output=True,text=True,timeout=25)
    if proc.returncode:errors.append('Composition audit failed: '+proc.stdout[-700:]+proc.stderr[-250:])
    # Research acceptance is intentionally informational, never a success gate.
    source_science=numeric.get('original_science_status','NOT_SPECIFIED')
    result={
      'report_status':'PASS' if not errors else 'CANDIDATE',
      'pdf_sha256':current,
      'science_report_faithfulness':'SOURCE_LINKS_STRUCTURAL_ONLY',
      'composition_gate':'PASS' if proc.returncode==0 else 'FAIL',
      'numeric_audit_scope':numeric.get('status'),
      'pdf_visual_gate':state,
      'original_research_acceptance':source_science,
      'model_training_or_algorithm_rerun':'OUT_OF_SCOPE',
      'human_approval':'NOT_REQUIRED_BY_FSR_WORKFLOW',
      'errors':errors,
      'limitations':['Semantic completeness and scientific truth cannot be proven by validators alone']
    }
    if registry_verdict is not None: attach_registry(result,registry_verdict)
    return result

def main():
    a=argparse.ArgumentParser();a.add_argument('output_dir');opts=a.parse_args()
    out=Path(opts.output_dir).resolve()
    res=evaluate(out)
    (out/'final_status.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(res,indent=2,ensure_ascii=False))
    if res['report_status']!='PASS':sys.exit(1)
if __name__=='__main__':main()
