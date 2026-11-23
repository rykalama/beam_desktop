import tempfile
import unittest
from pathlib import Path

from beam_calculations import BeamInput, UniformLoad, analyze_beam
from beam_data import section_properties
from beam_pdf import export_calculation_sheet


class CalculationSheetTests(unittest.TestCase):
    def test_calculation_sheet_is_written_as_pdf(self):
        data = BeamInput("Simply supported", 20, [], [UniformLoad(1, 0, 20)], 29000, 204, 33.4, 30)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calculation-sheet.pdf"
            export_calculation_sheet(path, data, analyze_beam(data), "Steel", "W12x26", section_properties("Steel", "W12x26"))
            contents = path.read_bytes()
        self.assertTrue(contents.startswith(b"%PDF"))
        self.assertGreater(len(contents), 10_000)
