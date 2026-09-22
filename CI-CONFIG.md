=== .github/workflows/ci.yml ===
name: Vacation CI

on:
  push:
    branches: [main, story-13-14-date-price-filter, bugix]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Python dependencies
        run: pip install -r requirements.txt -q
      - name: Install frontend dependencies and build
        run: cd frontend && npm ci && npm run build
      - name: Run pytest
        run: pip install pytest -q && python -m pytest -v
=== .github/branch-protection.md ===
# Branch Protection (Main)

Requirements for merge to `main`:

- Status checks must pass (CI / Tests)
- Pull Request required (no direct push)
- Tests executed for every commit and PR
- All User Stories implemented incrementally with passing tests

Config: GitHub Settings > Branches > main > Protection rules
=== CONFIG SUMMARY ===
- CI triggers: push to main + PR
- Required status checks for merge
- Branch protection doc included
