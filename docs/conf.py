# -*- coding: utf-8 -*-
#
# Robot Build Manual documentation build configuration file

import os

# -- General configuration ------------------------------------------------

needs_sphinx = '1.3'

extensions = [
    'sphinx.ext.mathjax',
    'sphinx.ext.todo',
    'sphinx_copybutton'
]

templates_path = ['_templates']

source_suffix = '.rst'
source_encoding = 'utf-8-sig'

# The master toctree document
master_doc = 'index'

# General information about the project
project = 'RoboRacer - Robot Build Manual'
copyright = '2025, Weber State University'
author = 'Weber State University'

version = 'latest'
release = 'latest'

language = 'en'

exclude_patterns = ['_build', 'build']

# Pygments (syntax highlighting) style to use
pygments_style = 'sphinx'

# -- Options for HTML output ----------------------------------------------

import sphinx_rtd_theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_theme_options = {
    'logo_only': False,
    'collapse_navigation': True,
    'prev_next_buttons_location': 'bottom',
    'navigation_depth': 3,
}

# Use a modern MathJax build from CDN for HTML output
mathjax_path = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'

mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']],
        'processEscapes': True,
        'processEnvironments': True
    },
    'options': {
        'ignoreHtmlClass': 'tex2jax_ignore',
        'processHtmlClass': 'tex2jax_process'
    }
}

# "Edit on GitHub" link
html_context = {
    "display_github": True,
    "github_user": "wsu-roboracer",
    "github_repo": "robot-build-manual",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

# These folders are copied to the documentation's HTML output
html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
]

html_js_files = [
    'js/custom.js',
]

# Copybutton settings: strip common shell prompts when copying
copybutton_prompt_text = r'>>> |\$ '
copybutton_prompt_is_regexp = True

html_show_copyright = True
html_show_sphinx = True
html_last_updated_fmt = '%b %d, %Y'

htmlhelp_basename = 'RobotBuildManual'

# -- Options for reStructuredText parser ----------------------------------

file_insertion_enabled = False

# -- Options for LaTeX output ---------------------------------------------

latex_documents = [
  (master_doc, 'RobotBuildManual.tex', 'RoboRacer Robot Build Manual',
   'Weber State University', 'manual'),
]

# -- Options for linkcheck builder ----------------------------------------

linkcheck_anchors = False
linkcheck_timeout = 10
