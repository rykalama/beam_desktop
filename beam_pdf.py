"""PDF calculation-sheet export for Beam Designer."""

from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages

from beam_calculations import BeamInput, BeamResult
from beam_plots import draw_calculation_sheet, make_figure


def export_calculation_sheet(path: str | Path, data: BeamInput, result: BeamResult,
                             material: str, section: str, properties: dict) -> None:
    """Save a one-page landscape PDF containing inputs, checks, and diagrams."""
    figure = make_figure()
    figure.set_size_inches(11, 8.5)
    draw_calculation_sheet(figure, data, result, material, section, properties)
    with PdfPages(path) as pdf:
        pdf.savefig(figure, bbox_inches="tight")
