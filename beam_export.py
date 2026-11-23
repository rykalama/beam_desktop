"""CSV export for calculated beam response values."""

from __future__ import annotations

import csv
from pathlib import Path

from beam_calculations import BeamResult


CSV_HEADERS = ("x_ft", "V_kip", "M_kip_ft", "deflection_in")


def export_results_csv(path: str | Path, result: BeamResult) -> None:
    """Write an Excel-friendly UTF-8 CSV with one row per calculation point."""
    with Path(path).open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADERS)
        for x_in, shear, moment_kip_in, deflection in zip(
                result.x_in, result.shear_kip, result.moment_kip_in, result.deflection_in):
            writer.writerow((f"{x_in / 12:.8f}", f"{shear:.8f}",
                             f"{moment_kip_in / 12:.8f}", f"{deflection:.8f}"))
