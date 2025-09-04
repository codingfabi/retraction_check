# retraction_check

[![Tests](https://github.com/codingfabi/retraction_check/workflows/Tests/badge.svg)](https://github.com/codingfabi/retraction_check/actions/workflows/test.yml)
[![Code Quality](https://github.com/codingfabi/retraction_check/workflows/Code%20Quality/badge.svg)](https://github.com/codingfabi/retraction_check/actions/workflows/code-quality.yml)
[![Build](https://github.com/codingfabi/retraction_check/workflows/Build%20and%20Package/badge.svg)](https://github.com/codingfabi/retraction_check/actions/workflows/build.yml)

A Python package to check whether papers in your .bib file or a specific bibtex entry have been listed on [Retraction Watch](https://retractionwatch.com/).

## Features
- Parse .bib files and extract paper information
- Query the Retraction Watch dataset for retracted papers
- Support both exact DOI matching and fuzzy title matching
- Robust error handling for various edge cases

## Installation

```bash
# Install from PyPI (when published)
pip install retraction-check

# Or install from source
git clone https://github.com/codingfabi/retraction_check.git
cd retraction_check
pipenv install

# Install development dependencies
pipenv install --dev
```

## Usage

### Command line
```bash
# Using the installed command
retraction-check yourfile.bib

# Or using the module
python -m retraction_check.check_bib yourfile.bib
```

## Development

### Running tests
```bash
# Run all tests
pipenv run test

# Run tests with coverage
pipenv run test-cov

# Run tests in watch mode
pipenv run test-watch

# Run tests directly with Python
python tests/run_tests.py
```

### Code quality
```bash
# Format code
pipenv run format

# Lint code
pipenv run lint

# Type checking
pipenv run type-check

# Run all checks
pipenv run check-all
```

### Available test commands
- `test` - Run all tests with verbose output
- `test-cov` - Run tests with coverage report (HTML and terminal)
- `test-watch` - Run tests in watch mode with short traceback
- `lint` - Run flake8 linting
- `format` - Format code with black
- `format-check` - Check if code is properly formatted
- `type-check` - Run mypy type checking
- `check-all` - Run all quality checks (format, lint, type-check, test-cov)

## Requirements
- Python 3.8+
- bibtexparser
- requests

## Example: Automated Retraction Check with GitHub Actions

You can automate retraction checks for your bibliography file using GitHub Actions. The following workflow runs the check on demand, on a schedule, or on every commit to a specific branch. If any retractions are found, it will open a GitHub issue listing the findings.

```yaml
name: Retraction Check

on:
  workflow_dispatch:  # Allows manual trigger
  schedule:
    - cron: '0 8 * * 1'  # Runs every Monday at 08:00 UTC
  push:
    paths:
      - yourfile.bib  # Change this to your personal bib file to make sure the workflow runs every time the bibfile changes

jobs:
  retraction_check:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install .

      - name: Run retraction check
        id: retraction
        run: |
          python -m retraction_check.check_bib path/to/your/bibfileyourfile.bib > findings.txt
          grep -v "No retracted papers found." findings.txt > findings_only.txt || true

      - name: Create issue if retractions found
        if: success() && hashFiles('findings_only.txt') != ''
        uses: peter-evans/create-issue-from-file@v5
        with:
          title: "Retraction Watch: Retracted Papers Detected in Bibliography"
          content-filepath: findings_only.txt
          labels: retraction, automated-check
```

- Replace `yourfile.bib` with the path to your bibliography file.
- The workflow will create an issue only if retractions are found.
- You can trigger the workflow manually, on a schedule, or on every commit to the specified branch.
