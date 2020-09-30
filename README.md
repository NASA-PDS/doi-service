# NASA PDS DOI Service

This tools provides services for PDS operators to mint DOIs.


## Prerequisites

- python 3
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
    

Deploy dependancies:

    pip install -r requirements_dev.txt
    
or
    
    pip intall -e .
    
    
## Launch api server (to be re-worked)

    pds-doi-start-dev
    
    
## Test 

### Unit tests:

    python setup.py test

### Behavioral testing

You first need to get some reference datasets, in the project base directory:

    curl https://pds.nasa.gov/software/test-data/pds-doi-service/aaDOI_production_submitted_labels.zip > aaDOI_production_submitted_labels.zip
    unzip aaDOI_production_submitted_labels.zip

Then you can run the behavioral tests:

    behave

You can also run them for a nicer reporting:

    behave -f allure_behave.formatter:AllureFormatter -o ./allure ./features 
    allure service allure
    
#### To report to testrail

Test report can be pushed to testrail: https://cae-testrail.jpl.nasa.gov/testrail/

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

Managed with sphynx

    brew install sphinx-doc
    pip install -r requirements_dev.txt
    cd docs
    sphinx-build -b html source build -a 


      
## Build & Release

The build and release process is managed in github actions.
    

   

