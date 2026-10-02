#!/usr/bin/env python3
from __future__ import annotations
import subprocess,sys
from pathlib import Path
import yaml
PARTS={"domain","domains","model","models","entity","entities","service","services","controller","controllers","api","dto","schema","schemas","migration","migrations","workflow","workflows","policy","policies","rule","rules"}
SUFFIX={".java",".kt",".py",".ts",".tsx",".js",".jsx",".sql",".yaml",".yml",".json"}
HINTS=("status","state","transition","enum","permission","role","policy","rule","validate","validation","archive","rollback","currentversion","versionid","relation","mapping","contract","voucher","document","归档","状态","规则","权限","凭证","关系","契约","版本","审批","移交","销毁")
def run(*a): return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT)
def norm(s): return s.replace("\\","/").lower()
def risk(f):
 p=Path(norm(f)); s=norm(f)
 return p.suffix in SUFFIX and (bool(set(p.parts)&PARTS) or any(x in s for x in ("/migration","/api/","/schema","flyway","liquibase")))
def isont(f,o):
 f,o=norm(f).strip("/"),norm(o).strip("/"); return f==o or f.startswith(o+"/")
def main(base,head,o="ontology",decl=".ontology-impact.yaml"):
 files=[x for x in run("git","diff","--name-only",base,head).splitlines() if x.strip()]
 ont=[f for f in files if isont(f,o)]; risky=[f for f in files if not isont(f,o) and norm(f)!=norm(decl) and risk(f)]
 patch=run("git","diff","--unified=0",base,head,"--",*risky).lower() if risky else ""
 hints=sorted({h for h in HINTS if h in patch}); sem=bool(risky and hints)
 print("Ontology Impact Gate"); print(f"Ontology changes: {len(ont)}"); print(f"Risky paths: {len(risky)}")
 if ont: print("RESULT: PASS\nReason: ontology changed; run ontology_validate.py."); return 0
 if not sem: print("RESULT: PASS\nReason: no semantic-risk signal detected."); return 0
 p=Path(decl)
 if p.exists():
  d=yaml.safe_load(p.read_text(encoding="utf-8")) or {}; impact=str(d.get("impact","")).lower(); reason=str(d.get("reason","")).strip(); ev=d.get("evidence") or []
  if impact=="none" and reason and ev: print("RESULT: PASS_WITH_DECLARATION\nReason: "+reason); return 0
  if impact in {"changed","unknown"}: print("RESULT: REVIEW_REQUIRED"); return 3
 print("RESULT: REVIEW_REQUIRED\nReason: semantic-risk signals without ontology change or valid no-impact declaration."); return 3
if __name__=="__main__":
 if len(sys.argv) not in (3,4,5): print("Usage: ontology_impact.py <base> <head> [ontology-path] [declaration]"); raise SystemExit(2)
 raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>=4 else "ontology",sys.argv[4] if len(sys.argv)>=5 else ".ontology-impact.yaml"))
