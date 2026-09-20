def test_single_service_on_port_80():
    with open("docker-compose.yml") as f:
        compose = f.read()
    assert "frontend:" not in compose
    assert "80:80" in compose

def test_sqlite_mount_exists():
    with open("docker-compose.yml") as f:
        compose = f.read()
    assert "/data/skybreak.db" in compose
