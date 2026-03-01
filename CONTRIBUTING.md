# Contributing to AI Lease Parser

Thank you for your interest in contributing. This document covers how to get started.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/ai-lease-parser.git
   cd ai-lease-parser
   ```
3. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Create a feature branch:
   ```
   git checkout -b feature/your-feature-name
   ```

## Running Tests

```
pytest tests/ -v
```

Aim to maintain 80%+ test coverage. Add tests for any new functionality.

## Code Style

- Follow PEP 8 for Python code.
- Use 4 spaces for indentation (no tabs).
- Keep lines under 100 characters.
- Write descriptive docstrings for all public functions and classes.

## Submitting a Pull Request

1. Ensure all tests pass.
2. Add or update tests to cover your changes.
3. Write a clear PR title and description explaining what changed and why.
4. Reference any related issues using `Fixes #123` in the PR description.

## Adding New Lease Fields

To add a new extractable field:

1. Add the field definition to `src/fields.py` in `LEASE_FIELDS`.
2. Add a regex pattern to `PATTERNS` in `src/extractor.py`.
3. Add validation logic to `src/validator.py` if needed.
4. Add tests to the relevant test files.

## Reporting Issues

Open an issue on GitHub with:
- A description of the problem or feature request.
- Steps to reproduce (for bugs).
- Expected vs. actual behavior.
- Sample lease text (anonymized) if relevant.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
