import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ontology_validate.py"

class ValidatorTests(unittest.TestCase):
    def test_valid_fixture_passes(self):
        p = subprocess.run([sys.executable, str(SCRIPT), str(ROOT / "tests/fixtures/valid/ontology")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("PASSED", p.stdout)

    def test_invalid_fixture_fails(self):
        p = subprocess.run([sys.executable, str(SCRIPT), str(ROOT / "tests/fixtures/invalid/ontology")], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("unknown object", p.stdout)
        self.assertIn("FAILED", p.stdout)

if __name__ == "__main__":
    unittest.main()
