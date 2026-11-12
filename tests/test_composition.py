import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_composition import check

class RelationMapTests(unittest.TestCase):
    def setUp(self):
        ev={"path":"protocol.md","locator":"section: variable"}
        obs={"path":"results.csv","locator":"columns: nll"}
        self.record={
          "questions":[{"id":"Q1","text":"Compare input representations."}],
          "blocks":[
            {"id":"B1","tier":"main","question_ids":["Q1"],
             "elements":[{"type":"equation","latex":"X_R=X_F[:,I]","evidence":[ev]}]},
            {"id":"B2","tier":"main","question_ids":["Q1"],
             "elements":[{"type":"table","headers":["Input","NLL"],"rows":[["RAW3","0.5"]],
                          "evidence":[obs]}]}
          ]}
        self.audit={
          "composition_schema":"relation-map-v1",
          "relations":[
            {"id":"R1","question_id":"Q1","role":"definition",
             "statement":"RAW3 equals the recorded feature subset of FULL7.",
             "evidence":[ev],"expression_ids":["B1.1"],"depends_on":[]},
            {"id":"R2","question_id":"Q1","role":"observation",
             "statement":"Observed NLL on the recorded test sessions.",
             "evidence":[obs],"expression_ids":["B2.1"],"depends_on":["R1"]}
          ],
          "removed_redundancies":[],
          "reviewed_by":"AI candidate; semantic review is not independently certified"
        }

    def test_clean_relation_map(self):
        self.assertEqual(check(self.record,self.audit),[])

    def test_legacy_prose_audit_rejected(self):
        self.audit.pop("composition_schema")
        self.assertIn("old prose-justification",str(check(self.record,self.audit)))

    def test_orphan_expression_rejected(self):
        self.audit["relations"].pop()
        self.assertIn("not necessary",str(check(self.record,self.audit)))

    def test_relation_requires_evidence(self):
        self.audit["relations"][0]["evidence"]=[]
        self.assertIn("lacks path + locator",str(check(self.record,self.audit)))

    def test_relation_source_must_match_expression(self):
        self.audit["relations"][0]["evidence"]=[{"path":"other.md","locator":"field"}]
        self.assertIn("cannot be matched",str(check(self.record,self.audit)))

    def test_wrong_question_rejected(self):
        self.audit["relations"][1]["question_id"]="Q2"
        self.assertIn("unknown source question",str(check(self.record,self.audit)))

    def test_future_dependency_rejected(self):
        self.audit["relations"][0]["depends_on"]=["R2"]
        self.assertIn("does not precede",str(check(self.record,self.audit)))

    def test_pdf_scientific_order_must_match_dependency(self):
        self.record["blocks"] = list(reversed(self.record["blocks"]))
        self.assertIn("human reading order",str(check(self.record,self.audit)))

    def test_missing_prerequisite_rejected(self):
        self.audit["relations"][1]["depends_on"]=["R4"]
        self.assertIn("missing prerequisite",str(check(self.record,self.audit)))

    def test_deletion_of_nonunique_element_rejected(self):
        self.audit["relations"][0]["expression_ids"]=["B1.1","B2.1"]
        self.assertIn("Deletion test",str(check(self.record,self.audit)))

    def test_multiple_viewpoints_need_distinct_relation(self):
        fig={"type":"chart","evidence":[{"path":"results.csv","locator":"columns: nll"}]}
        self.record["blocks"][1]["elements"].append(fig)
        self.assertIn("not necessary",str(check(self.record,self.audit)))
        self.audit["relations"].append({
            "id":"R3","question_id":"Q1","role":"observation",
            "statement":"Across-record variability in the measured NLL values.",
            "evidence":[{"path":"results.csv","locator":"columns: nll"}],
            "expression_ids":["B2.2"],"depends_on":["R2"]})
        self.assertEqual(check(self.record,self.audit),[])

    def test_same_element_cannot_answer_unrelated_question(self):
        self.record["questions"].append({"id":"Q2"})
        self.audit["relations"].append({
            "id":"R3","question_id":"Q2","role":"scope",
            "statement":"Population boundary from original procedure.",
            "evidence":[{"path":"protocol.md","locator":"section: variable"}],
            "expression_ids":["B1.1"],"depends_on":[]})
        self.assertIn("not linked to expression",str(check(self.record,self.audit)))

    def test_content_draft_displays_relation_map_before_prose(self):
        from build_draft import preview
        self.record["title"]="Synthetic relation-check fixture"
        self.record["questions"][0]["text"]="Recorded comparison question"
        for block in self.record["blocks"]:
            block["title"]=block["id"]+" measured object"
            block["kind"]="definition"
        result=preview(self.record,self.audit)
        self.assertIn("Scientific relation plan",result)
        self.assertIn("RAW3 equals the recorded feature subset",result)
        self.assertLess(result.index("Scientific relation plan"),result.index("Main scientific composition"))

    def test_two_identical_relations_are_rejected(self):
        self.audit['relations'][1]['statement']=self.audit['relations'][0]['statement']
        self.assertIn('duplicated',str(check(self.record,self.audit)))
    def test_each_relation_expression_link_needs_evidence(self):
        self.audit['relations'][0]['expression_ids']=['B1.1','B2.1']
        self.assertIn('evidence cannot be matched',str(check(self.record,self.audit)))
    def test_generic_self_description_rejected(self):
        self.audit["relations"][0]["statement"]="Required component of the research question"
        self.assertIn("lacks a concrete",str(check(self.record,self.audit)))

if __name__ == "__main__":unittest.main()
