# Contributing to Bhisma

First off, thank you for considering contributing to Bhisma! It's people like you that make Bhisma such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to see if the problem has already been reported. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what behavior you expected**
- **Include code samples and screenshots if possible**
- **Specify your environment** (OS, Python version, Bhisma version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the enhancement**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repository
2. Create a new branch from `main` for your feature or bug fix
3. Make your changes
4. Add or update tests as needed
5. Update documentation as needed
6. Ensure all tests pass
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/bhisma.git
cd bhisma

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bhisma --cov-report=html

# Run specific test file
pytest tests/test_basic.py
```

### Code Style

We follow PEP 8 with a few modifications:

- Line length: 100 characters
- Use double quotes for strings
- Use type hints where possible

```bash
# Format code
black bhisma/ tests/

# Check style
flake8 bhisma/ tests/

# Type checking
mypy bhisma/
```

## Project Structure

```
bhisma/
├── cli/           # Command-line interface
├── tui/           # Terminal UI components
├── brain/         # AI/LLM orchestration
│   ├── providers/ # LLM provider implementations
│   └── agents/    # AI agent implementations
├── core/          # Core framework logic
│   └── autonomous/# Autonomous mode components
├── wifi/          # WiFi attack modules
├── mitm/          # MITM attack modules
├── injection/     # Frame injection modules
├── persistence/   # Post-exploitation modules
├── radio/         # Radio protocol modules
├── intel/         # Intelligence gathering
├── ml/            # Machine learning models
├── stealth/       # Evasion techniques
├── tools/         # External tool management
├── dashboard/     # Web dashboard
└── utils/         # Utility functions
```

## Commit Messages

Use clear and meaningful commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add WPS brute-force attack module

- Implement PIN generation algorithm
- Add timeout and retry logic
- Update documentation

Fixes #123
```

## Documentation

- Update the README.md if you change functionality
- Update docstrings for modified functions
- Add examples for new features
- Update the docs/ directory for significant changes

## Testing Guidelines

- Write tests for new features
- Update tests for modified features
- Aim for high test coverage
- Use pytest for all tests
- Mock external dependencies

## Security

- Never commit API keys or credentials
- Report security vulnerabilities privately
- See [SECURITY.md](SECURITY.md) for details

## Questions?

Feel free to open an issue or start a discussion if you have any questions!

Thank you for contributing! 🔥
