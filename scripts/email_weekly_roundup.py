import os.path
from pds_doi_service.core.actions.roundup import run as run_weekly_roundup

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

if __name__ == '__main__':
    logging = get_logger('email_weekly_roundup')
    config = DOIConfigUtil.get_config()
    db_filepath = os.path.abspath(config['OTHER']['db_file'])
    sender_email_address = config['OTHER']['emailer_sender']
    receiver_email_address = config['OTHER']['emailer_receivers']

    run_weekly_roundup(db_filepath, sender_email_address, receiver_email_address)

    logging.info('Completed DOI weekly roundup email transmission')
