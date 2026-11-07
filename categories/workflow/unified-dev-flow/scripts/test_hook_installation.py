"""Real sync installer regression: existing project policy must never be replaced."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

SYNC=Path(__file__).resolve().parents[4]/'sync.sh'
# Snapshot of the actual Husky h used in the reproduced delegation defect.
HUSKY_HELPER='#!/usr/bin/env sh\n[ "$HUSKY" = "2" ] && set -x\nn=$(basename "$0")\ns=$(dirname "$(dirname "$0")")/$n\n\n[ ! -f "$s" ] && exit 0\n\nif [ -f "$HOME/.huskyrc" ]; then\n\techo "husky - \'~/.huskyrc\' is DEPRECATED, please move your code to ~/.config/husky/init.sh"\nfi\ni="${XDG_CONFIG_HOME:-$HOME/.config}/husky/init.sh"\n[ -f "$i" ] && . "$i"\n\n[ "${HUSKY-}" = "0" ] && exit 0\n\nexport PATH="node_modules/.bin:$PATH"\nsh -e "$s" "$@"\nc=$?\n\n[ $c != 0 ] && echo "husky - $n script failed (code $c)"\n[ $c = 127 ] && echo "husky - command not found in PATH=$PATH"\nexit $c\n'

class InstallationTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.guard=self.root/'guard.sh';self.guard.write_text('#!/bin/sh\nexit 0\n');self.guard.chmod(0o755)
        self.git('init','-q');self.git('config','core.hooksPath','.githooks')
        self.hook=self.repo/'.githooks/pre-push';self.hook.parent.mkdir()

    def git(self,*args):
        p=subprocess.run(['git','-C',str(self.repo),*args],text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);return p.stdout

    def install(self):
        source=SYNC.read_text()
        match=re.search(r'^install_pre_push_review_guard\(\) \{\n.*?^\}',source,re.S|re.M)
        self.assertIsNotNone(match,'sync must expose its actual non-destructive installer')
        p=subprocess.run(['bash','-c','set -euo pipefail\n'+match.group(0)+'\ninstall_pre_push_review_guard "$1" "$2"','test',str(self.repo),str(self.guard)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);return p.stdout

    def test_missing_hook_created_and_second_run_preserves_bytes_and_mode(self):
        self.install();first=self.hook.read_bytes();mode=self.hook.stat().st_mode
        self.guard.write_text('#!/bin/sh\nexit 99\n');self.install()
        self.assertEqual(self.hook.read_bytes(),first);self.assertEqual(self.hook.stat().st_mode,mode)
        self.assertTrue(os.access(self.hook,os.X_OK))

    def test_existing_custom_rejection_preserved(self):
        self.hook.write_text('#!/bin/sh\necho ORIGINAL_REPO_GATE\nexit 37\n');self.hook.chmod(0o751)
        before=self.hook.read_bytes();mode=self.hook.stat().st_mode
        message=self.install();p=subprocess.run([str(self.hook)],capture_output=True,text=True)
        self.assertEqual(p.returncode,37);self.assertIn('ORIGINAL_REPO_GATE',p.stdout)
        self.assertEqual(self.hook.read_bytes(),before);self.assertEqual(self.hook.stat().st_mode,mode)
        self.assertIn('未自动接管',message)

    def test_symlink_and_its_target_are_preserved(self):
        target=self.root/'owned-hook.sh';target.write_text('#!/bin/sh\nexit 38\n');target.chmod(0o755)
        self.hook.symlink_to(target);before=target.read_bytes();self.install()
        self.assertTrue(self.hook.is_symlink());self.assertEqual(target.read_bytes(),before)
        self.assertEqual(subprocess.run([str(self.hook)]).returncode,38)

    def test_husky_trampoline_preserves_real_h_delegate(self):
        self.git('config','core.hooksPath','.husky/_')
        husky=self.repo/'.husky';(husky/'_').mkdir(parents=True)
        (husky/'_/h').write_text(HUSKY_HELPER)
        entry=husky/'_/pre-push';entry.write_text('#!/usr/bin/env sh\n. "$(dirname "$0")/h"');entry.chmod(0o755)
        policy=husky/'pre-push';policy.write_text('#!/bin/sh\necho ORIGINAL_REPO_GATE\nexit 37\n')
        before=entry.read_bytes();self.install()
        env={**os.environ,'HOME':str(self.root/'home'),'XDG_CONFIG_HOME':str(self.root/'config')}
        env.pop('HUSKY',None)
        p=subprocess.run([str(entry)],cwd=self.repo,env=env,capture_output=True,text=True)
        self.assertEqual(p.returncode,37,p.stdout+p.stderr);self.assertIn('ORIGINAL_REPO_GATE',p.stdout)
        self.assertEqual(entry.read_bytes(),before)

    def test_missing_guard_cannot_create_hook(self):
        self.guard.unlink()
        source=SYNC.read_text();match=re.search(r'^install_pre_push_review_guard\(\) \{\n.*?^\}',source,re.S|re.M)
        self.assertIsNotNone(match)
        p=subprocess.run(['bash','-c','set -euo pipefail\n'+match.group(0)+'\ninstall_pre_push_review_guard "$1" "$2"','test',str(self.repo),str(self.guard)],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertFalse(self.hook.exists())

    def test_sync_calls_actual_installer_and_has_no_overwrite_fallback(self):
        source=SYNC.read_text();start=source.index('    for repo in "${target_repos[@]}"; do')
        end=source.index('\n}\n',start);body=source[start:end]
        self.assertIn('install_pre_push_review_guard "$repo"',body)
        self.assertNotIn('cp -f',body)

if __name__=='__main__':unittest.main()
