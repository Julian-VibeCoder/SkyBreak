def test_single_service_on_port_80():
    # Compose is an example; the main requirement is port 80 exposed
    with open("docker-compose.yml") as f:
        compose = f.read()
    assert "80:80" in compose or 'ports: ["80:80"]' in compose

def test_sqlite_mount_exists():
    # DB path is /data inside container; mount source is flexible
    with open("docker-compose.yml") as f:
        compose = f.read()
    assert "/data/" in compose
