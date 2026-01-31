[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=ffd343)](https://docs.python.org/3.13/)
[![CI](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions/workflows/ci.yml)
[![Build](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/build.yml?branch=main&style=flat-square&label=Build&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions/workflows/build.yml)
[![Docker](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/docker.yml?branch=main&style=flat-square&label=Docker&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions/workflows/docker.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- omit from toc -->
# Python Cloud Server

A production-ready FastAPI cloud server which uses [python-template-server](https://github.com/javidahmed64592/python-template-server).

<!-- omit from toc -->
## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Managing the Container](#managing-the-container)
- [Links](#links)
- [Documentation](#documentation)
- [License](#license)

## Prerequisites

- Docker and Docker Compose installed

## Quick Start

### Installation

Download the latest release from [GitHub Releases](https://github.com/javidahmed64592/python-cloud-server/releases).

### Configuration

Rename `.env.example` to `.env` and edit it to configure the server.

- `HOST`: Server host address (default: localhost)
- `PORT`: Server port (default: 443)
- `API_TOKEN_HASH`: Leave blank to auto-generate on first run, or provide your own token hash
- `GEMINI_API_KEY`: API key from Google AI Studio

### Managing the Container

```sh
# Start the container
docker compose up -d

# Stop the container
docker compose down

# Update to the latest version
docker compose pull && docker compose up -d

# View the logs
docker compose logs -f python-cloud-server
```

**Note:** You may need to add your user to the Docker group and log out/in for permission changes to take effect:
```sh
sudo usermod -aG docker ${USER}
```

## Links

- Access the web application: https://localhost:443
- Server runs at: https://localhost:443/api
- Swagger UI: https://localhost:443/api/docs
- Redoc: https://localhost:443/api/redoc

## Documentation

- **[API Documentation](./docs/API.md)**: Endpoints, authentication
- **[Software Maintenance Guide](./docs/SMG.md)**: Development setup, configuration
- **[Workflows](./docs/WORKFLOWS.md)**: CI/CD pipeline details

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
