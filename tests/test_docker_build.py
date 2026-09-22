import subprocess

def test_docker_image_builds():
    result = subprocess.run(["docker", "build", "-t", "skybreak-test", "."], capture_output=True, text=True)
    assert result.returncode == 0, f"Build failed: {result.stderr}"
