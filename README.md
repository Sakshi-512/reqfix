# 🔧 Reqfix

> Fix your Python dependency conflicts automatically.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/reqfix.svg)](https://pypi.org/project/reqfix/)

---

## The Problem

You clone a Python project, create a virtual environment, run `pip install -r requirements.txt` and get this:

```
ERROR: Cannot install flask==1.0.0 and werkzeug==2.3.0 because these
package versions have conflicting dependencies.
```

Then you spend the next hour manually hunting for compatible versions.
It's tedious, frustrating, and happens to every developer.

---

## The Solution

Reqfix analyzes your `requirements.txt`, talks to PyPI, finds compatible versions for every package, verifies they all work **together**, and installs them.

```bash
reqfix install
```

That's it.

---

## ✨ Features

- 🔍 **Analyze** — Detects conflicts, unpinned packages, and outdated versions
- 🔧 **Fix** — Generates a clean `requirements.fixed.txt` with pinned compatible versions
- 🚀 **Install** — Auto-installs all fixed packages in one command
- 🛡️ **Verify** — Cross-checks ALL packages are mutually compatible before installing anything
- 🎨 **Beautiful output** — Color-coded terminal reports powered by Rich

---

## 📦 Installation

### Option 1 — Via pip (recommended)
```bash
pip install reqfix
```

### Option 2 — From source (for contributors)
```bash
git clone https://github.com/Sakshi-512/reqfix.git
cd reqfix
pip install -e .
```

> Reqfix installs packages into the **Python environment it is run from** (system Python, a virtualenv, or a conda env). Run it from the environment where you want dependencies installed.

---

## 🚀 Usage

### The most common flow
```bash
# You cloned a project and pip install failed?
# Just run:
reqfix install
```

### Analyze — see what's broken (no changes made)
```bash
reqfix analyze
```

```
╭─────────────────────────────────────────╮
│  Reqfix — Python Dependency Doctor      │
╰─────────────────────────────────────────╯

Found 4 packages in requirements.txt

┌─────────────┬────────────┬─────────────┬──────────────────────┬──────────────────────────────────────┐
│ Package     │ Original   │ Status      │ Suggested Fix        │ Reason                               │
├─────────────┼────────────┼─────────────┼──────────────────────┼──────────────────────────────────────┤
│ flask       │ >=2.0.0    │ ✅ Healthy   │ flask==3.1.2         │ Pinned to latest compatible version  │
│ requests    │ ==2.28.1   │ ✅ Healthy   │ requests==2.28.1     │ Pinned to latest compatible version  │
│ numpy       │ none       │ 📌 Unpinned  │ numpy==2.4.2         │ Pinned to latest stable              │
│ pandas      │ >=1.3.0    │ ✅ Healthy   │ pandas==3.0.0        │ Pinned to latest compatible version  │
└─────────────┴────────────┴─────────────┴──────────────────────┴──────────────────────────────────────┘

  💥 Conflicts: 0   📌 Unpinned: 1   ✅ Healthy: 3

✅ All packages verified — no cross-package conflicts.
```

### Fix — generate a clean requirements file
```bash
reqfix fix
```
Writes a `requirements.fixed.txt` with every package pinned to a compatible version. Nothing is installed.

### Install — fix and install in one step
```bash
reqfix install
```
Asks for confirmation, verifies cross-package compatibility, then installs everything.

### Custom file paths
```bash
reqfix analyze --file path/to/requirements.txt
reqfix fix --output my-fixed-requirements.txt
```

---

## 🗺️ Roadmap

This is just the beginning. Here's what's coming:

- [ ] **v0.2** — Parallel PyPI requests (faster analysis)
- [ ] **v0.3** — Support for `pyproject.toml` and `setup.py`
- [ ] **v0.4** — Conflict graph visualization
- [ ] **v1.0** — SaaS web app with team features
- [ ] **v1.x** — VS Code extension with inline conflict highlighting

---

## 🤝 Contributing

Contributions are welcome! This project is actively developed.

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Push and open a Pull Request

Please follow the existing code style — type hints, docstrings, and single-responsibility functions throughout.

---

## 📁 Project Structure

```
reqfix/
├── core/
│   ├── parser.py      # Parses requirements.txt into objects
│   ├── resolver.py    # Fetches versions from PyPI, detects conflicts
│   ├── fixer.py       # Determines best version for each package
│   ├── verifier.py    # Verifies all packages are mutually compatible
│   └── installer.py   # Writes fixed file and runs pip install
├── cli/
│   └── main.py        # Terminal interface (analyze, fix, install)
├── setup.py           # Package configuration
└── requirements.txt   # Reqfix's own dependencies
```

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<p align="center">Built with ❤️ to save developers from dependency hell</p>