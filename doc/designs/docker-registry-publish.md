# Feature: Docker Registry Publish

## User Story / Requirement
Configure the project so GitHub Actions automatically builds and publishes Docker containers to GitHub Container Registry (`ghcr.io`).

## Design Decisions
- Use `docker/build-push-action@v5` with Buildx for multi-platform support.
- Publish to `ghcr.io/${{ github.repository }}` using `GITHUB_TOKEN` (default secret).
- Trigger on `push` to `main`, tags `v*`, and `pull_request`.
- Permissions: `packages: write`, `contents: read`.
- Update `Dockerfile` to reflect actual project (Python 3.11 + sqlite3 + app code).

## Compatibility
- Matches existing `AGENTS.md` workflow (design → plan → tests → implement → CI validate).
- Uses existing `.github/workflows/` structure.
- No breaking changes to `docker-compose.yml`.
