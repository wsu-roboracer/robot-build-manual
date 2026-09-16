# robot-build-manual

Hardware build and bring-up manual: mechanical, electrical, setup, troubleshooting.

The site is built with [Sphinx](https://www.sphinx-doc.org/) (reStructuredText, Read the Docs theme) and deployed to GitHub Pages by `.github/workflows/pages.yml` on every push to `main`.

---

## Windows quickstart (copy/paste)

Prerequisites
- Git (in PATH)
- Python 3.11 (in PATH) — the pinned versions in `docs/requirements.txt` match CI
- PowerShell

Clone:
```powershell
git clone https://github.com/wsu-roboracer/robot-build-manual.git
cd robot-build-manual
```

Create and activate a virtual environment (PowerShell):
```powershell
python -m venv .venv
# If activation is blocked by policy, run once:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Install Sphinx and the theme:
```powershell
python -m pip install --upgrade pip
pip install -r docs/requirements.txt
```

Build the site (same command CI runs):
```powershell
sphinx-build -b html docs docs/build/html
```
Open `docs/build/html/index.html` in your browser.

Or, from the `docs` folder:
```powershell
cd docs
.\make.bat html      # output in docs/_build/html
```

## Adding pages

- Pages are `.rst` files under `docs/`, one folder per section (`docs/<section>/index.rst`).
- Add new pages to a `toctree` in `docs/index.rst` (or in the section's `index.rst`) so they appear in the sidebar.
