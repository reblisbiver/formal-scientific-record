import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from check_relation_plan import check

class RelationPlanMicroTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/'PROTOCOL.md').write_text('Definition A. Recorded source facts.')
        ev=[{'path':'PROTOCOL.md','locator':'Definition A'}]
        self.plan={
            'questions':[{'id':'Q1'}],
            'relations':[
                {'id':'R1','role':'definition','question_id':'Q1','statement':'Recorded model state and input definition.',
                 'evidence':ev,'depends_on':[],'tier':'main'},
                {'id':'R2','role':'measurement','question_id':'Q1','statement':'Recorded metric definition, units and denominator.',
                 'evidence':ev,'depends_on':['R1'],'tier':'main'}
            ]
        }
    def tearDown(self):self.tmp.cleanup()
    def test_valid_plan(self):
        self.assertEqual(check(self.plan,self.root)[0],[])
    def test_bad_source(self):
        self.plan['relations'][0]['evidence']=[{'path':'../bad.md','locator':'X'}]
        self.assertTrue(check(self.plan,self.root)[0])
    def test_nonexistent_precondition(self):
        self.plan['relations'][1]['depends_on']=['R99']
        self.assertIn('missing dependency',str(check(self.plan,self.root)[0]))
    def test_main_cannot_depend_on_appendix_only_relation(self):
        self.plan['relations'][0]['tier']='appendix'
        self.plan['relations'][1]['tier']='main'
        errors,_=check(self.plan,self.root)
        self.assertIn('appendix-only prerequisite',str(errors))
    def test_valid_main_dependency(self):
        for r in self.plan['relations']:
            r['tier']='main'
        self.assertEqual(check(self.plan,self.root)[0],[])
    def test_no_questions_cannot_pass(self):
        self.plan['questions']=[]
        self.plan['relations'][0].pop('question_id',None)
        errors,_=check(self.plan,self.root)
        self.assertIn('No source-recorded research question',str(errors))
    def test_each_question_requires_main_relation(self):
        self.plan['questions'].append({'id':'Q2'})
        errors,_=check(self.plan,self.root)
        self.assertIn('Research question Q2 has no main scientific relation',str(errors))
    def test_appendix_only_cannot_pass(self):
        for r in self.plan['relations']:r['tier']='appendix'
        errors,_=check(self.plan,self.root)
        self.assertIn('no main scientific relation',str(errors))
    def test_missing_tier_is_rejected(self):
        self.plan['relations'][0].pop('tier')
        errors,_=check(self.plan,self.root)
        self.assertIn('explicit main/appendix tier required',str(errors))
    def test_malformed_statement_is_diagnostic_not_crash(self):
        self.plan['relations'][0]['statement']=None
        errors,_=check(self.plan,self.root)
        self.assertIn('statement must be a string',str(errors))
    def test_dense_chain_is_warning_not_scientific_rejection(self):
        for i in range(3,9):
            self.plan['relations'].append({
                'id':f'R{i}','role':'observation','question_id':'Q1',
                'statement':'Source-recorded observed quantity, with explicit unit.',
                'evidence':[{'path':'PROTOCOL.md','locator':'Definition A'}],
                'depends_on':[f'R{i-1}'],'tier':'main'})
        errors,warnings=check(self.plan,self.root)
        self.assertFalse(errors)
        self.assertIn('unusually dense',str(warnings))
if __name__=='__main__':unittest.main()
