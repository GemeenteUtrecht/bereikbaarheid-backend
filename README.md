# Bereikbaarheid Backend
Deze repository bevat de API zoals zichtbaar op https://api.nationaalwegenbestand.nl/ .

Zie de [interactieve API docs pagina](https://api.nationaalwegenbestand.nl/docs) voor een overzicht van de endpoints.

## Mappen & bestanden
Deze repo is als volgt ingedeeld:

* `docs` bevat documentatie over diverse aspecten.
* `src`
  * `app` bevat een Flask applicatie met 1) de API (`src/app/api`) en 2) een status endpoint (`src/app/status`).
  * `config` bevat de verschillende config files
* `Dockerfile` bevat config voor de Docker app server omgeving.
* `Dockerfile_database` bevat config voor de Docker development database.
* `Dockerfile_python_deps`; gebruikt voor onderhoud aan Python dependencies, zie het [maintenance document](./docs/maintenance.md) voor meer info.
* `.flake8`; Flake8 linting config, zie het [Contributing document](./CONTRIBUTING.md) voor meer info.
* `pyproject.toml`; Black formatting config, zie het [Contributing document](./CONTRIBUTING.md) voor meer info.
* `requirements.*` bevat de Python applicatie requirements.

## Getting Started
Om lokaal te kunnen ontwikkelen wordt gebruik gemaakt van Docker Compose. 

- Copy `.env.example` and rename it to `.env`. This `.env` file is used when running the Docker backend container.
- Complete the missing environment variables in `.env`. By default it is configured for the docker compose environment.
- Start the docker containers: `docker compose up --build backend`.
- Download a copy of the database and import it locally

De backend is beschikbaar op `localhost:8000`. De `src` folder wordt gedeeld met de container, dus lokale wijzigingen zijn zichtbaar in je browser na het verversen van de pagina.

From your own machine, e.g. with pgAdmin, you can connect to the database which is exposed on `localhost` and port `25432`. You can find all connection information in the `docker-compose` file.

### Override or add settings to the docker-compose file
You can override or add items to the `docker-compose.yaml` by using an override file:

- Copy `docker-compose.override.yaml.example` and rename it to `docker-compose.override.yaml`.
- Add or override items defined in `docker-compose.yaml`. An example of how to share a local folder with the database container is included.
- Validate your config with `docker compose config`
- Run `docker compose up --build backend`. During this process the aforementioned two `docker-compose` files are merged.

## Contributing
You would like to contribute? Great! All input, feedback and improvements are very welcome. Whether it is reporting a problem, suggesting a change, asking a question, improving the docs or code. Please have a look at the [Contributing document](./CONTRIBUTING.md).

## Maintenance
The dockerfile `Dockerfile_python_deps` is used to generate and upgrade Python dependencies.

From the root folder, use the following commands to:
- generate dependencies: `docker compose up --build generate_deps`
- upgrade dependencies: `docker compose up --build upgrade_deps`
