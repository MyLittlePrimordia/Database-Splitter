#!/usr/bin/env python3
"""
JSON Chunk Splitter (Split Database)
-------------------------------------
Splits a large top-level-array database.json into smaller *_chunk_N.json
files, each capped at an approximate token budget, so the pieces fit
inside an AI context window for auditing.

Reconstructed from the original SplitDatabase.pyc. Token counting in the
original binary is a lightweight heuristic (no tokenizer dependency was
bundled) rather than an exact GPT tokenizer; this reconstruction keeps
that same dependency-free approach: ~4 characters per token, estimated
from each entry's compact JSON representation.

Zero third-party runtime dependencies: tkinter, json, os, sys only.
"""

import sys
import os
import json
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --------------------------------------------------------------------------
# Theme (Slate - default IEM Tool retro dark theme)
# --------------------------------------------------------------------------
BG = "#1a1d29"
PANEL = "#232838"
PANEL_ALT = "#2a3040"
FG = "#e6e8f0"
FG_DIM = "#8890a8"
ACCENT = "#f87171"
ACCENT_DIM = "#7a3a3a"
FONT_UI = ("Consolas", 10)
FONT_MONO = ("Consolas", 10)
FONT_TITLE = ("Consolas", 13, "bold")

DEFAULT_INPUT_NAME = "database.json"
OUTPUT_DIR_NAME = "chunks"
DEFAULT_MAX_TOKENS = 6000


# --------------------------------------------------------------------------
# Cross-platform asset loader / base dir resolution
# --------------------------------------------------------------------------
def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(os.path.abspath(sys.executable)))
    return Path(os.path.dirname(os.path.abspath(__file__)))


def asset_path(*parts) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def set_window_icon(root: tk.Tk) -> None:
    try:
        if sys.platform.startswith("win"):
            ico = asset_path("assets", "icon.ico")
            if ico.is_file():
                root.iconbitmap(default=str(ico))
                return
        png = asset_path("assets", "icon.png")
        if png.is_file():
            img = tk.PhotoImage(file=str(png))
            root.iconphoto(True, img)
            root._icon_ref = img
    except tk.TclError:
        pass


