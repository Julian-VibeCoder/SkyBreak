"""Guard the CI / Docker workflow and Dockerfile fixes from regression.

These parse the workflow/Dockerfile text only (no runner, no Docker needed).
"""
import pathlib
import re

W = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def _wf(name):
    return (W / name).read_text()


def _dockerfile():
    return (ROOT / "Dockerfile").read_text()


# --- ci.yml ---------------------------------------------------------------
def test_ci_does_not_swallfail():
    c = _wf("ci.yml")
    assert "|| true" not in c, "a trailing '|| true' makes CI unable to fail"


def test_ci_runs_pytest():
    c = _wf("ci.yml")
    assert re.search(r"\bpytest\b", c), "CI must run pytest"
    assert "tests/" in c or "tests" in c


def test_ci_installs_deps_and_builds_frontend():
    c = _wf("ci.yml")
    assert "requirements" in c, "CI must install Python dependencies"
    assert "npm ci" in c or "npm install" in c
    assert "npm run build" in c


# --- docker-publish.yml ---------------------------------------------------
def test_publish_does_not_push_on_pull_request():
    c = _wf("docker-publish.yml")
    assert re.search(r"^\s*pull_request\s*:", c, re.M) is None, (
        "pushing on pull_request fails: GITHUB_TOKEN is read-only on PR events"
    )


def test_publish_cache_is_persisted():
    c = _wf("docker-publish.yml")
    assert "type=inline" not in c, "cache-to inline is not persisted across runs"
    assert "cache-to" in c
    assert "type=registry" in c, "cache must be persisted to a registry ref"


def test_publish_no_dead_cachebust_arg():
    c = _wf("docker-publish.yml")
    assert "CACHEBUST" not in c, "CACHEBUST build-arg is ignored by the Dockerfile"


# --- ghcr-cleanup.yml -----------------------------------------------------
def test_cleanup_login_user_not_empty_on_schedule():
    c = _wf("ghcr-cleanup.yml")
    # The login username must not depend on the event actor, which is empty on
    # 'schedule' events. Target the actual username: assignment.
    m = re.search(r"username:\s*('[^']*'|\$\{\{[^}]*\}\})", c)
    assert m is not None, "no login username found"
    assert "actor" not in m.group(1), "username must not use the (empty) actor on schedule"


def test_cleanup_deletes_per_version():
    c = _wf("ghcr-cleanup.yml")
    assert "versions/" in c, "delete must target a version id (/versions/{id})"
    # Keep a version if ANY of its tags is protected; the keep decision must be
    # made per-version by inspecting the version's whole tag list (jq `select`).
    assert "select(" in c, "keep logic must evaluate all of a version's tags"
    assert re.search(r"v\*|v\[0-9\]", c), "must recognise v* semver tags as protected"


def test_cleanup_fails_on_unexpected_status():
    c = _wf("ghcr-cleanup.yml")
    assert "http_code" in c or "%{http_code}" in c
    assert re.search(r"exit\s+[1-9]", c), "must fail when a delete returns a bad status"


# --- Dockerfile -----------------------------------------------------------
def test_dockerfile_uses_npm_ci():
    assert "npm ci" in _dockerfile(), "use npm ci for reproducible builds"
    assert "npm install" not in _dockerfile()


def test_dockerfile_final_stage_is_slim():
    docker = _dockerfile()
    # The final stage must not pull in Chromium/GTK runtime libraries.
    for lib in ("libgtk", "libnss3", "libasound", "libgbm", "libpango", "libatk"):
        assert lib not in docker, f"unused browser/GTK lib {lib} should be removed"
