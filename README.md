# NASA PDS DOI Service

The PDS DOI Service provides tools for PDS operators to mint DOIs.

## Prerequisites

- Python 3.7 or above
- a login to OSTI server

## User Documentation 

    https://nasa-pds.github.io/pds-doi-service/ 

## Developers

Get the code and work on a branch

    git clone ...
    git checkout -b "#<issue number>"
    

Install virtual env

    pip install virtualenv
    python -m venv venv
    source venv/bin/activate
    

Deploy dependencies:

    pip install -r requirements.txt
    pip install -r requirements_dev.txt
    
or
    
    pip install -e .
    

Update your local configuration to access the OSTI test server

Create a file in the base directory of the project named `pds_doi_service.ini`,
the following may be used as a template

    [OSTI]
    user = <ask pds-operator@jpl.nasa.gov>
    password = <ask pds-operator@jpl.nasa.gov>
    release_input_schematron = config/IAD3_scheematron.sch
    input_xsd = config/iad_schema.xsd
    
    [PDS4_DICTIONARY]
    url = https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON
    pds_node_identifier = 0001_NASA_PDS_1.pds.Node.pds.name
    
    [LANDING_PAGES]
    # template url, arguments are
    # 1) product_class suffix, after _
    # 2) lid
    # 3) vid
    url = https://pds.nasa.gov/ds-view/pds/view{}.jsp?identifier={}&version={}
    
    [OTHER]
    doi_publisher = NASA Planetary Data System
    global_keyword_values = PDS; PDS4;
    pds_uri = http://pds.nasa.gov/pds4/pds/v1
    transaction_dir = ./transaction_history
    db_file = doi.db
    db_table = doi
    api_host = 0.0.0.0
    api_port = 8080
    emailer_local_host = localhost
    emailer_port       = 25
    emailer_sender     = pdsen-doi-test@jpl.nasa.gov
    emailer_receivers  = pdsen-doi-test@jpl.nasa.gov
    draft_validate_against_xsd_flag = True
    release_validate_against_xsd_flag = True
    reserve_validate_against_xsd_flag = True
    pds_registration_doi_token = 10.17189
    logging_level=DEBUG

    
## Launch API server

    $ pip install pds-doi-service
    $ pds-doi-api
    
The started service documentation is available on http://localhost:8080/PDS_APIs/pds_doi_api/0.1/ui/

## Running with Docker

To run the server on a Docker container, please execute the following from the root directory:

```bash
# building the image
docker build -t pds-doi-service .

# starting up a container
docker run -p 8080:8080 pds-doi-service
```

However, note that when launching the container via `docker run`, all configuration values are
derived from the default INI file bundled with the repo. To override the configuration, it
is recommended to launch the service via docker-compose:

```bash
docker-compose up
```

This will launch the DOI Service container using the top-level `docker-compose.yml` file, which
specifies that environment variables be imported from `doi_service.env`. Modify `doi_service.env`
to define any configuration values to override when the service is launched.

## Test 

### Unit tests (for developers) :

    python setup.py test

### Behavioral testing (for Integration & Testing)

Then you can run the behavioral tests:

    behave

Note this will download reference test data. If they need to be updated you have to first remove your local copy of the reference data (`test/aaDOI_production_submitted_labels`)

You can also run them for a nicer reporting:

    behave -f allure_behave.formatter:AllureFormatter -o ./allure ./features 
    allure service allure
    
#### To report to testrail

Test reports can be pushed to testrail: https://cae-testrail.jpl.nasa.gov/testrail/

Project: Planetary Data System (PDS)
Test suite: pds-doi-service

Set you environment:

    export TESTRAIL_USER=<your email in testrail>
    export TESTRAIL_KEY=<your API key in tesrail>
    
Run the tests:

    behave
    
See the results in https://cae-testrail.jpl.nasa.gov/testrail/index.php?/projects/overview/168
    
## Documentation management

### Design :

See in this repository:

https://github.com/NASA-PDS/pds-doi-service/tree/master/docs

### User documentation

Managed with sphinx

    brew install sphinx-doc
    pip install -r requirements_dev.txt
    cd docs
    sphinx-build -b html source build -a 

## Build & Release

The build and release process is managed in github actions.
