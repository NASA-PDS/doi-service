# NASA PDS Incubator New Project Template
This repo is a template repo used for creating new NASA PDS Incubator projects.

## Prerequisites

python 3

## Developers

    git clone ...
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    
## Launch server

    export FLASK_APP=DOIWebServer.py
    python -m flask run
    
    
Or (version with flask-restplus):

     FLASK_APP=pds-doi-core/web-api/service.py flask run

## Test 

Unit tests:

    python setup.py test

The library:

    python  DOICoreServices_test.py

The service, in a browser http://127.0.0.1:5000/create_osti_label?target_url=%22https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml%22&contributor=%22Cartography+and+Imaging+Sciences+Discipline%22


## Build

### Development build 

A development build is publish for every push on the "dev" branch

It is available in the release section of gitHub


## Deploy    

Deploy the package and launch the API server (for demo or test purpose):

    pip install  --upgrade --force-reinstall https://github.com/NASA-PDS-Incubator/pds-doi-service/releases/download/0.0.1%2Bdev/pds_doi_core-0.0.1+dev-py3-none-any.whl
    pds-doi-start-dev
    
    

   

