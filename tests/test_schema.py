import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from render import validate,esc

class SchemaTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.dir=Path(self.t.name);(self.dir/'raw.csv').write_text('seed,b,t\n1,0.2,0.3\n2,0.4,0.5\n')
  self.obj={'title':'Test','record_type':'comparison','questions':[{'id':'Q1','text':'Compare outputs','evidence':[{'path':'raw.csv','locator':'header'}]}], 'preregistration':{'status':'not_recorded','evidence':[]}, 'blocks':[{'id':'B1','kind':'observation','title':'Measured result','tier':'main','question_ids':['Q1'],'provides':['metric'],'requires':[],'elements':[{'type':'table','headers':['a','b'],'rows':[['2','3']],'evidence':[{'path':'raw.csv','locator':'row'}]}]}]}
 def tearDown(self):self.t.cleanup()
 def test_good(self):self.assertEqual(validate(self.obj,self.dir)[0],[])
 def test_source_escape(self):
  self.obj['blocks'][0]['elements'][0]['evidence']=[{'path':'../raw.csv','locator':'row'}]
  self.assertIn('Unsafe',str(validate(self.obj,self.dir)[0]))
 def test_generated_hypothesis_blocked(self):
  b=self.obj['blocks'][0];b['kind']='verification';b['elements']=[{'type':'text','role':'observation','text':'Hypothesis supported','evidence':[{'path':'raw.csv','locator':'row'}]}]
  self.assertIn('Verification cannot assert',str(validate(self.obj,self.dir)[0]))
 def test_interpretive_prose_blocked(self):
  b=self.obj['blocks'][0];b['elements']=[{'type':'text','role':'observation','text':'The results suggest major progress','evidence':[{'path':'raw.csv','locator':'row'}]}]
  self.assertIn('Interpretive',str(validate(self.obj,self.dir)[0]))
 def test_tex_escape(self):self.assertEqual(esc('x_1 & 20%'),'x\\_1 \\& 20\\%')
 def test_repeated_folds_need_real_chart(self):
  b=self.obj['blocks'][0]
  b['elements'][0]['rows']=[['Fold 1 NLL','0.4'],['Fold 2 NLL','0.5'],['Fold 3 NLL','0.6']]
  self.assertIn('Repeated paired observations',str(validate(self.obj,self.dir)[0]))
 def test_extra_main_tables_rejected(self):
  b=self.obj['blocks'][0]
  b['elements']=b['elements']*3
  self.assertIn('overpromoted tables',str(validate(self.obj,self.dir)[0]))
 def test_excess_prose_rejected(self):
  b=self.obj['blocks'][0]
  b['elements']=[{'type':'text','role':'definition','text':'Recorded outcome. '*18,'evidence':[{'path':'raw.csv','locator':'row'}]} for _ in range(7)]
  self.assertIn('excessive main prose',str(validate(self.obj,self.dir)[0]))
if __name__=='__main__':unittest.main()
