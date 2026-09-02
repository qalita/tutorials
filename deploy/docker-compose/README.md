## Docker Compose Deployment

This stack runs the whole platform — backend, frontend, documentation, database,
cache, object storage — plus a **worker**, the component that actually executes
the data-quality packs. Without a worker, the platform accepts analyses but
nothing ever runs them.

### Prerequisites

To deploy locally on your computer, you will need:

- Docker
- Docker Compose
- Internet
- A valid license key [📀 Purchase a license](https://qalita.io) or [contact us to get a trial key](mailto:contact@qalita.io)

**The license key allows you to connect to the Docker registry and pull Docker images, in addition to adding information for the platform.**

### 1. Sign in to the Qalita client registry

```bash
docker login registry.qalita.io
```

Use the username and license key provided with your subscription when prompted.

> The images are pinned to a released version. `registry.qalita.io` only serves
> versioned tags — `latest` is not available. Replace the tags with the versions
> you were licensed for. Platform components and the worker are versioned
> independently: the worker follows the CLI release train, so its tag is
> normally ahead of the platform's.

### 2. Copy the deployment files

Put these next to each other in a directory of your choice:

- `docker-compose.yaml`
- `s3_config.json`
- `.env.example`

### 3. Start the platform

```bash
docker compose up -d
```

This brings up everything **except** the worker. The worker needs an API token,
and that token can only be created once the platform is running — so it is held
back behind a Compose profile rather than crash-looping on first boot.

### 4. Create the worker's API token

Open the frontend (http://localhost:3012 by default) and sign in with the
administrator account declared in `docker-compose.yaml`
(`QALITA_ADMIN_USERNAME` / `QALITA_ADMIN_PASSWORD`).

Create an API token from your user profile. **The user it belongs to must hold at
least the Data Engineer role** — the worker registers itself with that token, and
a token without the role fails the registration with an authorization error.

### 5. Start the worker

```bash
cp .env.example .env
# edit .env and paste the token into QALITA_WORKER_TOKEN
docker compose up -d
```

`.env` also carries `COMPOSE_PROFILES=worker`, so from now on plain
`docker compose up -d` includes the worker. Check that it registered:

```bash
docker compose logs -f worker
```

A healthy start ends with `Worker '<name>' registered with ID <n>`, and the
worker appears online in the platform UI.

### How the worker is wired

**Talking to the backend.** The worker uses `QALITA_WORKER_ENDPOINT` for the REST
API and derives its gRPC target from it — `http://backend:3080` becomes
`backend:50051` over the Compose network, so the gRPC port published on the host
plays no part in this deployment. Set `QALITA_GRPC_ENDPOINT` if you need to
override that guess (a separate host, a TLS-terminating proxy, a different port).

**State.** Worker state — its registration file, its pack cache and its job
workspaces — lives in the `workerdata` volume, mounted on `/home/qalita`. Remove
that volume and the worker simply re-registers and re-downloads its packs on the
next start.

Mount the volume on the home directory, not on `~/.qalita`. The image runs as a
non-root user (uid 10001); Docker seeds a named volume from the image directory
it covers, and only `/home/qalita` exists in the image, already owned by that
user. A volume mounted straight onto `/home/qalita/.qalita` is created empty and
root-owned, and every write the worker attempts then fails with a permission
error.

**Reading local files.** To let the worker use files from the host as a source,
uncomment the `./data:/data:ro` mount in the worker service and drop the files
there.

**Scaling.** One worker runs one job at a time. To process several analyses in
parallel, run several workers — give each one a distinct `QALITA_WORKER_NAME` and
its own state volume.

### Upgrading

Change the tags in `docker-compose.yaml`, then:

```bash
docker compose pull
docker compose up -d
```

Worker upgrades are safe to do on their own: the state volume survives, and the
worker re-registers under the same name.

#### Upgrading from 2.x to 3.x

The 3.0.0 platform brings no database migration: the backend still runs
`alembic upgrade head` at start and finds the schema already at head, so the
data volume needs nothing. What changes is the frontend, which now bootstraps
its session from `GET /api/v3/session`, a route the backend only serves in the
`dual` API mode.

1. Set `QALITA_API_MODE=dual` on the `backend` service (already present in the
   compose file above). Backend 3.0.0 defaults to `dual`, so the line is a
   safety net, not a requirement; `legacy` (v1/v2 only) breaks the frontend.
2. Move `backend` and `frontendprod` to the same 3.x tag **together** - a 3.x
   frontend cannot work against a 2.x backend, and a 2.x frontend loses its
   login flow against a `v3`-only backend.
3. Move the worker(s) to `cli:3.0.1` or later. The 3.0.x CLI still speaks the
   v1/v2 API, the worker state volume stays valid and the worker re-registers
   under its existing id.
4. Leave `doc` on the latest tag of the documentation image: it is versioned
   independently from the platform.
5. `docker compose pull && docker compose up -d`, then check:

   ```bash
   curl -s http://localhost:3080/api/v1/version            # {"version":"3.0.0"}
   curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3080/api/v3/session
   # 401 = route served (dual), 404 = backend still in legacy mode
   docker compose logs backend | grep 'API mode'           # API mode: dual
   docker compose logs worker  | grep registered
   ```

Users are asked to sign in again once: sessions opened on 2.x are not carried
over by the v3 session boundary. Worker API tokens created on 2.x keep working.

Rolling back is the reverse tag change on `backend` and `frontendprod`
together (and the worker if needed), then `docker compose up -d`: no schema
change means the 2.x backend starts on the same data volume.
