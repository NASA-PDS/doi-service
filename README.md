# NASA PDS DOI Service
This tools provides services for PDS operators to mint DOIs.

## Prerequisites

python 3

## Developers

    git clone ...
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip intall -e .
    
    
## Launch server

    pds-doi-start-dev
    
    
## Test 

Unit tests:

    python setup.py test

The service, in a browser http://127.0.0.1:5000/create_osti_label?target_url=%22https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml%22&contributor=%22Cartography+and+Imaging+Sciences+Discipline%22


## Build

### Development build 

A development build is publish for every push on the "dev" branch

It is available in the release section of gitHub


## Deploy    

Deploy the package and launch the API server (for demo or test purpose):

    pip install  --upgrade --force-reinstall https://github.com/NASA-PDS-Incubator/pds-doi-service/releases/download/0.0.1%2Bdev/pds_doi_core-0.0.1+dev-py3-none-any.whl
    pds-doi-start-dev
    
    

   

