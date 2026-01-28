# Contributing to TRIGRS-PyWrap

Thank you for your interest in contributing to TRIGRS-PyWrap! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you are expected to:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Accept responsibility and learn from mistakes

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs. actual behavior
- Your environment (OS, Python version, dependencies)
- Any relevant error messages or logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:
- A clear description of the proposed feature
- Why this enhancement would be useful
- Possible implementation approach (if you have one)
- Examples of how the feature would be used

### Pull Requests

We actively welcome pull requests:

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Test your changes** thoroughly
4. **Update documentation** if you've changed APIs or added features
5. **Submit a pull request** with a clear description of your changes

#### Pull Request Process

1. Ensure all tests pass and code follows style guidelines
2. Update the README.md with details of interface changes if applicable
3. Provide a clear description of the problem and solution
4. Reference any related issues in your PR description

## Development Setup

### Environment Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/trigrs-pywrap.git
cd trigrs-pywrap

# Create virtual environment
python3 -m venv .trigrsenv
source .trigrsenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if applicable)
pip install pytest black flake8 mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_geohazards.py

# Run with coverage
pytest --cov=geohazards --cov-report=html
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Keep functions focused and modular
- Maximum line length: 88 characters (Black default)

### Code Formatting

Use Black for automatic formatting:
```bash
black geohazards.py
```

### Type Hints

Add type hints to function signatures:
```python
def calculate_slope(dem: xr.DataArray, unit: str = "deg") -> xr.DataArray:
    """Calculate slope from DEM."""
    pass
```

### Documentation

#### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed, explaining the function's purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input is provided
        
    Example:
        >>> result = example_function("test", 42)
        >>> print(result)
        True
    """
    pass
```

#### Comments

- Write self-documenting code when possible
- Add comments for complex logic or non-obvious decisions
- Keep comments up-to-date with code changes

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

## Project Structure

When adding new features, follow the existing structure:

```
trigrs-pywrap/
├── geohazards.py      # Core functionality
├── Trigrs.py          # Example/demonstration scripts
├── tests/             # Unit tests (create if needed)
├── docs/              # Additional documentation
└── examples/          # Usage examples
```

## Commit Messages

Write clear, concise commit messages:

```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
- Reference issues: "Fixes #123" or "Related to #456"
```

## Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Ensure existing tests still pass
- Aim for high code coverage (>80%)
- Test edge cases and error conditions

### Test Structure

```python
import pytest
from geohazards import TRIGRS

def test_slope_calculation():
    """Test slope calculation from DEM."""
    # Arrange
    dem = create_test_dem()
    
    # Act
    slope = calculate_slope(dem)
    
    # Assert
    assert slope.min() >= 0
    assert slope.max() <= 90
```

## Documentation

### Updating README

When adding features, update the README with:
- Usage examples
- New dependencies
- Configuration options
- Breaking changes

### Adding Examples

Provide working examples for new features:
- Include sample data or data generation code
- Show complete, runnable examples
- Explain the purpose and expected output

## Review Process

### What We Look For

- **Correctness**: Does the code work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is it well-documented?
- **Style**: Does it follow project conventions?
- **Simplicity**: Is it the simplest solution?

### Timeline

- Initial review within 1 week
- Follow-up responses within 3-5 days
- We appreciate your patience!

## Getting Help

- Open an issue for questions
- Tag issues with appropriate labels
- Be patient and respectful when awaiting responses

## Areas for Contribution

We especially welcome contributions in:

- **Cross-platform support**: Testing and fixes for Mac/Linux
- **Documentation**: Examples, tutorials, API documentation
- **Testing**: Unit tests, integration tests, test data
- **Performance**: Optimization of computational routines
- **Features**: New analysis capabilities, output formats
- **Bug fixes**: Addressing known issues

## Recognition

Contributors will be:
- Listed in the project contributors
- Mentioned in release notes for significant contributions
- Appreciated for their effort and time!

## Questions?

Don't hesitate to ask! Open an issue with the "question" label, and we'll be happy to help.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to TRIGRS-PyWrap! 🎉
