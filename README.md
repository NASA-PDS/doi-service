# NASA PDS DOI Service

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5764878.svg)](https://doi.org/10.5281/zenodo.5764878)

The Planetary Data System (PDS) Digital Object Identifier (DOI) Service provides tools for PDS operators to mint [DOI](https://www.doi.org/)s.


## Prerequisites

- Python 3.9 or above
- A login to the DOI Service Provider endpoint server (currently DataCite)


## User Documentation

Please visit the documentation at: https://nasa-pds.github.io/doi-service/


## Developers

[JPL Internal Wiki](https://wiki.jpl.nasa.gov/display/PDSEN/DOI+Service)

Get the code and work on a branch:

    git clone ...
    git checkout -b "#<issue number>"

Install a Python virtual environment, say in a `venv` directory:

    python3 -m venv venv
    source venv/bin/activate

Install the package and its dependencies for development into the virtual environment:

    pip install --editable '.[dev]'

If you get an error like

    src/types.h:36:2: error: You need a compatible libgit2 version (1.1.x)

then you're probably using [brew.sh](https://brew.sh)'s Python 3.10. Use their Python 3.9 instead.

Update your local configuration to access the DOI service provider's test server.

Create a file in the base directory of the project named `pds_doi_service.ini`; the following may be used as a template

    [SERVICE]
    # Should be set to DataCite (case-insensitive)
    provider = datacite

    [DATACITE]
    # Select the appropriate URL endpoint for either a test or production deployment
    url = https://api.test.datacite.org/dois
    #url = https://api.datacite.org/dois
    user = <contact [PDS Help Desk](https://pds.nasa.gov/?feedback=true)>
    password = <contact [PDS Help Desk](https://pds.nasa.gov/?feedback=true)>
    doi_prefix = 10.17189
    validate_against_schema = True

    [OSTI]
    # This section is kept for posterity, but should be ignored as OSTI is no longer a supported endpoint
    url = https://www.osti.gov/iad2test/api/records
    #url = https://www.osti.gov/iad2/api/records
    user = <contact [PDS Help Desk](https://pds.nasa.gov/?feedback=true)>
    password = <contact [PDS Help Desk](https://pds.nasa.gov/?feedback=true)>
    doi_prefix = 10.17189
    validate_against_schema = True

    [PDS4_DICTIONARY]
    url = https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON
    pds_node_identifier = 0001_NASA_PDS_1.pds.Node.pds.name

    [API_AUTHENTICATION]
    # Add the issuer of the oauth tokens, for cognito https://cognito-idp.<aws-region>.amazonaws.com/<userpoolID>
    jwt_issuer =
    # Add the entire content of the JSON file at https://cognito-idp.<aws-region>.amazonaws.com/<userpoolID>/.well-known/jwks.json
    json_web_key_set =
    jwt_lifetime_seconds = 3600
    jwt_algorithm = RS256

    [OTHER]
    logging_level = INFO
    doi_publisher = NASA Planetary Data System
    global_keyword_values = PDS,PDS4
    pds_uri = https://pds.nasa.gov/pds4/pds/v1/
    transaction_dir = ./transaction_history
    db_file = doi.db
    db_table = doi
    api_host = 0.0.0.0
    api_port = 8080
    api_valid_referrers =
    emailer_local_host = localhost
    emailer_port       = 25
    emailer_sender     = pdsen-doi-test@jpl.nasa.gov
    emailer_receivers  = pdsen-doi-test@jpl.nasa.gov


## Launch API server

To run the DOI API server, try:

```console
$ pip install pds-doi-service
$ pds-doi-api
```

The started service documentation is available on http://localhost:8080/PDS_APIs/pds_doi_api/0.2/ui/

👉 **Note:** When the `api_valid_referrers` option is set in `pds_doi_service.ini`, this service documentation UI will be unavailable.


## Running with Docker

To run the server on a Docker container, please execute the following from the package directory:

```console
$ # building the image
$ docker image build --tag pds-doi-service .
$ # starting up a container
$ docker container run --publish 8080:8080 pds-doi-service
```

However, note that when launching the container via `docker container run`, all configuration values are derived from the default INI file bundled with the repository. To override the configuration, it is recommended to launch the service via a Docker Composition:

```console
$ # Make a copy of the docker composition environment template:
$ cp doi_service.env.in doi_service.env
$ # Edit the environment file, setting the credentials within:
$ vi doi_service.env
$ # Start the composition; on some systems, `docker compose` is `docker-compose`:
$ docker compose up
```

This will launch the DOI Service container using the top-level `docker-compose.yml` file, which specifies that environment variables be imported from `doi_service.env`. Modify `doi_service.env` (after copying it from `doi_service.env.in`) to define any configuration values to override when the service is launched.

## Test

Testing details are detailed in this section.


### Tox (for developers)

#### N.B. Updates to pip dependencies are not automatically applied to existing tox virtual environments, to keep unit testing fast.  The simplest way to propagate dependency updates is to delete `./.tox` and run tox again.

[tox](https://tox.readthedocs.io/) is installed automatically during `pip install --editable .[dev]`, and provides virtual environments and run configurations for
- unit/functional testing
- linting
- building the rich documentation.

To launch the full set of tests, simply run:

    tox

You can also run individual components:

```console
$ tox -e tests  # Run unit, functional, and integration tests
$ tox -e lint  # Run flake8, mypy, and black code reformatting
$ tox -e docs  # Build the documentation to see if that works
```

It is strongly recommended to add `tox -e lint` to your `pre-commit` [git hook](https://www.atlassian.com/git/tutorials/git-hooks), and `tox -e tests` in a `pre-push` hook, as only linted and test-passing PRs will be merged.

The following linting example is provided for ease of use:

```bash
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep ".py$")

echo "Linting files"
tox -e lint
git add $STAGED_FILES  # add any lint-related changes to the current commit

if [ $? -ne 0 ]
then
    echo "Initial lint detected errors, re-linting to determine whether errors remain"
    tox -e lint
    if [ $? -ne 0 ]
    then
      exit 1
    fi
fi

exit 0
```

You can also run `pytest`, `sphinx-build`, `mypy`, etc., if that's more your speed.


### ~~Behavioral testing (for Integration & Testing)~~

~~Behavioral tests are also pre-installed in the Python virtual environment when you run `pip install --editable .[dev]`. Launch those by running:~~

    behave

~~Note this will download reference test data. If they need to be updated you have to first remove your local copy of the reference data (`test/aaDOI_production_submitted_labels`)~~

~~You can also run them for a nicer reporting:~~

    behave -f allure_behave.formatter:AllureFormatter -o ./allure ./features
    allure service allure

~~👉 **Note:** This assumes you have [Allure Test Reporting](http://allure.qatools.ru/) framework installed.~~


#### Testrail Reporting

Test reports can be pushed to [Testrail](https://cae-testrail.jpl.nasa.gov/testrail/)

Project: Planetary Data System (PDS)
Test suite: pds-doi-service

Set your environment:

    export TESTRAIL_USER=<your email in testrail>
    export TESTRAIL_KEY=<your API key in tesrail>

Run the tests:

    behave

See the results in https://cae-testrail.jpl.nasa.gov/testrail/index.php?/projects/overview/168

👉 **Note:** This assumes you have access to the [Jet Propulsion Laboratory's Testrail installation](https://opencae.jpl.nasa.gov/portal/#/tool-detail/site__18_5_3_83a025f_1554392171681_999533_17603_cover).


## Documentation Management

Documentation about the documentation is described in this section.


### Design

See in this repository:

    https://github.com/NASA-PDS/pds-doi-service/tree/main/docs

or the `docs` directory in the source package.


### User Documentation

User documentation is managed with Sphinx, which is also installed in your Python virtual environment when you run `pip install --editable .[dev]`. You can use `tox` as described above to make the docs, or by hand at any time by running:

    sphinx-build -ab html docs/source docs/build


## Build & Release

The build and release process is managed by [GitHub Actions](https://github.com/features/actions) and the [Roundup](https://github.com/NASA-PDS/roundup-action).
