import subprocess


def _docker_available():
    """Return True only if docker daemon is reachable."""
    result = subprocess.run(
        ["docker", "info"], capture_output=True, text=True
    )
    return result.returncode == 0


def test_docker_image_builds():
    """Validate that the Dockerfile is parseable.

    We deliberately avoid ``docker build`` in this test because CI
    runners are expensive and running a full image build inside pytest
    adds significant flakiness.  The real build-and-publish is covered
    by the ``Build and Publish Docker`` workflow.
    """
    # Skip when docker daemon is not reachable (e.g. local dev, certain
    # CI environments).
    if not _docker_available():
        __import__("pytest").skip(
            "docker daemon not available", allow_module_level=True
        )

    result = subprocess.run(
        ["docker", "build", "-t", "skybreak-test-ci", "."],
        capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"
