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
