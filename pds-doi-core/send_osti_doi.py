import os
import requests
import logging
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# curl -u NASA-PDS:Ef0$d@v3Ef0$d@v3 https://www.osti.gov/iad2test/api/records -X POST -H "Content-Type: application/xml" -H "Accept: application/xml" --data @osti_doi.xml
auth = HTTPBasicAuth("NASA-PDS", "Ef0$d@v3-Ef0$d@v3")
headers = {'Accept': 'application/xml',
           'Content-Type': 'application/xml'}

test_doi_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "test",
                             "data",
                             "osti_doi_broken.xml")

with open(test_doi_file,'rb') as payload:
    response = requests.post("https://www.osti.gov/iad2test/api/records",
                            auth=auth,
                            data=payload,
                            headers=headers)

logger.info(f"DOI records submitted with status {response.status_code}")

response = requests.get("https://www.osti.gov/iad2test/api/records",
                            auth=auth)
records = response.json()

status = [(record['title'], record['status']) for record in records['records']]
print(status)
