import sys
import os
import requests
import logging
import configparser
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = configparser.ConfigParser()
candidates = ['conf.ini.default',
              'conf.ini',]
candidates_full_path = [os.path.join(os.getcwd(), "config", f) for f in candidates] # for development deployment
candidates_full_path.extend([os.path.join(sys.prefix, "pds-doi-core", f) for f in candidates]) # for real deployment
logger.info(f"search configuration files in {candidates_full_path}")
found = parser.read(candidates_full_path)
logger.info(f"used configuration following files {found}")

osti_url = parser.get("OSTI", "url")
osti_user = parser.get("OSTI", "user")
osti_password = parser.get("OSTI", "password")

# curl -u username:password https://www.osti.gov/iad2test/api/records -X POST -H "Content-Type: application/xml" -H "Accept: application/xml" --data @osti_doi.xml
# DON'T LOG THE CONNECTION PARAMETERS FOR SECURITY REASON
#logger.debug(f"connection with codes {osti_user}:{osti_password}")
auth = HTTPBasicAuth(osti_user, osti_password)
headers = {'Accept': 'application/xml',
           'Content-Type': 'application/xml'}

test_doi_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "data",
                             "osti_doi_broken.xml")

with open(test_doi_file,'rb') as payload:
    response = requests.post("https://www.osti.gov/iad2test/api/records",
                            auth=auth,
                            data=payload,
                            headers=headers)

logger.info(f"DOI records submitted with status {response.status_code}")

response = requests.get(osti_url,
                            auth=auth)
records = response.json()

status = [(record['title'], record['status']) for record in records['records']]
print(status)
