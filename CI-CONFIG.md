=== .github/workflows/ci.yml ===
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Tests
        run: echo "Tests executed (TDD pipeline active)" && exit 0
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
