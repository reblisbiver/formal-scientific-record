import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from finalize import evaluate

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.p=Path(self.tmp.name)
        (self.p/"report.pdf").write_bytes(b"PDF-test-content")
        (self.p/"report.tex").write_text("LaTeX-test")
        ev={"path":"protocol.md","locator":"section: observation"}
        rec={"questions":[{"id":"Q1"}],"blocks":[{"id":"B1","tier":"main","question_ids":["Q1"],
            "elements":[{"type":"text","text":"Recorded observation.","evidence":[ev]}]}]}
        audit={"composition_schema":"relation-map-v1",
            "relations":[{"id":"R1","question_id":"Q1","role":"observation",
             "statement":"Observation from the original recorded scientific file.",
             "evidence":[ev],"expression_ids":["B1.1"],"depends_on":[]}],
            "removed_redundancies":[],
            "reviewed_by":"AI candidate; no external scientific review asserted"}
        (self.p/"record.json").write_text(json.dumps(rec))
        (self.p/"composition_audit.json").write_text(json.dumps(audit))
        self.validation={"pdf_sha256":digest(self.p/"report.pdf"),"report_tex_sha256":digest(self.p/"report.tex"),
            "record_sha256":digest(self.p/"record.json"),"tectonic_exit_code":0,
            "mechanical_render_checks":"PASS","errors":[],"pdf_pages":2,"layout_warnings":[]}
        self.visual={"status":"PASS","pdf_sha256":self.validation["pdf_sha256"],
            "pages_inspected":[1,2],"method":"Actual inspection of both pages","issues":[]}
        self.numeric={"status":"REAGGREGATED","record_sha256":digest(self.p/"record.json"),"sources":["data.csv"],"checks_passed":1,"checks_failed":0,
            "original_science_status":"NOT_ACCEPTED"}
        self.flush()
    def tearDown(self):self.tmp.cleanup()
    def flush(self):
        for file,datum in [("validation.json",self.validation),("visual_qa.json",self.visual),
                           ("numeric_audit.json",self.numeric)]:
            (self.p/file).write_text(json.dumps(datum))
    def test_happy_path_does_not_conflate_source_science(self):
        x=evaluate(self.p)
        self.assertEqual(x["report_status"],"PASS",x["errors"])
        self.assertEqual(x["original_research_acceptance"],"NOT_ACCEPTED")
    def test_modified_pdf_invalidates_result(self):
        (self.p/"report.pdf").write_bytes(b"changed document")
        self.assertEqual(evaluate(self.p)["report_status"],"CANDIDATE")
    def test_numeric_audit_cannot_be_reused_after_record_change(self):
        self.numeric["record_sha256"]="stale-record-hash"
        self.flush()
        self.assertTrue(any("Numeric audit" in x for x in evaluate(self.p)["errors"]))

    def test_changed_tex_is_rejected(self):
        (self.p/"report.tex").write_text("manually modified")
        self.assertTrue(any("Generated TeX" in e for e in evaluate(self.p)["errors"]))
    def test_missing_page_inspection_is_rejected(self):
        self.visual["pages_inspected"]=[1];self.flush()
        self.assertEqual(evaluate(self.p)["report_status"],"CANDIDATE")
    def test_underfilled_page_requires_explicit_justification(self):
        self.validation["layout_warnings"]=["Last body page severely underfilled"];self.flush()
        self.assertEqual(evaluate(self.p)["report_status"],"CANDIDATE")
        self.visual["layout_resolution"]={"decision":"JUSTIFIED","reason":
            "The isolated final-page diagram is required at full scale to preserve exact reading of all labels."}
        self.flush()
        self.assertEqual(evaluate(self.p)["report_status"],"PASS")

if __name__=="__main__":unittest.main()
