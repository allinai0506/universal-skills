from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_domain_model.py"
INIT = ROOT / "scripts" / "init_domain_model.py"
spec = importlib.util.spec_from_file_location("validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def test_valid_greenfield_model_passes(self):
        self.assertEqual([], validator.validate(self.fixtures / "valid-domain-model.md", "greenfield"))

    def test_invalid_model_fails(self):
        errors = validator.validate(self.fixtures / "invalid-domain-model.md", "greenfield")
        self.assertTrue(errors)
        self.assertTrue(any("glossary" in e for e in errors))
        self.assertTrue(any("sources of truth" in e for e in errors))

    def test_brownfield_example_bundle_passes(self):
        model = ROOT / "examples" / "brownfield-bid-system" / "domain-model.md"
        self.assertEqual([], validator.validate_brownfield_bundle(model))

    def test_brownfield_requires_read_only_rule(self):
        model = (ROOT / "examples" / "brownfield-bid-system" / "domain-model.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "domain-model.md"
            p.write_text(model.replace("READ_ONLY", "DISCOVERY_ONLY"), encoding="utf-8")
            errors = validator.validate(p, "brownfield")
            self.assertTrue(any("READ_ONLY" in e for e in errors))

    def test_brownfield_init_creates_four_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            result = subprocess.run(
                [sys.executable, str(INIT), str(repo), "--mode", "brownfield"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            expected = {
                "domain-model.md",
                "semantic-conflicts.md",
                "source-of-truth.md",
                "semantic-migration-plan.md",
            }
            actual = {p.name for p in (repo / "docs").glob("*.md")}
            self.assertEqual(expected, actual)

    def test_init_does_not_overwrite_existing_domain_model(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            docs = repo / "docs"
            docs.mkdir(parents=True)
            target = docs / "domain-model.md"
            target.write_text("KEEP_ME", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(INIT), str(repo), "--mode", "brownfield"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("KEEP_ME", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
