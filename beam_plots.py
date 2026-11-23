"""Matplotlib rendering helpers for Beam Designer."""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from beam_calculations import BeamInput, BeamResult


def make_figure() -> Figure:
    return Figure(figsize=(10, 8), dpi=100, constrained_layout=True)


def _colors(dark: bool) -> dict[str, str]:
    return ({"surface": "#1e293b", "text": "#f8fafc", "grid": "#64748b", "navy": "#7dd3fc", "load": "#fbbf24", "ok": "#86efac"}
            if dark else {"surface": "#ffffff", "text": "#172554", "grid": "#cbd5e1", "navy": "#003da5", "load": "#b45309", "ok": "#15803d"})


def draw_all(figure: Figure, data: BeamInput | None, result: BeamResult | None, dark: bool = False) -> None:
    """Draw the beam and three response diagrams, or a validation prompt."""
    colors = _colors(dark)
    figure.clear()
    figure.set_facecolor(colors["surface"])
    axes = figure.subplots(2, 2)
    if data is None or result is None:
        for axis in axes.flat:
            axis.set_facecolor(colors["surface"])
            axis.text(.5, .5, "Enter valid inputs to calculate", ha="center", va="center", color=colors["text"], transform=axis.transAxes)
            axis.set_xticks([])
            axis.set_yticks([])
        return

    beam_axis, shear_axis, moment_axis, deflection_axis = axes.flat
    _draw_beam(beam_axis, data, result, colors)
    _draw_response(shear_axis, result.x_in / 12, result.shear_kip, "Shear", "kip", result.max_shear_kip, result.max_shear_location_ft, colors)
    _draw_response(moment_axis, result.x_in / 12, result.moment_kip_in / 12, "Moment", "kip-ft", result.max_moment_kip_ft, result.max_moment_location_ft, colors)
    _draw_response(deflection_axis, result.x_in / 12, result.deflection_in, "Deflection", "in (down +)", result.max_deflection_in, result.max_deflection_location_ft, colors)


def _style(axis, colors: dict[str, str]) -> None:
    axis.set_facecolor(colors["surface"])
    axis.tick_params(colors=colors["text"], labelsize=8)
    axis.xaxis.label.set_color(colors["text"])
    axis.yaxis.label.set_color(colors["text"])
    axis.title.set_color(colors["text"])
    for spine in axis.spines.values():
        spine.set_color(colors["grid"])
    axis.grid(True, alpha=.35, color=colors["grid"])


def _draw_beam(axis, data: BeamInput, result: BeamResult, colors: dict[str, str]) -> None:
    _style(axis, colors)
    length = data.span_ft
    axis.set_title("Beam and loads", fontweight="bold")
    axis.plot([0, length], [0, 0], color=colors["navy"], linewidth=5, solid_capstyle="butt")
    if data.configuration == "Simply supported":
        axis.fill([0, -.32, .32], [-.06, -.55, -.55], color=colors["text"])
        axis.fill([length, length - .32, length + .32], [-.06, -.55, -.55], color=colors["text"])
        reaction_items = ((0, result.reactions_kip["RA"], "RA"), (length, result.reactions_kip["RB"], "RB"))
    else:
        axis.plot([0, 0], [-.9, .9], color=colors["text"], linewidth=4)
        reaction_items = ((0, result.reactions_kip["R"], "R"),)
    for location, reaction, name in reaction_items:
        direction = 1 if reaction >= 0 else -1
        axis.plot([location, location], [-.66 * direction, -.10 * direction], color=colors["ok"], linewidth=1.5)
        triangle_y = -.10 * direction
        axis.fill([location - .12, location + .12, location], [triangle_y - .12 * direction, triangle_y - .12 * direction, triangle_y + .12 * direction], color=colors["ok"])
        axis.text(location, -.82 * direction, f"{name} = {reaction:.2f} k", ha="center", va="top" if direction > 0 else "bottom", fontsize=8, color=colors["ok"])
    for load in data.point_loads:
        if load.magnitude_kip == 0:
            continue
        up = load.direction == "Up"
        head_y, tail_y = (.18, .92) if not up else (-.18, -.92)
        axis.plot([load.location_ft, load.location_ft], [tail_y, head_y], color=colors["load"], linewidth=1.8)
        if up:
            triangle = [head_y + .14, head_y - .10, head_y - .10]
        else:
            triangle = [head_y - .14, head_y + .10, head_y + .10]
        axis.fill([load.location_ft, load.location_ft - .12, load.location_ft + .12], triangle, color=colors["load"])
        axis.text(load.location_ft, tail_y + (.11 if not up else -.11), f"{load.magnitude_kip:g} k", ha="center", va="bottom" if not up else "top", fontsize=8, color=colors["load"])
    for load in data.uniform_loads:
        if load.magnitude_kip_per_ft == 0 or load.start_ft == load.end_ft:
            continue
        y = .98
        axis.plot([load.start_ft, load.end_ft], [y, y], color=colors["load"], linewidth=1.2)
        for position in np.linspace(load.start_ft, load.end_ft, 7):
            axis.plot([position, position], [y, .24], color=colors["load"], linewidth=.8)
            axis.fill([position, position - .08, position + .08], [.16, .31, .31], color=colors["load"])
        axis.text((load.start_ft + load.end_ft) / 2, y + .11, f"{load.magnitude_kip_per_ft:g} k/ft", ha="center", fontsize=8, color=colors["load"])
    axis.set_xlim(-max(1, length * .07), length + max(1, length * .07))
    axis.set_ylim(-1.25, 1.35)
    axis.set_xlabel("Position (ft)")
    axis.set_yticks([])


def _draw_response(axis, x, values, title, units, maximum, position, colors):
    _style(axis, colors)
    axis.plot(x, values, color=colors["navy"], linewidth=1.8)
    axis.axhline(0, color=colors["grid"], linewidth=.8)
    index = int(np.argmax(np.abs(values)))
    axis.scatter([x[index]], [values[index]], color=colors["load"], zorder=3, s=20)
    axis.annotate(f"max |{maximum:.2f}| @ {position:.2f} ft", (x[index], values[index]), xytext=(5, 8), textcoords="offset points", fontsize=7, color=colors["text"])
    axis.set_title(title, fontweight="bold")
    axis.set_xlabel("Position (ft)")
    axis.set_ylabel(units)
