# Project Memory - SkyBreak (vacation)
- Stack: React frontend, Flask backend, SQLite DB at /data/skybreak.db
- Docker: socket at /var/run/docker.sock (sudo needed); image skybreak-local
- Design docs: doc/designs/ and doc/plans/ deleted per user; architecture.md updated
- DB init: container handles (not Dockerfile); init_db creates schema + migrates
- Cleanup protocol: rm -rf test containers/volumes; keep production image
