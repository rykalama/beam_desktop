import tempfile
import unittest
from pathlib import Path

from beam_calculations import PointLoad, UniformLoad
from beam_design_io import make_design, open_design, save_design


class DesignPersistenceTests(unittest.TestCase):
    def test_saved_design_round_trips_every_input(self):
        design = make_design("Cantilever", 18, "Steel", "W14x22",
                             [PointLoad(4.5, 6, "Down"), PointLoad(1.25, 12, "Up")],
                             [UniformLoad(1.5, 2, 10)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.beam.json"
            save_design(path, design)
            restored = open_design(path)
        self.assertEqual(restored["configuration"], "Cantilever")
        self.assertEqual(restored["span_ft"], 18)
        self.assertEqual(restored["material"], "Steel")
        self.assertEqual(restored["section"], "W14x22")
        self.assertEqual(restored["point_loads"], [PointLoad(4.5, 6, "Down"), PointLoad(1.25, 12, "Up")])
        self.assertEqual(restored["uniform_loads"], [UniformLoad(1.5, 2, 10)])
        self.assertEqual(design["beam"]["deflection_limit_in"], 18 * 12 / 360)

    def test_invalid_design_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.beam.json"
            path.write_text('{"format": "other"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                open_design(path)
