"""Fail-closed delivery evidence regressions; all runtime records are isolated fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('entry-gate-check.py')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class EvidenceGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.home = Path(self.tmp.name) / 'home'
        self.home.mkdir()
        self.env = {**os.environ, 'HOME':str(self.home)}
        for key in ('UNIFIED_DEV_FLOW_SKIP_REVIEW','UNIFIED_DEV_FLOW_FORCE'):
            self.env.pop(key,None)
        self.git('init','-q')
        self.git('config','user.name','Fixture')
        self.git('config','user.email','fixture@example.invalid')
        (self.root/'nexusarchive-java').mkdir()
        (self.root/'fixture.py').write_text('x = 1\n')
        self.git('add','fixture.py'); self.git('commit','-qm','base')
        self.git('update-ref','refs/remotes/origin/dev','HEAD')
        self.git('checkout','-qb','agent/test/fix-fixture')
        (self.root/'fixture.py').write_text('x = 2\n')
        self.git('add','fixture.py'); self.git('commit','-qm','change')
        self.head=self.git('rev-parse','HEAD').strip()
        self.diff=hashlib.sha256(self.git('diff','origin/dev..HEAD').encode()).hexdigest()
        (self.root/'.omc').mkdir()
        self.session='fixture'
        self.review=self.root/'.omc/review-fixture.md'
        self.verify=self.root/'.omc/verify-fixture.md'
        self.verify.write_text('## 验证证据\n- ai-slop-cleaner Mode B: claimed complete\n'+'Claim without proof. '*20)
        self.legacy='## 评审结论\nverdict: MERGE_READY\nreviewer: fictional-reviewer\nround: 1\ncode-review: google-code-review\nproduction-risk-review: PASS\n'+'Claim without proof. '*20
        self.review.write_text(self.legacy)

    def git(self,*args):
        p=subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=self.root,env=self.env,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        return p.stdout

    def run_gate(self,*args,stdin_text=''):
        argv=[*args,'--project-dir',str(self.root),'--session-id',self.session]
        # Dependency injection exists only in the test process, never a production
        # flag or environment override for the native-session trust root.
        code=("import importlib.util; from pathlib import Path; "
              f"s=importlib.util.spec_from_file_location('gate', {str(SCRIPT)!r}); "
              "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
              f"m.native_review_root=lambda: Path({str(self.home / '.codex/sessions')!r}).resolve(); "
              f"m.main({argv!r})")
        return subprocess.run([sys.executable,'-c',code],cwd=self.root,env=self.env,input=stdin_text,text=True,capture_output=True)

    def test_global_wrapper_without_checker_blocks(self):
        script=SCRIPT.with_name('git-pre-push-guard.sh')
        isolated=self.root/'guard-fixture.sh'
        text=script.read_text().replace('CANONICAL_USER_HOME="$(python3 -c \'import os,pwd; print(pwd.getpwuid(os.getuid()).pw_dir)\')"',
            'CANONICAL_USER_HOME='+str(self.home))
        isolated.write_text(text)
        p=subprocess.run(['bash',str(isolated)],cwd=self.root,env=self.env,input='',text=True,capture_output=True)
        self.assertNotEqual(p.returncode,0,p.stdout+p.stderr)

    def test_HOME_cannot_authorize_fabricated_runtime_records(self):
        self.bundle()
        p=subprocess.run([sys.executable,str(SCRIPT),'--guard-pr','--project-dir',str(self.root),'--session-id',self.session],cwd=self.root,env=self.env,text=True,capture_output=True)
        self.assertNotEqual(p.returncode,0,p.stdout+p.stderr)

    def test_claims_only_blocked(self):
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_record_without_evidence_blocked(self):
        self.assertNotEqual(self.run_gate('--record-review','--reviewer','fictional-reviewer','--risk-verdict','PASS').returncode,0)

    def test_inline_pass_cannot_override_failed_report(self):
        (self.root/'.omc/risk.md').write_text('FAIL - 禁止上线\n')
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_missing_hash_blocked(self):
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_skip_environment_cannot_bypass(self):
        self.env['UNIFIED_DEV_FLOW_SKIP_REVIEW']='1'
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def bundle(self):
        import time
        stamp=time.time()-20
        source={'path':'fixture.py','sha256':digest(self.root/'fixture.py'),'line':1}
        cell={'status':'PASS','reason':'Fixture check with concrete source evidence','evidence':[source]}
        keys={
          'ai-slop-cleaner':('duplication','dead_code','abstraction','boundaries','tests'),
          'google-code-review':('design','functionality','complexity','tests','naming','comments','style','documentation','description'),
          'production-risk-review':('null','collections','concurrency','database','redis','mq','api','json','time','io','frontend','legacy_data','tests')}
        sections=('understanding','dependencies','fault_analysis','classification','business_regression','extremes','hidden_bugs','evidence','verdict','deployment_rollback')
        self.reports={}
        self.report_files={}
        refs={}
        for skill in (*keys,'verification'):
            data={'skill':skill,'head':self.head,'diff_hash':self.diff,
                  'verdict':'MERGE_READY' if skill=='google-code-review' else 'PASS'}
            if skill in keys: data['checks']={k:cell for k in keys[skill]}
            if skill=='ai-slop-cleaner': data.update(mode='B',finished_at=stamp)
            if skill=='verification':
                (self.root/'.omc/test.log').write_text('Ran meaningful fixture tests: PASS\n')
                data.update(started_at=stamp+1,finished_at=stamp+2,
                    checks=[{'argv':['python3','-m','unittest'],'exit_code':0,
                             'log':{'path':'.omc/test.log','sha256':digest(self.root/'.omc/test.log')}}])
            if skill=='production-risk-review':
                data['sections']={k:cell for k in sections}
                data['fault_chains']=[dict(cell,trigger=f'trigger-{n}',chain=['trigger','cause']) for n in range(3)]
            path=self.root/f'.omc/{skill}.json';path.write_text(json.dumps(data))
            self.reports[skill]=data;self.report_files[skill]=path
            refs[skill]={'path':str(path.relative_to(self.root)),'sha256':digest(path)}
        native=self.home/'.codex/sessions/fixture.jsonl';native.parent.mkdir(parents=True)
        rows=[{'type':'response_item','payload':{'type':'function_call','namespace':'collaboration','name':'spawn_agent','call_id':'spawn'}},
              {'type':'response_item','payload':{'type':'function_call_output','call_id':'spawn','output':json.dumps({'task_name':'/root/reviewer'})}}]
        attestations={}
        for n,skill in enumerate(('google-code-review','production-risk-review')):
            receipt={'skill':skill,'head':self.head,'diff_hash':self.diff,'report_sha256':refs[skill]['sha256'],
                     'cleanup_sha256':refs['ai-slop-cleaner']['sha256'],
                     'verification_sha256':refs['verification']['sha256'],'verdict':self.reports[skill]['verdict']}
            if n: receipt['code_review_sha256']=refs['google-code-review']['sha256']
            event=f'review-{n}'
            rows.append({'type':'response_item','payload':{'type':'agent_message','id':event,'author':'/root/reviewer',
                'content':[{'type':'input_text','text':'REVIEW_RECEIPT '+json.dumps(receipt)}],
                'internal_chat_message_metadata_passthrough':{'create_time':stamp+3+n,
                    'content_item_metadata':[{'provenance':{'type':'tool','namespace':'collaboration'}}]}}})
            attestations[skill]={'transcript_path':str(native),'event_id':event,'reviewer':'/root/reviewer'}
        native.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
        self.native=native;self.rows=rows
        self.bundle_data={'version':1,'head':self.head,'diff_hash':self.diff,'reports':refs,'attestations':attestations}
        self.bundle_file=self.root/'.omc/evidence.json'
        self.save_bundle()

    def save_bundle(self):
        self.bundle_file.write_text(json.dumps(self.bundle_data))
        self.review.write_text(self.legacy.replace('fictional-reviewer','/root/reviewer')+
            f'\ndiff_hash: {self.diff}\nevidence_bundle: .omc/evidence.json\nevidence_bundle_sha256: {digest(self.bundle_file)}\n')

    def test_negative_native_result_can_be_recorded_but_never_delivered(self):
        self.bundle();skill='google-code-review'
        self.reports[skill]['verdict']='NEEDS_FIXES'
        self.report_files[skill].write_text(json.dumps(self.reports[skill]))
        self.bundle_data['reports'][skill]['sha256']=digest(self.report_files[skill])
        del self.bundle_data['reports']['production-risk-review']
        del self.bundle_data['attestations']['production-risk-review']
        item=self.rows[2]['payload']
        receipt=json.loads(item['content'][0]['text'].removeprefix('REVIEW_RECEIPT '))
        receipt.update(verdict='NEEDS_FIXES',report_sha256=digest(self.report_files[skill]))
        item['content'][0]['text']='REVIEW_RECEIPT '+json.dumps(receipt)
        self.native.write_text('\n'.join(json.dumps(r) for r in self.rows[:3]))
        self.save_bundle()
        p=self.run_gate('--record-review','--reviewer','/root/reviewer','--verdict','NEEDS_FIXES','--evidence-bundle','.omc/evidence.json')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('verdict: NEEDS_FIXES',self.review.read_text())
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_valid_native_bundle_passes_and_records(self):
        self.bundle()
        p=self.run_gate('--record-review','--reviewer','/root/reviewer','--evidence-bundle','.omc/evidence.json')
        self.assertEqual(p.returncode,0,p.stderr)
        p=self.run_gate('--guard-pr');self.assertEqual(p.returncode,0,p.stderr)

    def test_modified_report_blocked(self):
        self.bundle();self.report_files['production-risk-review'].write_text('{}')
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_modified_log_blocked(self):
        self.bundle();(self.root/'.omc/test.log').write_text('changed')
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_missing_risk_section_blocked_even_with_updated_hash(self):
        self.bundle();skill='production-risk-review';del self.reports[skill]['sections']['dependencies']
        self.report_files[skill].write_text(json.dumps(self.reports[skill]))
        self.bundle_data['reports'][skill]['sha256']=digest(self.report_files[skill]);self.save_bundle()
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_failed_report_cannot_be_overridden_by_inline_pass(self):
        self.bundle();skill='production-risk-review';self.reports[skill]['verdict']='FAIL'
        self.report_files[skill].write_text(json.dumps(self.reports[skill]))
        self.bundle_data['reports'][skill]['sha256']=digest(self.report_files[skill]);self.save_bundle()
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_missing_runtime_source_blocked(self):
        self.bundle();self.native.unlink()
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_user_prompt_with_receipt_cannot_impersonate_reviewer(self):
        self.bundle()
        for row in self.rows[2:]:row['payload'].update(type='message',role='user')
        self.native.write_text('\n'.join(json.dumps(r) for r in self.rows))
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_ordinary_file_outside_native_root_blocked(self):
        self.bundle();other=self.root/'.omc/fake-runtime.jsonl';other.write_bytes(self.native.read_bytes())
        for v in self.bundle_data['attestations'].values():v['transcript_path']=str(other)
        self.save_bundle();self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_signature_does_not_cover_changed_source(self):
        self.bundle();(self.root/'fixture.py').write_text('x = 3\n')
        self.git('add','fixture.py');self.git('commit','-qm','changed')
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_wrong_stage_order_blocked(self):
        self.bundle();self.rows[2],self.rows[3]=self.rows[3],self.rows[2]
        self.native.write_text('\n'.join(json.dumps(r) for r in self.rows))
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_hash_is_mandatory_even_with_valid_bundle(self):
        self.bundle();self.review.write_text('\n'.join(x for x in self.review.read_text().splitlines() if not x.startswith('diff_hash:')))
        self.assertNotEqual(self.run_gate('--guard-pr').returncode,0)

    def test_every_pushed_ref_is_checked(self):
        self.bundle()
        branch='agent/test/fix-second'
        self.git('checkout','-qb',branch)
        (self.root/'fixture.py').write_text('x = 3\n');self.git('add','fixture.py');self.git('commit','-qm','second')
        second=self.git('rev-parse','HEAD').strip()
        self.git('checkout','-q','agent/test/fix-fixture')
        data=f'refs/heads/agent/test/fix-fixture {self.head} refs/heads/agent/test/fix-fixture '+('0'*40)+'\n'
        data+=f'refs/heads/{branch} {second} refs/heads/{branch} '+('0'*40)+'\n'
        p=self.run_gate('--guard-push',stdin_text=data)
        self.assertNotEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('门禁放行',p.stdout)

if __name__ == '__main__':
    unittest.main()
