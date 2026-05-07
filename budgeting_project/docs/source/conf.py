# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'budgeting_project.settings'
django.setup()
project = 'Budgeting_project'
copyright = '2026, Ziad mohamed-Malk abdelrahman-malk mahmoud-Rawan Ashraf'
author = 'Ziad mohamed-Malk abdelrahman-malk mahmoud-Rawan Ashraf'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
]
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
