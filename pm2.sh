#!/bin/bash
set -e

poetry env use ./.venv/bin/python
poetry install
poetry run streamlit run src/app.py