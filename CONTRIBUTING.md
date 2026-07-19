# Contributing to Khushi AI

Thank you for your interest in contributing to Khushi AI! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new skills or plugins
- Writing or improving documentation

---

## 📜 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand the expectations we have for our community members.

---

## 🛠️ Getting Started with Development

To start contributing, follow these steps to set up your local development environment:

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/khushi-ai.git
   cd khushi-ai
   ```
3. **Set up the virtual environment** and activate it:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. **Install all dependencies** (including test packages):
   ```powershell
   pip install -r requirements.txt
   ```
5. **Run the existing test suite** to verify your setup:
   ```powershell
   pytest
   ```

---

## 🌿 Branching Strategy

We use a standard Git branch workflow:

- `main` represents the stable production-ready state of the system.
- Feature branches should be created off `main` and named descriptively:
  - For features: `feature/your-feature-name`
  - For bug fixes: `bugfix/your-bug-name`
  - For documentation: `docs/your-doc-name`
- Make small, atomic commits with clear messages.

---

## 🧪 Testing

We take test coverage seriously. If you are adding a new feature or fixing a bug, please write tests for it!

- All tests reside in the `tests/` directory.
- We use **PyTest** for testing.
- Run the full test suite before committing:
  ```powershell
  pytest
  ```
- Run a specific test file:
  ```powershell
  pytest tests/test_skills.py
  ```

---

## 📝 Coding Standards

To maintain a consistent codebase:

1. **PEP 8**: Follow standard Python PEP 8 style guidelines.
2. **Type Hinting**: Use type hints in function declarations where possible.
3. **Docstrings**: Provide standard docstrings for modules, classes, and public methods.
4. **Clean Code**: Keep functions small and focused on a single responsibility.
5. **Linting**: Run a linter like `flake8` or `black` to format code if needed.

---

## 🚀 Submitting a Pull Request

When you are ready to submit your changes:

1. Push your branch to your GitHub fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request against the `main` branch.
3. Fill out the [Pull Request Template](.github/pull_request_template.md).
4. Ensure all tests pass.
5. A maintainer will review your Pull Request, provide feedback, and merge it once approved.
