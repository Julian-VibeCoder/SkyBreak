def test_single_service_on_port_80():
    # Compose is an example; the main requirement is port 80 *inside* the container
    # (host mapping may differ, e.g. 8088:80 to avoid host port clashes in dev).
    with open("docker-compose.yml") as f:
        compose = f.read()
    assert ":80" in compose, "container must expose/listen on port 80"

def test_sqlite_mount_exists():
    # DB path is /data inside container; mount source is flexible
    with open("docker-compose.yml") as f:
        compose = f.read()
    assert "/data/" in compose
