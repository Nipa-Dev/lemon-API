# Using Testcontainers with Podman


### One-time setup
Enable and start the Podman Docker-compatible socket:

```bash
systemctl --user enable --now podman.socket
```
#### Persistent environment variable

Tell Docker-compatible tools where the socket lives by adding this to your shell config:
```bash
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
# alternative, should resolve to same path
export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock
```
#### Rootless Podman (important)

In rootless mode, this is usually required or containers may hang or fail to clean up:
```bash
export TESTCONTAINERS_RYUK_DISABLED=true
```

Example to export them, using fish shell 
```fish
set -Ux DOCKER_HOST unix://$XDG_RUNTIME_DIR/podman/podman.sock
set -Ux TESTCONTAINERS_RYUK_DISABLED true
```
