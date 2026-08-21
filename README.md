# ✂️ JSON Chunk Splitter

A tiny, 100% offline desktop utility that splits a large `database.json`
array into smaller, token-budgeted chunk files — sized to fit inside an
AI context window for auditing. Built for the [IEM Tool](.) ecosystem.

No servers, no tracking, no third-party runtime dependencies.

---

## ✨ Features

- **Token-budgeted chunking** — splits a top-level JSON array into
  `*_chunk_N.json` files, each kept under a configurable token limit
  (default 6,000).
- **Dependency-free token estimate** — no tokenizer library required;
  uses a lightweight `chars / 4` heuristic per entry so the tool stays
  a single-file, zero-dependency script.
- **Stale chunk cleanup** — automatically removes old `*_chunk_*.json`
  files for the same database name before writing new ones.
- **Live progress log** — entries found, per-chunk token counts, and a
  final summary (chunks created, entries written, output folder).
- **Retro Slate theme** to match the rest of the IEM Tool suite.

## 🚀 Quick Start

```bash
python app/main.py
```

Defaults to `database.json` next to wherever the app is running from,
writing chunks into a `chunks/` subfolder. Both the input file, output
folder, and max-tokens-per-chunk are editable from the UI.

Console mode (no GUI):

```bash
python app/main.py --cli path/to/database.json 6000
```

## 🛠️ Building

Requires [PyInstaller](https://pyinstaller.org/) (`pip install pyinstaller`).

**Windows (.exe)**

```bash
pyinstaller --noconfirm --onefile --windowed --name "JSON Chunk Splitter" ^
  --icon app/assets/icon.ico --add-data "app/assets;assets" app/main.py
```

**macOS (.dmg)**

```bash
bash app/build_macos.sh
```

**Linux (.AppImage)**

```bash
bash app/build_linux_appimage.sh
```

All three platforms also build automatically via the included GitHub
Actions workflow (`.github/workflows/build.yml`) on any `v*` tag push.

## 📦 Requirements

- Python 3.9+
- `tkinter` (bundled with most Python installs; on Linux you may need
  `sudo apt install python3-tk`)

No other dependencies — splitting uses only the standard library
(`json`, `os`).
