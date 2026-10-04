import json
import unittest
from pathlib import Path
from runner import replay


class ReplayTests(unittest.TestCase):
    def test_contracts_and_missing_guards(self):
        cases = json.loads((Path(__file__).parent / 'cases.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']):
                self.assertEqual(replay(case['events']), case['expected'])
                self.assertNotEqual(replay(case['events'], case['guard']), case['expected'])

    def test_unknown_event_is_rejected(self):
        with self.assertRaises(ValueError):
            replay([{'type': 'unrecognized'}])

    def test_unrelated_cancel_does_not_cancel_current_request(self):
        events = [{'type': 'request', 'revision': 2}, {'type': 'cancel', 'revision': 1},
                  {'type': 'result', 'revision': 2, 'call_id': 'x', 'action': 'book:B'}]
        self.assertEqual(replay(events)['actions'], ['book:B'])


if __name__ == '__main__':
    unittest.main()
