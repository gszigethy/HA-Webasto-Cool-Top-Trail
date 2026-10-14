# Contributing

## Development checks

Create a Python 3.14.2+ virtual environment and install `requirements-dev.txt`.
Run Ruff lint, Ruff formatting checks, and pytest as shown in the README.
GitHub Actions also runs Home Assistant hassfest and HACS validation.
All HACS checks run, including `brands`: the integration ships its own icon in
`custom_components/webasto_cool_top_trail/brand/`.

Tests use Home Assistant's custom-component test plugin and a real test
instance. Network access is disabled during tests. Hardware claims require
separate live-device validation; passing CI is not evidence of IR compatibility.

## Protocol contributions

Include model and remote identifiers, raw recordings, capture metadata, and
tests showing what changes with each setting. Preserve prototype attribution
and licensing. Describe unconfirmed field meanings as hypotheses.

Keep protocol parsing independent from Home Assistant and bridge networking.
Do not guess climate features or report commanded settings as actual telemetry.
Climate capabilities must have labelled capture evidence and software tests;
physical appliance claims additionally require recorded acceptance tests.

## Releases

Published releases are listed on GitHub; HACS installs them by tag. For a new
release:

1. Update `manifest.json` and `pyproject.toml` to the same version.
2. Add concrete changes and hardware validation limits to `CHANGELOG.md`.
3. Require all CI and validation jobs to pass on the target commit.
4. Publish a GitHub release with a matching `v<version>` tag; mark experimental
   builds as prereleases.

HACS will download the integration directory from the repository. ZIP assets
are not required by the current `hacs.json` configuration.
