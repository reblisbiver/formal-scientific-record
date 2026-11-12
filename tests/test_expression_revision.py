import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_expression_revision import compare
class TestExpressionRevision(unittest.TestCase):
    def setUp(self):
        self.raw='# Test\n\\[ p_t=1 \\]\n| Regime | AUC | Brier |\n|---|---|---|\n| T=100 | 0.9 | 0.1 |\nA repeated explanation.\n'
    def test_remove_prose_only(self):
        x=compare(self.raw,self.raw.replace('A repeated explanation.',''))
        self.assertEqual(x['status'],'PASS_MECHANICAL_ONLY')
    def test_formula_change_rejected(self):
        x=compare(self.raw,self.raw.replace('p_t=1','p_t=2'))
        self.assertEqual(x['status'],'FAIL')
    def test_redundant_brier_definition_label_can_be_shortened(self):
        old='| Brier (mean squared probability error) | 0.15 | 0.16 | 0.01 |'
        new='| Brier | 0.15 | 0.16 | 0.01 |'
        self.assertEqual(compare(old,new)['status'],'PASS_MECHANICAL_ONLY')
    def test_changing_metric_identity_is_rejected(self):
        old='| Brier (mean squared probability error) | 0.15 | 0.16 | 0.01 |'
        new='| NLL | 0.15 | 0.16 | 0.01 |'
        self.assertEqual(compare(old,new)['status'],'FAIL')
    def test_unit_scope_parenthetical_cannot_be_deleted(self):
        old='| NLL (nats/trial) | 0.45 | 0.46 | 0.01 |'
        new='| NLL | 0.45 | 0.46 | 0.01 |'
        self.assertEqual(compare(old,new)['status'],'FAIL')
    def test_numeric_row_change_rejected(self):
        x=compare(self.raw,self.raw.replace('0.9 | 0.1','0.8 | 0.1'))
        self.assertEqual(x['status'],'FAIL')
if __name__=='__main__':unittest.main()
