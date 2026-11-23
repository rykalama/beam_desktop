"""JSON persistence for Beam Designer input data."""

from __future__ import annotations

import json
from pathlib import Path

from beam_calculations import BeamInput, PointLoad, UniformLoad, analyze_beam, validate_input
from beam_data import MATERIALS, section_properties


FORMAT_NAME = "beam-designer-design"
FORMAT_VERSION = 1


def make_design(configuration: str, span_ft: float, material: str, section: str,
                point_loads: list[PointLoad], uniform_loads: list[UniformLoad]) -> dict:
    """Create a validated, portable representation of one design."""
    if material not in MATERIALS or section not in MATERIALS[material]["sections"]:
        raise ValueError("The design has an unsupported material or section.")
    properties = section_properties(material, section)
    beam = BeamInput(configuration, span_ft, point_loads, uniform_loads,
                     properties["E"], properties["ix"], properties["sx"], properties["fb_allow"])
    errors = validate_input(beam)
    if errors:
        raise ValueError(" ".join(errors))
    result = analyze_beam(beam)
    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "beam": {
            "configuration": configuration,
            "span_ft": span_ft,
            "material": material,
            "section": section,
            "deflection_limit_in": result.deflection_limit_in,
            "deflection_limit_basis": "L/360",
            "point_loads": [
                {"magnitude_kip": load.magnitude_kip, "location_ft": load.location_ft, "direction": load.direction}
                for load in point_loads
            ],
            "uniform_loads": [
                {"magnitude_kip_per_ft": load.magnitude_kip_per_ft, "start_ft": load.start_ft, "end_ft": load.end_ft}
                for load in uniform_loads
            ],
        },
    }


def save_design(path: str | Path, design: dict) -> None:
    Path(path).write_text(json.dumps(design, indent=2) + "\n", encoding="utf-8")


def open_design(path: str | Path) -> dict:
    """Read and validate a design file, returning only safe application inputs."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if raw.get("format") != FORMAT_NAME or raw.get("version") != FORMAT_VERSION:
            raise ValueError("This is not a supported Beam Designer design file.")
        beam = raw["beam"]
        material, section = beam["material"], beam["section"]
        if material not in MATERIALS or section not in MATERIALS[material]["sections"]:
            raise ValueError("The design references an unsupported material or section.")
        points = [PointLoad(float(item["magnitude_kip"]), float(item["location_ft"]), item["direction"])
                  for item in beam.get("point_loads", [])]
        uniforms = [UniformLoad(float(item["magnitude_kip_per_ft"]), float(item["start_ft"]), float(item["end_ft"]))
                    for item in beam.get("uniform_loads", [])]
        properties = section_properties(material, section)
        calculation_input = BeamInput(beam["configuration"], float(beam["span_ft"]), points, uniforms,
                                      properties["E"], properties["ix"], properties["sx"], properties["fb_allow"])
        errors = validate_input(calculation_input)
        if errors:
            raise ValueError(" ".join(errors))
        return {"configuration": beam["configuration"], "span_ft": float(beam["span_ft"]),
                "material": material, "section": section, "point_loads": points, "uniform_loads": uniforms}
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not open the design file: {error}") from error
