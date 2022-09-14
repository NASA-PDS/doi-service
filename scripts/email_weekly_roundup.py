import os.path
from pds_doi_service.core.actions.roundup import run as run_weekly_roundup
from pds_doi_service.core.db.doi_database import DOIDataBase

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

if __name__ == '__main__':
    """
    Send an email consisting of a summary of all DOIs updated in the previous week (i.e. between the previous Sunday 
    and the Monday before that, inclusive), with a JSON attachment for those DoiRecords.
    
    Should be run in a crontab, preferably on Monday, for example:
    0 0 * * MON . path/to/doi-service/venv/bin/python path/to/doi-service/scripts/email_weekly_roundup.py
    """

    logging = get_logger('email_weekly_roundup')
    config = DOIConfigUtil.get_config()
    db_filepath = os.path.abspath(config['OTHER']['db_file'])
    sender_email_address = config['OTHER']['emailer_sender']
    receiver_email_address = config['OTHER']['emailer_receivers']
    db = DOIDataBase(db_filepath)

    run_weekly_roundup(db, sender_email_address, receiver_email_address)

    logging.info('Completed DOI weekly roundup email transmission')
