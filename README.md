# envdiff

> Compare `.env` files across environments and surface missing or mismatched keys.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/yourusername/envdiff.git
cd envdiff
pip install .
```

---

## Usage

Compare two `.env` files directly from the command line:

```bash
envdiff .env.development .env.production
```

**Example output:**

```
Missing in .env.production:
  - DATABASE_URL
  - DEBUG

Mismatched values:
  - API_BASE_URL
      development: http://localhost:3000
      production:  https://api.example.com
```

You can also compare multiple files at once:

```bash
envdiff .env.development .env.staging .env.production
```

### Python API

```python
from envdiff import compare

results = compare(".env.development", ".env.production")
print(results.missing)
print(results.mismatched)
```

---

## Options

| Flag | Description |
|------|-------------|
| `--keys-only` | Only check for missing keys, ignore value differences |
| `--quiet` | Suppress output, exit with non-zero status if differences found |
| `--format json` | Output results as JSON |

---

## License

This project is licensed under the [MIT License](LICENSE).