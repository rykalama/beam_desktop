import csv
import tempfile
import unittest
from pathlib import Path

from beam_calculations import BeamInput, UniformLoad, analyze_beam
from beam_export import CSV_HEADERS, export_results_csv


class ResultExportTests(unittest.TestCase):
    def test_csv_has_expected_columns_and_all_analysis_rows(self):
        result = analyze_beam(BeamInput("Simply supported", 20, [], [UniformLoad(1, 0, 20)],
                                        29000, 204, 33.4, 30))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.csv"
            export_results_csv(path, result)
            with path.open(newline="", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))
        self.assertEqual(tuple(rows[0]), CSV_HEADERS)
        self.assertEqual(len(rows), len(result.x_in))
        self.assertEqual(float(rows[0]["x_ft"]), 0.0)
        self.assertEqual(float(rows[-1]["x_ft"]), 20.0)
        self.assertAlmostEqual(float(rows[len(rows) // 2]["M_kip_ft"]), 50.0, places=6)
