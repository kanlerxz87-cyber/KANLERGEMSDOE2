import json
import unittest
from pathlib import Path


class RunCardProtocolTests(unittest.TestCase):
    def test_parallel_lattice_overlap_is_a_literal_duplicate_stop(self):
        card = json.loads(Path("docs/run-card.json").read_text())
        artifact = card["parallel_artifact_review"]

        self.assertGreater(
            artifact["reported_final_dots_within_3px_of_R13_spacing5_lattice_pct"],
            artifact["prompt_limit_pct"],
        )
        self.assertIn("DUPLICATE STOP", artifact["literal_protocol_result"])
        self.assertEqual(card["verdict"], "negative")
        self.assertIsNone(card["raster_sha256"])
        self.assertIn("not accepted", artifact["prior_parallel_selector_verdict"])

    def test_source_reported_holdout_is_not_claimed_as_current_session_run(self):
        card = json.loads(Path("docs/run-card.json").read_text())

        self.assertIsNone(card["holdout"]["dti"])
        self.assertEqual(card["holdout"]["status"].split(" — ", 1)[0], "NOT RUN by this session")
        self.assertIsNone(card["submission_name"])
        self.assertEqual(card["weekly_slots_used"], 0)


if __name__ == "__main__":
    unittest.main()
