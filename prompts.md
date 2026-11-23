# Request log

## 2026-11-23

- Asked: Conserve tokens by using the lowest required agent for each situation.
- Changed: Added this preference to `AGENTS.md`.
- Worked: Yes.

- Asked: Read `spec.md` and describe a Tkinter implementation plan before writing application code, including files, calculation organization, risks, and refinements.
- Changed: Read the specification and prepared a plan; no application code was written.
- Worked: Yes.

- Asked: Adjust `spec.md` to reflect the agreed Tkinter implementation plan.
- Changed: Replaced browser-only behaviors with native desktop equivalents and clarified numerical calculation, plotting, resizing, persistence, and launch requirements.
- Worked: Yes.

- Asked: Build the Tkinter beam-design application following the plan and `spec.md`.
- Changed: Added the desktop interface, built-in section data, isolated NumPy calculations, embedded Matplotlib diagrams, dependency list, and automated engineering checks.
- Worked: Yes. Python syntax checks, native Tkinter/Matplotlib construction, and all five supplied calculation validations passed.

- Asked: Run every validation case in `spec.md` against the beam calculations and report expected versus actual values.
- Changed: Executed the numerical validation cases plus representative upward and multiple-load sign/equilibrium checks; no application code changed.
- Worked: Yes. All five automated validation tests passed and the reported calculation outputs matched the specified targets.

- Asked: Add Save and Open design files, update the specification, try the feature in the app, and rerun validation cases.
- Changed: Added the File menu, JSON design persistence, round-trip and invalid-file tests, and Save/Open requirements to the specification.
- Worked: Yes. A native app save/open cycle restored a cantilever design with two point loads and one uniform load; all seven automated tests passed.

- Asked: Add CSV export of position, shear, moment, and deflection results; update the specification, try it in the app, and rerun validation cases.
- Changed: Added the export requirement, a visible CSV-export button, Excel-friendly CSV output, and a CSV structure test.
- Worked: Yes. The app exported 4,001 rows with the required columns for the default beam; all eight automated tests passed.

- Asked: Add a PDF calculation sheet with inputs, diagrams, and checks; update the specification, try it in the app, and rerun validation cases.
- Changed: Added the PDF requirement, a visible calculation-sheet export button, a landscape PDF generator, and a PDF export test.
- Worked: Yes. The app generated a 36,814-byte PDF with a valid `%PDF` header; all nine automated tests passed.

- Asked: Raise the graph titles in the PDF calculation sheet to avoid overlap with text.
- Changed: Increased PDF-only diagram title padding while preserving the on-screen chart layout.
- Worked: Yes. The calculation-sheet PDF test and the complete nine-test suite passed.
