# Plan: Docker Registry Publish

1. Design review completed (`doc/designs/docker-registry-publish.md`).
2. Create feature branch (if not already on one): `git checkout -b feature/docker-registry-publish`.
3. Write workflow test/reference (`tests/test_workflow.py` updated if needed).
4. Implement `.github/workflows/docker-publish.yml`.
5. Update `Dockerfile` to build correct image (Python 3.11, install deps, copy app).
6. Update `docker-compose.yml` if needed (context, image tag).
7. Run tests / validate syntax (`python -m pytest` / `actionlint` if available).
8. Commit and push branch; open PR (only with explicit user approval).
