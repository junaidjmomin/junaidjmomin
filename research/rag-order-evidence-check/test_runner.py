import json
import unittest
from pathlib import Path
from runner import evaluate, score, first_match, evidence_first


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((Path(__file__).parent / 'cases.json').read_text())

    def test_reference_is_consistent_across_orders(self):
        rows, s = evaluate(evidence_first, self.cases, [7, 19, 42])
        self.assertEqual(len(rows), 72)
        self.assertEqual(s['exact_match'], 1)
        self.assertEqual(s['answer_consistency'], 1)

    def test_order_sensitive_baseline_is_detected(self):
        _, s = evaluate(first_match, self.cases, [7, 19, 42])
        self.assertLess(s['answer_consistency'], 1)
        self.assertLess(s['exact_match'], 1)

    def test_fabricated_citation_does_not_count_as_supported(self):
        _, supported, current = score(self.cases[0], {'answer': '7', 'citations': ['invented']})
        self.assertFalse(supported)
        self.assertFalse(current)

    def test_citing_old_but_matching_text_is_not_current_authority(self):
        exact, supported, current = score(self.cases[0], {'answer': '30', 'citations': ['refund-archived']})
        self.assertFalse(exact)
        self.assertTrue(supported)
        self.assertFalse(current)


if __name__ == '__main__':
    unittest.main()
