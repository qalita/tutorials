# AGENTS.md — Qalita Tutorials

Instructions for AI agents working on this repository.

## Project

**Qalita Tutorials** — Collection of tutorials, sample data, and integration guides for the Qalita platform.

- **Organization** : `qalita`
- **Documentation** : https://doc.qalita.io/
- **Content** : Markdown, sample datasets, configuration files

## Tech Stack

| Component | Technologies |
|-----------|-------------|
| **Content** | Markdown, YAML, JSON |
| **Data Formats** | CSV, Parquet, JSON, SQL |
| **Integrations** | dbt, Airflow, Prefect, Great Expectations, Soda |
| **Platforms** | Docker, Kubernetes, cloud providers |
| **Documentation** | Markdown with code examples |

## Dependencies

- Docker (for deployment tutorials)
- dbt, Airflow, or other tools covered in tutorials
- Sample datasets (anonymized)

## Build/Lint/Test Commands

```bash
# Validate Markdown syntax (if mdspell or markdownlint configured)
npx markdownlint **/*.md

# Validate YAML files
yamllint **/*.yaml **/*.yml

# Validate JSON files
jsonlint **/*.json

# Test deployment tutorials (Docker Compose)
cd deploy/docker-compose/ && docker-compose config

# Check links in Markdown (if markdown-link-check configured)
npx markdown-link-check **/*.md
```

## Code Conventions

- Each tutorial is a standalone folder with its own `README.md`
- **Language** : README in English for consistency
- **Data** : Sample data must be anonymized (no real data)
- **Formatting** : Consistent Markdown formatting
- **Links** : Verify links to documentation are valid
- **Code examples** : Test all code examples before committing

## Architecture

```
tutorials/
├── deploy/
│   └── docker-compose/    # Deployment via Docker Compose
├── integrations/
│   ├── data-engineering/  # ELT & orchestration integrations
│   ├── data-quality/      # Data quality framework integrations
│   └── platform/          # Platform integrations (ticketing, alerting, reporting, catalogs)
└── source/                # Source registration guides
```

## Git Workflow

- **Commits** : English, conventional commits (`feat:`, `fix:`, `docs:`)
- **Branches** : `main` (prod), feature branches for development
- **Tags** : Strict semver `X.Y.Z` for releases

## Content Rules

- ❌ Do not commit sensitive or confidential data
- ✅ Verify documentation links are valid
- ✅ Test all code examples and deployment guides
- ✅ Anonymize all sample datasets
- ✅ Keep tutorials up to date with platform changes
