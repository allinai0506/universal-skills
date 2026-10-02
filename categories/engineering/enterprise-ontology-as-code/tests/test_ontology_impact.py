import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/'scripts/ontology_impact.py'
def run(c,w): return subprocess.run(c,cwd=w,capture_output=True,text=True)
class T(unittest.TestCase):
 def repo(self):
  td=tempfile.TemporaryDirectory(); r=Path(td.name); run(['git','init','-q'],r); run(['git','config','user.email','a@b.c'],r); run(['git','config','user.name','T'],r); (r/'src/domain').mkdir(parents=True); (r/'ontology').mkdir(); (r/'src/domain/service.py').write_text("def x(): return 'ok'\n"); (r/'ontology/ontology.yaml').write_text('version: 0.1.0\n'); run(['git','add','.'],r); run(['git','commit','-qm','base'],r); return td,r
 def gate(self,r): return run([sys.executable,str(SCRIPT),'HEAD~1','HEAD'],r)
 def test_review(self):
  td,r=self.repo(); (r/'src/domain/service.py').write_text("status='ARCHIVED'\n"); run(['git','add','.'],r); run(['git','commit','-qm','c'],r); p=self.gate(r); self.assertEqual(p.returncode,3,p.stdout+p.stderr); td.cleanup()
 def test_ontology_pass(self):
  td,r=self.repo(); (r/'src/domain/service.py').write_text("status='ARCHIVED'\n"); (r/'ontology/rule.yaml').write_text('id: archive-status\n'); run(['git','add','.'],r); run(['git','commit','-qm','c'],r); self.assertEqual(self.gate(r).returncode,0); td.cleanup()
 def test_none_pass(self):
  td,r=self.repo(); (r/'src/domain/service.py').write_text("status='ARCHIVED'\n"); (r/'.ontology-impact.yaml').write_text('impact: none\nreason: implementation only\nevidence:\n  - src/domain/service.py\n'); run(['git','add','.'],r); run(['git','commit','-qm','c'],r); p=self.gate(r); self.assertEqual(p.returncode,0,p.stdout+p.stderr); td.cleanup()
if __name__=='__main__': unittest.main()
