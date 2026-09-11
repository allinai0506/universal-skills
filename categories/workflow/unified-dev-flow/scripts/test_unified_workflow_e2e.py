#!/usr/bin/env python3
"""Complete real-Git CLI lifecycle, including stale dependency acceptance."""
import unittest

from test_unified_workflow_cli import CLIProject


class WorkflowE2ETests(CLIProject):
    def accept(self, identifier):
        self.mutate("verify", "--task-id", identifier, "--command-id", "unit")
        self.mutate("review", "record", "--task-id", identifier,
                    "--assertion-file", self.document(self.review(identifier)))
        self.mutate("task", "accept", "--task-id", identifier)

    def test_working_tree_delivery_reverification_and_canonical_replay(self):
        self.initialize()
        self.add("A")
        self.add("B", ["A"])
        self.mutate("task", "ready", "--task-id", "B", code=3)
        self.start("A")
        self.mutate("task", "report", "--task-id", "A", "--report-file", self.document({
            "report": {"summary": "Implemented A"}, "workspace_revision": self.observation().to_dict()}))
        self.root.joinpath("input.txt").write_text("fail\n")
        self.mutate("verify", "--task-id", "A", "--command-id", "unit", code=6)
        _, state = self.store()
        self.assertFalse(state.tasks["A"].verifications[-1]["success"])
        self.assertEqual(state.tasks["A"].status, "ready")
        self.root.joinpath("input.txt").write_text("pass fixed\n")
        self.mutate("task", "start", "--task-id", "A")
        self.accept("A")
        self.start("B")
        self.accept("B")
        self.assertTrue(all(t.currently_satisfied for t in self.store()[1].tasks.values()))
        self.root.joinpath("input.txt").write_text("pass changed\n")
        denied = self.mutate("run", "complete", code=3)
        self.assertEqual(denied["reason_code"], "EVIDENCE_STALE")
        _, state = self.store()
        self.assertEqual({t.status for t in state.tasks.values()}, {"stale"})
        self.assertFalse(any(t.currently_satisfied for t in state.tasks.values()))
        for identifier in ("A", "B"):
            self.start(identifier)
            self.accept(identifier)
        _, state = self.store()
        delivery = dict(delivery_target="working_tree", acceptance_set_sha256=state.acceptance_set_sha256,
                        workspace_revision=self.observation().to_dict(),
                        provenance={"provider": "human", "reference": str(self.root)})
        self.mutate("delivery", "record", "--delivery-file", self.document(delivery))
        self.mutate("run", "complete")
        status = self.call("status")
        self.assertEqual(status["state"]["status"], "completed")
        self.assertEqual(status, self.call("replay"))
        self.assertEqual(status["state"]["deliveries"][-1]["acceptance_set_sha256"],
                         status["state"]["acceptance_set_sha256"])
        for path in (".omc", ".superpowers", ".codegraph"):
            self.assertFalse((self.root / path).exists())


if __name__ == "__main__":
    unittest.main()
