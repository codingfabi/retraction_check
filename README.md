# retraction_check

A Python package to check whether papers in your .bib file or a specific bibtex entry have been listed on [Retraction Watch](https://retractionwatch.com/).

## Features
- Parse .bib files and extract paper information
- Query the Retraction Watch dataset for retracted papers
- Support both exact DOI matching and fuzzy title matching
- Robust error handling for various edge cases

## Installation

```bash
# Install dependencies
pipenv install

# Install development dependencies
pipenv install --dev
```

## Usage

### Command line
```bash
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
