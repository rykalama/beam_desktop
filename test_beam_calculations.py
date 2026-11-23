import unittest

from beam_calculations import BeamInput, PointLoad, UniformLoad, analyze_beam


def standard_input(**changes):
    values = dict(
        configuration="Simply supported", span_ft=20, point_loads=[],
        uniform_loads=[UniformLoad(1, 0, 20)], elastic_modulus_ksi=29000,
        inertia_in4=204, section_modulus_in3=33.4, allowable_stress_ksi=30,
    )
    values.update(changes)
    return BeamInput(**values)


class BeamCalculationTests(unittest.TestCase):
    def test_full_span_uniform_load(self):
        result = analyze_beam(standard_input())
        self.assertAlmostEqual(result.max_moment_kip_ft, 50.0, places=2)
        self.assertAlmostEqual(result.max_deflection_in, 0.609, places=3)
        self.assertAlmostEqual(result.bending_stress_ksi, 17.964, places=3)

    def test_cantilever_uniform_load(self):
        result = analyze_beam(standard_input(configuration="Cantilever", span_ft=10,
            uniform_loads=[UniformLoad(1, 0, 10)]))
        self.assertAlmostEqual(result.max_moment_kip_ft, 50.0, places=2)
        self.assertAlmostEqual(result.max_deflection_in, 0.365, places=3)

    def test_center_point_load(self):
        result = analyze_beam(standard_input(point_loads=[PointLoad(5, 10)], uniform_loads=[]))
        self.assertAlmostEqual(result.reactions_kip["RA"], 2.5, places=2)
        self.assertAlmostEqual(result.reactions_kip["RB"], 2.5, places=2)
        self.assertAlmostEqual(result.max_moment_kip_ft, 25.0, places=2)

    def test_partial_uniform_load(self):
        result = analyze_beam(standard_input(span_ft=30, inertia_in4=510, section_modulus_in3=57.6,
            uniform_loads=[UniformLoad(2, 0, 15)]))
        self.assertAlmostEqual(result.reactions_kip["RA"], 22.5, places=2)
        self.assertAlmostEqual(result.reactions_kip["RB"], 7.5, places=2)
        self.assertAlmostEqual(result.max_moment_kip_ft, 126.5625, places=2)

    def test_lumber_deflects_more(self):
        steel = analyze_beam(standard_input())
        lumber = analyze_beam(standard_input(elastic_modulus_ksi=1600, inertia_in4=177.98,
            section_modulus_in3=31.64, allowable_stress_ksi=.9))
        self.assertGreater(lumber.max_deflection_in, steel.max_deflection_in)


if __name__ == "__main__":
    unittest.main()
