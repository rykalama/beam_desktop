"""Beam Designer: a native Tkinter desktop application."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from beam_calculations import BeamInput, PointLoad, UniformLoad, analyze_beam, validate_input
from beam_data import MATERIALS, section_properties
from beam_design_io import make_design, open_design, save_design
from beam_export import export_results_csv
from beam_pdf import export_calculation_sheet
from beam_plots import draw_all, make_figure


NAVY = "#003da5"
LIGHT = {"bg": "#f1f5f9", "card": "#ffffff", "text": "#172554", "muted": "#475569", "border": "#cbd5e1", "good": "#15803d", "bad": "#b91c1c"}
DARK = {"bg": "#0f172a", "card": "#1e293b", "text": "#f8fafc", "muted": "#cbd5e1", "border": "#475569", "good": "#86efac", "bad": "#fca5a5"}
INSTITUTIONS = {"BYU": "BYU", "University of Utah": "U", "Utah State": "USU", "SUU": "SUU", "Weber": "Weber"}


def preferences_path() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home())) / "BeamDesigner"
    return root / "preferences.json"


class BeamDesigner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Beam Designer | Construction Management")
        self.geometry("1360x860")
        self.minsize(1040, 660)
        self.preferences = self._load_preferences()
        self.dark_mode = self.preferences.get("theme") == "dark"
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configuration_var = tk.StringVar(value="Simply supported")
        self.span_var = tk.StringVar(value="20")
        self.material_var = tk.StringVar(value="Steel")
        self.section_var = tk.StringVar(value="W12x26")
        self.institution_var = tk.StringVar(value=self.preferences.get("institution", "BYU"))
        self.point_rows: list[dict] = []
        self.uniform_rows: list[dict] = []
        self.result = None
        self._pending_update: str | None = None
        self._build()
        self._add_uniform_row("1", "0", "20")
        for variable in (self.configuration_var, self.span_var, self.material_var, self.section_var):
            variable.trace_add("write", self._input_changed)
        self.material_var.trace_add("write", self._material_changed)
        self.institution_var.trace_add("write", self._institution_changed)
        self._apply_theme()
        self._schedule_update()

    def _load_preferences(self) -> dict:
        try:
            with preferences_path().open(encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError, TypeError):
            return {}

    def _save_preferences(self):
        try:
            path = preferences_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.preferences), encoding="utf-8")
        except OSError:
            pass

    def _build(self):
        self._build_menu()
        self.header = ttk.Frame(self, padding=(20, 14))
        self.header.pack(fill="x")
        self.brand_mark = ttk.Label(self.header, style="Header.TLabel", font=("Arial", 24, "bold"))
        self.brand_mark.pack(side="left")
        brand_text = ttk.Frame(self.header, style="Header.TFrame")
        brand_text.pack(side="left", padx=14)
        ttk.Label(brand_text, text="Beam Designer", style="Header.TLabel", font=("Arial", 17, "bold")).pack(anchor="w")
        ttk.Label(brand_text, text="Construction Management", style="Header.TLabel").pack(anchor="w")
        controls = ttk.Frame(self.header, style="Header.TFrame")
        controls.pack(side="right")
        ttk.Label(controls, text="Institution", style="Header.TLabel").grid(row=0, column=0, padx=(0, 5))
        self.institution_box = ttk.Combobox(controls, textvariable=self.institution_var, values=list(INSTITUTIONS), width=16, state="readonly")
        self.institution_box.grid(row=0, column=1, padx=5)
        self.theme_button = ttk.Button(controls, command=self._toggle_theme, width=4)
        self.theme_button.grid(row=0, column=2, padx=(10, 0))

        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        left_shell = ttk.Frame(main, width=370)
        right = ttk.Frame(main)
        main.add(left_shell, weight=1)
        main.add(right, weight=4)
        self._build_scroll_panel(left_shell)
        self._build_inputs(self.input_panel)
        self._build_results(right)

    def _build_menu(self):
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Save", command=self._save_design, accelerator="Ctrl+S")
        file_menu.add_command(label="Open", command=self._open_design, accelerator="Ctrl+O")
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.configure(menu=menu_bar)
        self.bind_all("<Control-s>", lambda _event: self._save_design())
        self.bind_all("<Control-o>", lambda _event: self._open_design())

    def _build_scroll_panel(self, parent):
        self.scroll_canvas = tk.Canvas(parent, highlightthickness=0, width=370)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.scroll_canvas.yview)
        self.input_panel = ttk.Frame(self.scroll_canvas, padding=12)
        self.input_panel.bind("<Configure>", lambda _event: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
        self.scroll_canvas.create_window((0, 0), window=self.input_panel, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_inputs(self, panel):
        ttk.Label(panel, text="Beam inputs", style="Section.TLabel", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 8))
        basics = self._card(panel)
        self._field(basics, "Configuration", self.configuration_var, ["Simply supported", "Cantilever"])
        self._field(basics, "Span (ft)", self.span_var)
        self._field(basics, "Material", self.material_var, ["Steel", "Lumber"])
        self._field(basics, "Section", self.section_var, list(MATERIALS["Steel"]["sections"]))
        self.section_summary = ttk.Label(basics, justify="left", wraplength=310)
        self.section_summary.pack(anchor="w", pady=(6, 0))

        self.point_card = self._card(panel, "Point loads")
        self.point_rows_frame = ttk.Frame(self.point_card)
        self.point_rows_frame.pack(fill="x")
        ttk.Button(self.point_card, text="+ Add point load", command=self._add_point_row).pack(anchor="w", pady=(8, 0))
        self.uniform_card = self._card(panel, "Uniform loads")
        self.uniform_rows_frame = ttk.Frame(self.uniform_card)
        self.uniform_rows_frame.pack(fill="x")
        ttk.Button(self.uniform_card, text="+ Add uniform load", command=self._add_uniform_row).pack(anchor="w", pady=(8, 0))
        self.validation_label = ttk.Label(panel, text="", justify="left", wraplength=330, style="Error.TLabel")
        self.validation_label.pack(fill="x", pady=12)

    def _card(self, parent, title: str | None = None):
        card = ttk.Frame(parent, style="Card.TFrame", padding=10)
        card.pack(fill="x", pady=(0, 10))
        if title:
            ttk.Label(card, text=title, style="CardTitle.TLabel", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 7))
        return card

    def _field(self, parent, label, variable, choices=None):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(fill="x", pady=3)
        ttk.Label(frame, text=label, width=15, style="Card.TLabel").pack(side="left")
        if choices:
            widget = ttk.Combobox(frame, textvariable=variable, values=choices, state="readonly", width=19)
        else:
            widget = ttk.Entry(frame, textvariable=variable, width=22)
        widget.pack(side="right", fill="x", expand=True)
        return widget

    def _build_results(self, parent):
        summary = ttk.Frame(parent, style="Card.TFrame", padding=12)
        summary.pack(fill="x", pady=(0, 10))
        ttk.Label(summary, text="Analysis summary", style="CardTitle.TLabel", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        self.result_labels = {}
        for index, key in enumerate(("Reactions", "Vmax", "Mmax", "ymax", "Bending stress", "Deflection limit")):
            row, column = divmod(index, 3)
            cell = ttk.Frame(summary, style="Card.TFrame")
            cell.grid(row=row + 1, column=column, sticky="ew", padx=8, pady=7)
            ttk.Label(cell, text=key, style="Muted.TLabel").pack(anchor="w")
            label = ttk.Label(cell, text="—", style="Value.TLabel", font=("Arial", 11, "bold"))
            label.pack(anchor="w")
            self.result_labels[key] = label
        for column in range(3):
            summary.columnconfigure(column, weight=1)
        self.bending_badge = ttk.Label(summary, text="Bending —", style="NeutralBadge.TLabel", padding=(8, 4))
        self.deflection_badge = ttk.Label(summary, text="Deflection —", style="NeutralBadge.TLabel", padding=(8, 4))
        self.bending_badge.grid(row=3, column=0, padx=8, pady=(4, 0), sticky="w")
        self.deflection_badge.grid(row=3, column=1, padx=8, pady=(4, 0), sticky="w")
        self.export_button = ttk.Button(summary, text="Export results CSV", command=self._export_results)
        self.export_button.grid(row=3, column=2, padx=8, pady=(4, 0), sticky="e")
        self.pdf_button = ttk.Button(summary, text="Export calculation sheet PDF", command=self._export_calculation_sheet)
        self.pdf_button.grid(row=4, column=0, columnspan=3, padx=8, pady=(8, 0), sticky="ew")
        self.figure = make_figure()
        self.figure_canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.figure_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _add_point_row(self, magnitude="", location="", direction="Down"):
        row = {"magnitude": tk.StringVar(value=magnitude), "location": tk.StringVar(value=location), "direction": tk.StringVar(value=direction)}
        self.point_rows.append(row)
        for value in row.values(): value.trace_add("write", self._input_changed)
        self._render_load_rows()

    def _add_uniform_row(self, magnitude="", start="", end=""):
        row = {"magnitude": tk.StringVar(value=magnitude), "start": tk.StringVar(value=start), "end": tk.StringVar(value=end)}
        self.uniform_rows.append(row)
        for value in row.values(): value.trace_add("write", self._input_changed)
        self._render_load_rows()

    def _render_load_rows(self):
        for frame in (self.point_rows_frame, self.uniform_rows_frame):
            for child in frame.winfo_children(): child.destroy()
        for index, row in enumerate(self.point_rows):
            frame = ttk.Frame(self.point_rows_frame, style="Card.TFrame")
            frame.pack(fill="x", pady=3)
            ttk.Entry(frame, textvariable=row["magnitude"], width=7).grid(row=0, column=0, padx=1)
            ttk.Label(frame, text="kip", style="Card.TLabel").grid(row=0, column=1)
            ttk.Entry(frame, textvariable=row["location"], width=7).grid(row=0, column=2, padx=(7, 1))
            ttk.Label(frame, text="ft", style="Card.TLabel").grid(row=0, column=3)
            ttk.Combobox(frame, textvariable=row["direction"], values=["Down", "Up"], state="readonly", width=6).grid(row=0, column=4, padx=5)
            ttk.Button(frame, text="×", width=3, command=lambda i=index: self._remove_row(self.point_rows, i)).grid(row=0, column=5)
        for index, row in enumerate(self.uniform_rows):
            frame = ttk.Frame(self.uniform_rows_frame, style="Card.TFrame")
            frame.pack(fill="x", pady=3)
            ttk.Entry(frame, textvariable=row["magnitude"], width=7).grid(row=0, column=0, padx=1)
            ttk.Label(frame, text="k/ft", style="Card.TLabel").grid(row=0, column=1)
            ttk.Entry(frame, textvariable=row["start"], width=6).grid(row=0, column=2, padx=(6, 1))
            ttk.Label(frame, text="to", style="Card.TLabel").grid(row=0, column=3)
            ttk.Entry(frame, textvariable=row["end"], width=6).grid(row=0, column=4, padx=1)
            ttk.Button(frame, text="×", width=3, command=lambda i=index: self._remove_row(self.uniform_rows, i)).grid(row=0, column=5, padx=(5, 0))

    def _remove_row(self, rows, index):
        rows.pop(index)
        self._render_load_rows()
        self._schedule_update()

    def _save_design(self):
        try:
            data, _properties = self._collect_input()
            errors = validate_input(data)
            if errors:
                raise ValueError("\n".join(errors))
            design = make_design(self.configuration_var.get(), float(self.span_var.get()),
                                 self.material_var.get(), self.section_var.get(),
                                 list(data.point_loads), list(data.uniform_loads))
        except (ValueError, KeyError) as error:
            messagebox.showerror("Cannot save design", f"Fix the current inputs before saving.\n\n{error}", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Save beam design", defaultextension=".beam.json",
                                            filetypes=[("Beam Designer files", "*.beam.json"), ("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            save_design(path, design)
        except OSError as error:
            messagebox.showerror("Cannot save design", str(error), parent=self)
            return
        messagebox.showinfo("Design saved", f"Saved beam design to:\n{path}", parent=self)

    def _open_design(self):
        path = filedialog.askopenfilename(parent=self, title="Open beam design",
                                          filetypes=[("Beam Designer files", "*.beam.json"), ("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            restored = open_design(path)
        except ValueError as error:
            messagebox.showerror("Cannot open design", str(error), parent=self)
            return
        # Mutate the interface only after the complete file has been validated.
        self.configuration_var.set(restored["configuration"])
        self.material_var.set(restored["material"])
        self.section_var.set(restored["section"])
        self.span_var.set(f"{restored['span_ft']:g}")
        self.point_rows.clear()
        self.uniform_rows.clear()
        for load in restored["point_loads"]:
            self._add_point_row(f"{load.magnitude_kip:g}", f"{load.location_ft:g}", load.direction)
        for load in restored["uniform_loads"]:
            self._add_uniform_row(f"{load.magnitude_kip_per_ft:g}", f"{load.start_ft:g}", f"{load.end_ft:g}")
        self._render_load_rows()
        self._schedule_update()

    def _export_results(self):
        try:
            data, _properties = self._collect_input()
            errors = validate_input(data)
            if errors:
                raise ValueError("\n".join(errors))
            current_result = analyze_beam(data)
        except (ValueError, KeyError) as error:
            messagebox.showerror("Cannot export results", f"Fix the current inputs before exporting.\n\n{error}", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Export beam results", defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            export_results_csv(path, current_result)
        except OSError as error:
            messagebox.showerror("Cannot export results", str(error), parent=self)
            return
        messagebox.showinfo("Results exported", f"Saved beam results to:\n{path}", parent=self)

    def _export_calculation_sheet(self):
        try:
            data, properties = self._collect_input()
            errors = validate_input(data)
            if errors:
                raise ValueError("\n".join(errors))
            current_result = analyze_beam(data)
        except (ValueError, KeyError) as error:
            messagebox.showerror("Cannot export calculation sheet", f"Fix the current inputs before exporting.\n\n{error}", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Export calculation sheet", defaultextension=".pdf",
                                            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if not path:
            return
        try:
            export_calculation_sheet(path, data, current_result, self.material_var.get(), self.section_var.get(), properties)
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot export calculation sheet", str(error), parent=self)
            return
        messagebox.showinfo("Calculation sheet exported", f"Saved calculation sheet to:\n{path}", parent=self)

    def _input_changed(self, *_):
        self._schedule_update()

    def _schedule_update(self):
        if self._pending_update:
            self.after_cancel(self._pending_update)
        self._pending_update = self.after(180, self._update_analysis)

    def _material_changed(self, *_):
        sections = list(MATERIALS[self.material_var.get()]["sections"])
        if self.section_var.get() not in sections:
            self.section_var.set("2x12" if self.material_var.get() == "Lumber" else "W12x26")
        self._schedule_update()

    def _institution_changed(self, *_):
        self.preferences["institution"] = self.institution_var.get()
        self._save_preferences()
        self._update_brand()

    def _collect_input(self):
        def number(variable): return float(variable.get())
        points = [PointLoad(number(row["magnitude"]), number(row["location"]), row["direction"].get()) for row in self.point_rows]
        uniforms = [UniformLoad(number(row["magnitude"]), number(row["start"]), number(row["end"])) for row in self.uniform_rows]
        properties = section_properties(self.material_var.get(), self.section_var.get())
        return BeamInput(self.configuration_var.get(), number(self.span_var), points, uniforms,
            properties["E"], properties["ix"], properties["sx"], properties["fb_allow"]), properties

    def _update_analysis(self):
        self._pending_update = None
        try:
            data, properties = self._collect_input()
            errors = validate_input(data)
        except (ValueError, KeyError):
            data, properties, errors = None, None, ["Complete every load and numeric input with a valid number."]
        if errors:
            self.result = None
            self.validation_label.configure(text="\n".join(errors))
            self._show_empty()
            draw_all(self.figure, None, None, self.dark_mode)
        else:
            self.result = analyze_beam(data)
            weight = f"   Weight: {properties['weight']:.1f} lb/ft" if "weight" in properties else ""
            self.section_summary.configure(text=f"Ix: {properties['ix']:.2f} in⁴   Sx: {properties['sx']:.2f} in³\nE: {properties['E']:,.0f} ksi   Fb: {properties['fb_allow']:.3f} ksi{weight}")
            self.validation_label.configure(text="")
            self._show_result(data)
            draw_all(self.figure, data, self.result, self.dark_mode)
        self.figure_canvas.draw_idle()

    def _show_empty(self):
        self.section_summary.configure(text="—")
        for label in self.result_labels.values(): label.configure(text="—")
        self.bending_badge.configure(text="Bending —", style="NeutralBadge.TLabel")
        self.deflection_badge.configure(text="Deflection —", style="NeutralBadge.TLabel")

    def _show_result(self, data):
        result = self.result
        reactions = ", ".join(f"{name} {value:.2f} k" for name, value in result.reactions_kip.items())
        if result.fixed_end_moment_kip_ft is not None:
            reactions += f"; Mfix {result.fixed_end_moment_kip_ft:.2f} kip-ft"
        values = {
            "Reactions": reactions, "Vmax": f"{result.max_shear_kip:.2f} k @ {result.max_shear_location_ft:.2f} ft",
            "Mmax": f"{result.max_moment_kip_ft:.2f} kip-ft @ {result.max_moment_location_ft:.2f} ft",
            "ymax": f"{result.max_deflection_in:.2f} in @ {result.max_deflection_location_ft:.2f} ft",
            "Bending stress": f"{result.bending_stress_ksi:.2f} ksi / {data.allowable_stress_ksi:.2f} ksi",
            "Deflection limit": f"{result.deflection_limit_in:.2f} in (L/360)",
        }
        for key, value in values.items(): self.result_labels[key].configure(text=value)
        bend_pass = result.bending_ratio <= 1
        deflection_pass = result.deflection_ratio <= 1
        self.bending_badge.configure(text=f"Bending {'PASS' if bend_pass else 'FAIL'}  |  {result.bending_ratio:.2f} / 1.00", style="Pass.TLabel" if bend_pass else "Fail.TLabel")
        self.deflection_badge.configure(text=f"Deflection {'PASS' if deflection_pass else 'FAIL'}  |  {result.deflection_ratio:.2f} / 1.00", style="Pass.TLabel" if deflection_pass else "Fail.TLabel")

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.preferences["theme"] = "dark" if self.dark_mode else "light"
        self._save_preferences()
        self._apply_theme()
        self._schedule_update()

    def _update_brand(self):
        self.brand_mark.configure(text=INSTITUTIONS.get(self.institution_var.get(), "BYU"))

    def _apply_theme(self):
        colors = DARK if self.dark_mode else LIGHT
        self.configure(background=colors["bg"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("Card.TFrame", background=colors["card"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["text"])
        self.style.configure("Card.TLabel", background=colors["card"], foreground=colors["text"])
        self.style.configure("CardTitle.TLabel", background=colors["card"], foreground=colors["text"])
        self.style.configure("Header.TLabel", background=NAVY, foreground="white")
        self.style.configure("Section.TLabel", foreground=colors["text"])
        self.style.configure("Muted.TLabel", background=colors["card"], foreground=colors["muted"])
        self.style.configure("Value.TLabel", background=colors["card"], foreground=colors["text"])
        self.style.configure("Error.TLabel", foreground=colors["bad"])
        self.style.configure("Pass.TLabel", background=colors["good"], foreground="#062b14")
        self.style.configure("Fail.TLabel", background=colors["bad"], foreground="#ffffff")
        self.style.configure("NeutralBadge.TLabel", background=colors["border"], foreground=colors["text"])
        self.style.configure("TEntry", fieldbackground=colors["card"], foreground=colors["text"])
        self.style.configure("TCombobox", fieldbackground=colors["card"], foreground=colors["text"])
        self.header.configure(style="Header.TFrame")
        self.style.configure("Header.TFrame", background=NAVY)
        self.scroll_canvas.configure(background=colors["bg"])
        self.theme_button.configure(text="☀" if self.dark_mode else "☾")
        self.theme_button.configure(takefocus=True)
        self.theme_button.bind("<Return>", lambda _event: self._toggle_theme())
        self._update_brand()


if __name__ == "__main__":
    BeamDesigner().mainloop()
