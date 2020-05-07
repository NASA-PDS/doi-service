# NASA PDS DOI Service
This tools provides services for PDS operators to mint DOIs.

## Prerequisites

python 3

## Supported inputs

### PDS4 Label
- Bundle - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml
- Data Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml
- Browse Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml
- Calibration Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml
- Document Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml

### XLS spreadsheets
For reserved dois

### CSV files
CSV is not supported.  It was a one-time deal from Ron.

## Usage 

    pds-doi-cmd --help

    pds-doi-cmd draft -c 'Cartography and Imaging Sciences Discipline' -i 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
    pds-doi-cmd draft -c 'Cartography and Imaging Sciences Discipline' -i input/bundle_in_with_contributors.xml 
    pds-doi-cmd draft -c 'Cartography and Imaging Sciences Discipline' -i 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml'

    pds-doi-cmd reserve -c 'Cartography and Imaging Sciences Discipline' -i input/DOI_Reserved_GEO_200318.xlsx
    pds-doi-cmd reserve -c 'Cartography and Imaging Sciences Discipline' -i input/DOI_Reserved_GEO_200318.csv
    pds-doi-cmd reserve -c 'Cartography and Imaging Sciences Discipline' -i input/OSTI_IAD_submitted_records_Reserved-only_20200304.csv 


## Developers

Get the code and work on a branch

    git clone ...
    git checkout -b "#<issue number>"
    

Install virtual env

    pip install virtualenv
    python -m venv venv
    source venv/bin/activate
    

Deploy dependancies:

    pip install -r requirements.txt
    
or
    
    pip intall -e .

    
## Launch server

    pds-doi-start-dev
    
    
## Test 

Unit tests:

    python setup.py test

Test the service, in a browser.

Test the library:

    python  DOICoreServices_test.py



## Build

### Development build 

A development build is publish for every push on the "dev" branch

It is available in the release section of gitHub

### Release

To be completed


## Deploy    

Deploy the package and launch the API server (for demo or test purpose):

    pip install  --upgrade --force-reinstall https://github.com/NASA-PDS-Incubator/pds-doi-service/releases/download/0.0.1%2Bdev/pds_doi_core-0.0.1+dev-py3-none-any.whl
    pds-doi-start-dev
    
    

   