# --------------------------------------------------------------------------
# Core logic (faithful to the original split_json())
# --------------------------------------------------------------------------
def count_tokens(item) -> int:
    """Rough, dependency-free token estimate for one JSON entry (~4 chars
    per token), based on its compact JSON serialization.
    """
    text = json.dumps(item, ensure_ascii=False)
    return max(1, len(text) // 4)


def split_json(input_file: Path, output_dir: Path, max_tokens: int = DEFAULT_MAX_TOKENS, log=print):
    """Splits a top-level JSON array into token-budgeted chunk files.
    Returns (chunk_count, total_entries).
    """
    if not input_file.exists():
        raise FileNotFoundError("JSON file not found.")

    with open(input_file, "r", encoding="utf-8") as f:
        database = json.load(f)

    if not isinstance(database, list):
        raise ValueError("JSON must contain a top-level array []")

    total_entries = len(database)
    log(f"Entries found: {total_entries:,}")

    os.makedirs(output_dir, exist_ok=True)
    filename_only = os.path.splitext(os.path.basename(input_file))[0]

    # Clear any stale chunk files from a previous run for this database name.
    for file in os.listdir(output_dir):
        if file.startswith(f"{filename_only}_chunk_") and file.endswith(".json"):
            os.remove(os.path.join(output_dir, file))

    log("Splitting...")

    number = 1
    current_chunk = []
    current_tokens = 0
    chunks_created = 0
    entries_written = 0

    def flush():
        nonlocal number, current_chunk, current_tokens, chunks_created, entries_written
        if not current_chunk:
            return
        output_name = f"{filename_only}_chunk_{number}.json"
        output_path = os.path.join(output_dir, output_name)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(current_chunk, f, ensure_ascii=False, indent=2)
        log(f"  Created: {output_name}")
        log(f"  Entries: {len(current_chunk)}")
        log(f"  Tokens: ~{current_tokens}")
        chunks_created += 1
        entries_written += len(current_chunk)
        number += 1
        current_chunk = []
        current_tokens = 0

    for index, item in enumerate(database):
        item_tokens = count_tokens(item)
        if current_chunk and current_tokens + item_tokens > max_tokens:
            flush()
        current_chunk.append(item)
        current_tokens += item_tokens
        if index % 200 == 0:
            log(f"  Processing {index + 1}/{total_entries} | Current chunk: ~{current_tokens} tokens")

    flush()

    log("=" * 40)
    log(" COMPLETE")
    log(f"Chunks created: {chunks_created}")
    log(f"Entries written: {entries_written}")
    log(f"Output: {output_dir}")

    return chunks_created, total_entries


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class SplitDatabaseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JSON Chunk Splitter")
        self.configure(bg=BG)
        self.geometry("660x480")
        self.minsize(560, 400)
        set_window_icon(self)
        self._build_style()

        base = get_base_dir()
        self.input_var = tk.StringVar(value=str(base / DEFAULT_INPUT_NAME))
        self.output_var = tk.StringVar(value=str(base / OUTPUT_DIR_NAME))
        self.max_tokens_var = tk.IntVar(value=DEFAULT_MAX_TOKENS)
        self.status_var = tk.StringVar(value="Ready.")

        self._build_ui()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=FONT_UI)
        style.configure("Dim.TLabel", background=BG, foreground=FG_DIM, font=FONT_UI)
        style.configure("Title.TLabel", background=BG, foreground=ACCENT, font=FONT_TITLE)
        style.configure(
            "Accent.TButton",
            background=ACCENT_DIM,
            foreground=FG,
            font=FONT_UI,
            borderwidth=0,
            padding=8,
        )
        style.map("Accent.TButton", background=[("active", ACCENT)])
        style.configure("TButton", background=PANEL_ALT, foreground=FG, font=FONT_UI, padding=6, borderwidth=0)
        style.map("TButton", background=[("active", PANEL)])
        style.configure("TEntry", fieldbackground=PANEL_ALT, foreground=FG, insertcolor=FG, borderwidth=0)
        style.configure("TSpinbox", fieldbackground=PANEL_ALT, foreground=FG, borderwidth=0)

    def _build_ui(self):
        pad = {"padx": 14, "pady": 8}

        header = ttk.Frame(self)
        header.pack(fill="x", **pad)
        ttk.Label(header, text="✂  JSON Chunk Splitter", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Splits database.json into token-budgeted chunks for AI-assisted auditing.",
            style="Dim.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        form = ttk.Frame(self)
        form.pack(fill="x", **pad)

        ttk.Label(form, text="Input", style="TLabel").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.input_var, font=FONT_MONO).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(form, text="Browse...", command=self._browse_input).grid(row=0, column=2)

        ttk.Label(form, text="Output folder", style="TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.output_var, font=FONT_MONO).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        ttk.Button(form, text="Browse...", command=self._browse_output).grid(row=1, column=2)

        ttk.Label(form, text="Max tokens/chunk", style="TLabel").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Spinbox(
            form,
            from_=500,
            to=200000,
            increment=500,
            textvariable=self.max_tokens_var,
            font=FONT_MONO,
            width=10,
        ).grid(row=2, column=1, sticky="w", padx=8)

        form.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", **pad)
        ttk.Button(btn_row, text="Split", style="Accent.TButton", command=self._run).pack(side="left")

        panel = tk.Frame(self, bg=PANEL, highlightthickness=0)
        panel.pack(fill="both", expand=True, padx=14, pady=(4, 8))
        self.log = tk.Text(
            panel,
            bg=PANEL,
            fg=FG,
            insertbackground=FG,
            font=FONT_MONO,
            relief="flat",
            wrap="word",
            padx=10,
            pady=10,
        )
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")

        status = ttk.Label(self, textvariable=self.status_var, style="Dim.TLabel")
        status.pack(fill="x", padx=14, pady=(0, 10))

    def _log(self, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.configure(state="disabled")
        self.log.see("end")

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Select database.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(get_base_dir()),
        )
        if path:
            self.input_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(
            title="Select output folder",
            initialdir=str(get_base_dir()),
        )
        if path:
            self.output_var.set(path)

    def _run(self):
        input_file = Path(self.input_var.get())
        output_dir = Path(self.output_var.get())
        max_tokens = self.max_tokens_var.get()

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        self._log("=" * 40)
        self._log(" JSON CHUNK SPLITTER")
        self._log(f"Input: {input_file}")
        self.status_var.set("Splitting...")

        threading.Thread(
            target=self._run_worker, args=(input_file, output_dir, max_tokens), daemon=True
        ).start()

    def _run_worker(self, input_file, output_dir, max_tokens):
        try:
            chunks, entries = split_json(
                input_file,
                output_dir,
                max_tokens=max_tokens,
                log=lambda m: self.after(0, self._log, m),
            )
            self.after(0, self._on_done, chunks, entries)
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._on_error, str(exc))

    def _on_done(self, chunks, entries):
        self.status_var.set(f"Done: {chunks} chunks, {entries} entries.")

    def _on_error(self, message):
        self._log(f"ERROR: {message}")
        self.status_var.set("Failed.")
        messagebox.showerror("JSON Chunk Splitter", message)


# --------------------------------------------------------------------------
# CLI fallback
# --------------------------------------------------------------------------
def run_cli(argv):
    base_dir = get_base_dir()
    input_file = Path(argv[1]) if len(argv) > 1 else base_dir / DEFAULT_INPUT_NAME
    output_dir = base_dir / OUTPUT_DIR_NAME
    max_tokens = int(argv[2]) if len(argv) > 2 else DEFAULT_MAX_TOKENS

    print("=" * 40)
    print(" JSON CHUNK SPLITTER")
    print(f"Input: {input_file}")
    try:
        split_json(input_file, output_dir, max_tokens=max_tokens)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        input("Press ENTER to close...")
        sys.exit(1)


def main():
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        run_cli(sys.argv)
        return
    app = SplitDatabaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
