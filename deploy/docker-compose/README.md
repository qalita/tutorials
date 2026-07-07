## Docker Compose Deployment

### Prerequisites

To deploy locally on your computer, you will need:

- Docker
- Docker Compose
- Internet
- A valid license key [📀 Purchase a license](https://qalita.io) or [contact us to get a trial key](mailto:contact@qalita.io)

**The license key allows you to connect to the Docker registry and pull Docker images, in addition to adding information for the platform.**

1. Sign in to the Qalita client registry:

```bash
docker login registry.qalita.io
```

Use the username and license key provided with your subscription when prompted.

> The images are pinned to a released version (e.g. `2.16.2`). `registry.qalita.io`
> only serves versioned tags — `latest` is not available. Replace the tag with the
> version you were licensed for.

2. Create these two files:

- docker-compose.yaml
- s3_config.json

1. Run Docker Compose:

```bash
docker compose up -d
```
