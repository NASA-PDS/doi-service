import json
import logging
import os
import tempfile

import fabric.transfer  # type: ignore
from fabric import Connection  # type: ignore
from paramiko.sftp import SFTPError  # type: ignore
from pds_doi_service.core.actions.roundup.enumerate import get_previous_week_metadata
from pds_doi_service.core.actions.roundup.output import prepare_doi_record_for_ads_sftp
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.util.config_parser import DOIConfigUtil


def ensure_target_dir(dir_path: str, conn: Connection):
    transfer = fabric.transfer.Transfer(connection=conn)
    sftp = transfer.sftp

    try:
        sftp.mkdir(dir_path)
    except OSError:
        pass

    cwd = sftp.getcwd()
    try:
        sftp.chdir(dir_path)
    except (SFTPError, FileNotFoundError) as err:
        logging.error(f"Failed to chdir to target sftp directory {dir_path}")
        raise err
    finally:
        # The SFTPClient 'chdir' propagates up to the Connection and failure to reset the emulated
        # 'cwd' results in a FileNotFoundError when subsequently attempting to write the pathed file
        sftp.chdir(cwd)


def run(
    database: DOIDataBase,
    sftp_host: str,
    sftp_user: str,
    sftp_password: str,
    sftp_port: int = 22,
    dest_dir_path="doi-weekly-roundup",
):
    """
    Enumerate DOIs updated in the previous week (i.e. between the previous Sunday
    and the Monday before that, inclusive), prepare the metadata as JSON, and write that metadata file to an SFTP server
    .
    """
    config = DOIConfigUtil().get_config()

    metadata = get_previous_week_metadata(database)

    dest_filename = f'roundup-week-ending-{metadata.last_date.strftime("%Y%m%d")}.json'
    dest_path = os.path.join(dest_dir_path, dest_filename)

    conn = Connection(host=sftp_host, port=sftp_port, user=sftp_user, connect_kwargs={"password": sftp_password})
    transfer = fabric.transfer.Transfer(connection=conn)

    ensure_target_dir(dest_dir_path, conn)

    with tempfile.NamedTemporaryFile(mode="w") as fp:
        output = metadata.to_json(doi_record_mapper=prepare_doi_record_for_ads_sftp)
        json.dump(output, fp)
        fp.flush()
        temp_file_path = os.path.join(tempfile.gettempdir(), fp.name)
        transfer.put(temp_file_path, dest_path)
