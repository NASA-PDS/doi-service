import sys
import os
import requests
import logging
from requests.auth import HTTPBasicAuth
import time

from pds_doi_core.util.config_parser import DOIConfigUtil

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = DOIConfigUtil().get_config()
osti_url = parser.get("OSTI", "url")
osti_user = parser.get("OSTI", "user")
osti_password = parser.get("OSTI", "password")

# curl -u username:password https://www.osti.gov/iad2test/api/records -X POST -H "Content-Type: application/xml" -H "Accept: application/xml" --data @osti_doi.xml
# DON'T LOG THE CONNECTION PARAMETERS FOR SECURITY REASON
logger.debug(f"connection with codes {osti_user}:{osti_password}")
auth = HTTPBasicAuth(osti_user, osti_password)
headers = {'Accept': 'application/xml',
           'Content-Type': 'application/xml',
           'Connection': 'close'}

test_doi_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "data",
                             "osti_doi_broken.xml")

time_start = time.perf_counter()
with open(test_doi_file,'rb') as payload:
    response = requests.post("https://www.osti.gov/iad2test/api/records",
                            auth=auth,
                            data=payload,
                            headers=headers)

logger.info(f"requests post duration {time.perf_counter() - time_start}")

logger.info(f"DOI records submitted with status {response.status_code}")

response = requests.get(osti_url,
                            auth=auth)
records = response.json()

status = [(record['title'], record['status']) for record in records['records']]
print(status)
