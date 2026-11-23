"""Stateless beam analysis routines, deliberately independent of the GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np


Configuration = Literal["Simply supported", "Cantilever"]


@dataclass(frozen=True)
class PointLoad:
    magnitude_kip: float
    location_ft: float
    direction: Literal["Down", "Up"] = "Down"

    @property
    def signed_downward_kip(self) -> float:
        return self.magnitude_kip if self.direction == "Down" else -self.magnitude_kip


@dataclass(frozen=True)
class UniformLoad:
    magnitude_kip_per_ft: float
    start_ft: float
    end_ft: float


@dataclass(frozen=True)
class BeamInput:
    configuration: Configuration
    span_ft: float
    point_loads: Sequence[PointLoad]
    uniform_loads: Sequence[UniformLoad]
    elastic_modulus_ksi: float
    inertia_in4: float
    section_modulus_in3: float
    allowable_stress_ksi: float


@dataclass(frozen=True)
class BeamResult:
    x_in: np.ndarray
    shear_kip: np.ndarray
    moment_kip_in: np.ndarray
    deflection_in: np.ndarray
    reactions_kip: dict[str, float]
    fixed_end_moment_kip_ft: float | None
    max_shear_kip: float
    max_shear_location_ft: float
    max_moment_kip_ft: float
    max_moment_location_ft: float
    max_deflection_in: float
    max_deflection_location_ft: float
    bending_stress_ksi: float
    deflection_limit_in: float
    bending_ratio: float
    deflection_ratio: float


def validate_input(data: BeamInput) -> list[str]:
    """Return all validation messages; a blank list means the input is usable."""
    errors: list[str] = []
    if data.configuration not in ("Simply supported", "Cantilever"):
        errors.append("Choose a valid beam configuration.")
    if not 1 <= data.span_ft <= 200:
        errors.append("Span must be between 1 and 200 ft.")
    if data.elastic_modulus_ksi <= 0 or data.inertia_in4 <= 0 or data.section_modulus_in3 <= 0:
        errors.append("Selected section properties must be positive.")
    if data.allowable_stress_ksi <= 0:
        errors.append("Allowable bending stress must be positive.")
    for number, load in enumerate(data.point_loads, 1):
        if not 0 <= load.magnitude_kip <= 100:
            errors.append(f"Point load {number}: magnitude must be between 0 and 100 kip.")
        if not 0 <= load.location_ft <= data.span_ft:
            errors.append(f"Point load {number}: location must be within the span.")
        if load.direction not in ("Down", "Up"):
            errors.append(f"Point load {number}: choose Up or Down.")
    for number, load in enumerate(data.uniform_loads, 1):
        if not 0 <= load.magnitude_kip_per_ft <= 10:
            errors.append(f"Uniform load {number}: magnitude must be between 0 and 10 kip/ft.")
        if not 0 <= load.start_ft <= data.span_ft or not 0 <= load.end_ft <= data.span_ft:
            errors.append(f"Uniform load {number}: interval must be within the span.")
        if load.start_ft > load.end_ft:
            errors.append(f"Uniform load {number}: start must not exceed end.")
    return errors


def _cumulative_trapezoid(values: np.ndarray, x: np.ndarray) -> np.ndarray:
    accumulated = np.zeros_like(values)
    accumulated[1:] = np.cumsum((values[1:] + values[:-1]) * np.diff(x) / 2)
    return accumulated


def analyze_beam(data: BeamInput, samples: int = 4001) -> BeamResult:
    """Analyze a prismatic beam using consistent kip-inch units.

    Positive internal moment is sagging. Deflection is returned positive downward,
    hence the curvature used for the displayed downward coordinate is -M/(EI).
    """
    errors = validate_input(data)
    if errors:
        raise ValueError(" ".join(errors))

    length_in = data.span_ft * 12.0
    points = [load for load in data.point_loads if load.magnitude_kip != 0]
    uniforms = [load for load in data.uniform_loads if load.magnitude_kip_per_ft != 0 and load.start_ft != load.end_ft]
    key_positions = [0.0, length_in]
    key_positions.extend(load.location_ft * 12.0 for load in points)
    key_positions.extend(edge * 12.0 for load in uniforms for edge in (load.start_ft, load.end_ft))
    x = np.unique(np.concatenate((np.linspace(0.0, length_in, samples), np.asarray(key_positions))))

    total_downward = sum(load.signed_downward_kip for load in points)
    total_downward += sum(load.magnitude_kip_per_ft * (load.end_ft - load.start_ft) for load in uniforms)
    moment_downward_about_left = sum(load.signed_downward_kip * load.location_ft * 12.0 for load in points)
    moment_downward_about_left += sum(
        load.magnitude_kip_per_ft / 12.0
        * ((load.start_ft + load.end_ft) * 6.0)
        * ((load.end_ft - load.start_ft) * 12.0)
        for load in uniforms
    )

    if data.configuration == "Simply supported":
        right_reaction = moment_downward_about_left / length_in
        left_reaction = total_downward - right_reaction
        reactions = {"RA": left_reaction, "RB": right_reaction}
        fixed_end_moment = None
        left_moment = 0.0
    else:
        reactions = {"R": total_downward}
        fixed_end_moment = -moment_downward_about_left / 12.0
        left_moment = -moment_downward_about_left

    shear = np.full_like(x, reactions.get("RA", reactions.get("R", 0.0)))
    moment = left_moment + reactions.get("RA", reactions.get("R", 0.0)) * x
    for load in points:
        position = load.location_ft * 12.0
        active = x >= position
        shear[active] -= load.signed_downward_kip
        moment[active] -= load.signed_downward_kip * (x[active] - position)
    for load in uniforms:
        start, end = load.start_ft * 12.0, load.end_ft * 12.0
        intensity = load.magnitude_kip_per_ft / 12.0
        covered = np.clip(x - start, 0.0, end - start)
        shear -= intensity * covered
        moment -= intensity * (covered * (x - start) - covered**2 / 2)

    curvature = -moment / (data.elastic_modulus_ksi * data.inertia_in4)
    slope = _cumulative_trapezoid(curvature, x)
    deflection = _cumulative_trapezoid(slope, x)
    if data.configuration == "Simply supported":
        # Add the integration constant that satisfies y(0)=y(L)=0.
        deflection -= (deflection[-1] / length_in) * x

    shear_index = int(np.argmax(np.abs(shear)))
    moment_index = int(np.argmax(np.abs(moment)))
    deflection_index = int(np.argmax(np.abs(deflection)))
    maximum_moment_kip_in = abs(moment[moment_index])
    maximum_deflection = abs(deflection[deflection_index])
    deflection_limit = length_in / 360.0
    stress = maximum_moment_kip_in / data.section_modulus_in3
    return BeamResult(
        x_in=x,
        shear_kip=shear,
        moment_kip_in=moment,
        deflection_in=deflection,
        reactions_kip=reactions,
        fixed_end_moment_kip_ft=fixed_end_moment,
        max_shear_kip=float(abs(shear[shear_index])),
        max_shear_location_ft=float(x[shear_index] / 12.0),
        max_moment_kip_ft=float(maximum_moment_kip_in / 12.0),
        max_moment_location_ft=float(x[moment_index] / 12.0),
        max_deflection_in=float(maximum_deflection),
        max_deflection_location_ft=float(x[deflection_index] / 12.0),
        bending_stress_ksi=float(stress),
        deflection_limit_in=float(deflection_limit),
        bending_ratio=float(stress / data.allowable_stress_ksi),
        deflection_ratio=float(maximum_deflection / deflection_limit),
    )
