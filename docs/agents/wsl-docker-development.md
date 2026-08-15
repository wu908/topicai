# PowerShell Development and WSL Docker Validation

> AI-assisted engineering note, checked against the primary references listed
> below on 2026-07-31.

## Decision

TopicAI keeps one canonical source tree at `G:\codex_project\topicAI\mvp`.
PowerShell is the default development environment. WSL is used only to host
Docker Compose tests against the same files at
`/mnt/g/codex_project/topicAI/mvp`.

The normative procedure is `$windows-wsl-docker-validation`; this document
stores only TopicAI-specific paths, commands, and data-retention decisions.

This separates two concerns:

- Fast feedback: targeted tests, linting, type checks, and development commands
  run directly in PowerShell after ordinary source edits.
- Runtime parity: Docker images are rebuilt after environment-affecting changes
  and before a commit/PR or explicit container verification.

## Why

- Docker Compose Watch distinguishes source `sync` from image `rebuild`; its
  examples rebuild dependency manifests rather than every source edit.
- Docker recommends leveraging build cache and avoiding unnecessary packages.
  Routine cache pruning works against incremental build speed.
- Twelve-Factor dev/prod parity requires similar environments, not a complete
  production image rebuild after every file save.
- Continuous Integration favors small changes and fast, repeatable feedback.
- Microsoft documents `/mnt/<drive>` as direct access to Windows files and
  notes that WSL-native storage is faster for Linux-heavy file I/O.

## Project workflow

For ordinary work, stay in PowerShell:

```powershell
Set-Location 'G:\codex_project\topicAI\mvp'
```

When a container test is required, start Docker through WSL:

```powershell
wsl -d Ubuntu -u root -- bash -lc "systemctl start docker && docker info >/dev/null && printf '__DOCKER_READY__\n'"
```

Then run Compose against the shared source tree:

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/g/codex_project/topicAI/mvp && docker compose up --build -d --wait"
```

For ordinary source edits, run the smallest relevant backend or frontend check
in PowerShell. Do not rebuild images merely because a source file was saved.

Run the container gate after dependency manifests, Dockerfiles, startup
commands, runtime configuration, or generated frontend artifacts change, and
before a commit/PR or explicit container verification:

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/g/codex_project/topicAI/mvp && docker compose up --build -d --wait && docker compose ps"
```

The current production Compose setup does not define `develop.watch`. Its
frontend image serves a compiled bundle through Nginx, so Compose Watch should
not be added until a real frontend development command and development Compose
configuration exist.

## Generated files and dependencies

- Source, virtual environments, and normal development dependencies remain on
  Windows unless a container build creates its own isolated dependencies.
- If a future frontend development container is justified, keep
  `node_modules` in a Docker named volume and sync only source files.
- Add a direct runtime dependency only for a demonstrated production caller.
  Prefer the standard library or an existing package, keep development tools
  separate, and update manifest and lock files together.

## Cleanup and shutdown

Inspect usage before cleanup:

```bash
docker system df
```

After a successful replacement build, remove only confirmed obsolete or
dangling images. Do not routinely prune builder cache, because it accelerates
incremental builds.

### Development volume policy

The Compose file currently declares:

| Volume | Mount | Policy |
| --- | --- | --- |
| `topicai_data` | `/app/data` | Persistent local SQLite database and migration state; keep by default. |
| `topicai_logs` | `/app/logs` | Rebuildable logs; remove after the task when the stack is stopped. |

For a fresh-database or migration test, isolate the run with a task-specific
Compose project name:

```bash
docker compose -p topicai-validate-<task> up --build -d --wait
docker compose -p topicai-validate-<task> down
docker volume ls --filter label=com.docker.compose.project=topicai-validate-<task>
# After reviewing the names and confirming they are task-only:
docker volume rm <confirmed-temporary-volume>
```

After the result is recorded, remove only the listed volumes from that
isolated project. Before removing any volume that may contain user-created
data, export or copy the required data first. If a future service adds an
uploads, backups, cache, or vector-store mount, inspect its readers and writers
and assign an explicit retention policy before cleaning it.

Always inspect first:

```bash
docker compose config --volumes
docker system df -v
```

Routine cleanup must not use `docker volume prune`,
`docker system prune --volumes`, or `docker compose down -v`; each can remove
unrelated projects or the persistent development database. Use plain
`docker compose down` for the normal stack, and remove only explicitly named
temporary task volumes.

When containers are no longer needed:

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/g/codex_project/topicAI/mvp && docker compose down"
wsl --shutdown
```

## Primary references

- [Microsoft: Working across Windows and Linux file systems](https://learn.microsoft.com/windows/wsl/filesystems)
- [Microsoft: Basic commands for WSL](https://learn.microsoft.com/windows/wsl/basic-commands)
- [Docker: Use Compose Watch](https://docs.docker.com/compose/how-tos/file-watch/)
- [Docker: Build cache](https://docs.docker.com/build/cache/)
- [Docker: Building best practices](https://docs.docker.com/build/building/best-practices/)
- [The Twelve-Factor App: Dev/prod parity](https://12factor.net/dev-prod-parity)
- [Martin Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html)
- [Python Packaging: install_requires vs requirements files](https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/)
- [npm: npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci)
