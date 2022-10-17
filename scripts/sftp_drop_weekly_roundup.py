import os.path
from pds_doi_service.core.actions.roundup.sftp import run as run_sftp_drop_weekly_roundup
from pds_doi_service.core.db.doi_database import DOIDataBase

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

if __name__ == '__main__':
    """
    Transfer a JSON file consisting of a summary of all DOIs updated in the previous week (i.e. between the previous Sunday
    and the Monday before that, inclusive) to the ADS SFTP server.

    Should be run in a crontab, preferably on Monday, for example:
    0 0 * * MON . path/to/doi-service/venv/bin/python path/to/doi-service/scripts/sftp_drop_weekly_roundup.py
    """

    logging = get_logger('sftp_drop_weekly_roundup')

    config = DOIConfigUtil.get_config()

    db_filepath = os.path.abspath(config['OTHER']['db_file'])
    db = DOIDataBase(db_filepath)

    sftp_config = config['ADS_SFTP']
    sftp_host = sftp_config['host']
    sftp_port = sftp_config['port']
    sftp_user = sftp_config['user']
    sftp_password = sftp_config['password']

    run_sftp_drop_weekly_roundup(db, sftp_host, sftp_user, sftp_password)

    logging.info('Completed DOI weekly roundup email transmission')
