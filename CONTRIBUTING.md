# Contributing to BookNLP

Thank you for your interest in contributing to BookNLP! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.12+
- Docker (for running tests)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/booknlp.git
   cd booknlp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/add-new-endpoint`
- `fix/rate-limit-bug`
- `docs/update-api-reference`

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our code style

3. **Run tests**
   ```bash
   pytest tests/unit -v
   pytest tests/integration/api -v
   ```

4. **Run linters**
   ```bash
   ruff check .
   ruff format .
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat(scope): description of change"
   ```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(api): add new endpoint`
- `fix(docker): resolve build issue`
- `docs(readme): update installation instructions`
- `test(unit): add tests for job queue`
- `refactor(nlp): simplify entity extraction`

### Pull Requests

1. Push your branch to your fork
2. Open a PR against `main`
3. Fill out the PR template
4. Wait for CI to pass
5. Request review

## Code Style

- **Python**: Follow PEP 8, enforced by ruff
- **Type hints**: Required for public functions
- **Docstrings**: Required for public modules, classes, and functions
- **Tests**: Required for new features and bug fixes

## Testing

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (API)
pytest tests/integration/api -v

# All tests with coverage
pytest tests/ -v --cov=booknlp/api --cov-report=term-missing
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names: `test_submit_job_with_valid_input_returns_job_id`
- Follow AAA pattern: Arrange, Act, Assert

## API Development

### Adding a New Endpoint

1. Define the route in `booknlp/api/routes/`
2. Add request/response schemas in `booknlp/api/schemas/`
3. Add tests in `tests/unit/api/` and `tests/integration/api/`
4. Update API documentation in README

### Environment Variables

Document any new environment variables in:
- README.md
- `.env.example` (if applicable)

## Docker

### Building Images

```bash
# CPU version
docker build -t booknlp:cpu .

# GPU version
docker build -f Dockerfile.gpu -t booknlp:gpu .
```

### Testing Docker Images

```bash
docker run -d -p 8000:8000 booknlp:cpu
curl http://localhost:8000/v1/health
```

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/jahales/booknlp/discussions)
- **Bugs**: Open an [Issue](https://github.com/jahales/booknlp/issues)
- **Security**: Email security concerns privately

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
