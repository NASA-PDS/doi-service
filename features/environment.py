import os
import logging
import requests
import shutil
import zipfile
from behave_testrail_reporter import TestrailReporter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def download_file(url):
    local_filename = url.split('/')[-1]
    tmp_dir = 'tests'
    local_filepath = os.path.join(tmp_dir,
                                  local_filename)

    dir_target = local_filepath[:-4]
    if not os.path.exists(dir_target):
        logger.info(f'Downloading reference test datasets {dir_target}')
        with requests.get(url, stream=True) as r:
            with open(local_filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        with zipfile.ZipFile(local_filepath, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

    return local_filepath[:-4]


def before_all(context):

    download_file('https://pds.nasa.gov/software/test-data/pds-doi-service/aaDOI_production_submitted_labels.zip')

    current_branch = 'master' # Change this to get the current build branch of your CI system
    testrail_reporter = TestrailReporter(current_branch)
    context.config.reporters.append(testrail_reporter)


#def after_scenario(context):
#    if hasattr(context, 'random_lid'):
#        del context.random_lid
