import time
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

target_url = 'https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON'

# fast method
from urllib.request import urlopen

timer_start = time.time()
logger.info(f"TIMER_START:urlopen {target_url}");
response = urlopen(target_url)
logger.info("TIMER_START:reponse.read()");
web_data = response.read().decode('utf-8');
timer_end = time.time()
timer_elapsed = timer_end - timer_start
logger.info(f"TIMER_END:timer_end {timer_end}")
logger.info(f"TIMER_ELAPSED:timer_elapsed {timer_elapsed}")

# slow method
logger.info("==============================")
import requests

timer_start = time.time()
session = requests.session()
timer_elapsed = time.time() - timer_start;
logger.info(f"TIMER_END:timer_end {timer_elapsed}")
response = session.get(target_url, headers={'Accept-Charset': 'utf-8'})
timer_elapsed = time.time() - timer_start;
logger.info(f"TIMER_END:timer_end {timer_elapsed}")
web_data_json = response.json()
response.encoding = 'utf-8'
web_data_str = response.text
timer_end = time.time()
timer_elapsed = timer_end - timer_start;
logger.info(f"TIMER_END:timer_end {timer_end}")
logger.info(f"TIMER_ELAPSED:timer_elapsed {timer_elapsed}")
