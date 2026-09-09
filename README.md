# robot-build-manual

Hardware build and bring-up manual: mechanical, electrical, setup, troubleshooting.

---

## Windows quickstart (copy/paste)

Prerequisites
- Git (in PATH)
- Python 3.8+ (in PATH)
- PowerShell

Clone and switch to the scaffold branch:
    git clone https://github.com/wsu-roboracer/robot-build-manual.git
    cd robot-build-manual
    git checkout site_skeleton

Create and activate a virtual environment (PowerShell):
    python -m venv .venv
    # If activation is blocked by policy, run once:
    # Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .venv\Scripts\Activate.ps1

Install MkDocs and the Material theme:
    python -m pip install --upgrade pip
    pip install mkdocs mkdocs-material

Quick checks:
    mkdocs --version            # prints MkDocs version
    Test-Path mkdocs.yml        # should be True (mkdocs.yml must be at repo root)
    Get-ChildItem docs -Directory

Live preview (hot reload):
    mkdocs serve
    # Open http://127.0.0.1:8000 in your browser

Build static site:
    mkdocs build
    # Output is in ./site/

Commit and push changes:
    git add mkdocs.yml docs README.md
    git commit -m "Update docs site content"
    git push origin site_skeleton

Acceptance test — run from a clean clone:
Start in an empty folder and run the steps above. Expected results:
- `mkdocs --version` prints a version.
- `mkdocs serve` serves the site at http://127.0.0.1:8000 and pages load.
- `mkdocs build` creates `site/index.html`.