import json
import logging
import os
import tempfile

import fabric.transfer  # type: ignore
import paramiko  # type: ignore
from fabric import Connection  # type: ignore
from paramiko.sftp import SFTPError  # type: ignore
from pds_doi_service.core.actions.roundup.enumerate import get_previous_week_metadata
from pds_doi_service.core.actions.roundup.output import prepare_doi_record_for_ads_sftp
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.util.config_parser import DOIConfigUtil


class FIPSCompliantAutoAddPolicy(paramiko.MissingHostKeyPolicy):
    """
    FIPS-compliant host key policy that accepts unknown hosts without computing MD5 fingerprints.

    This policy is similar to AutoAddPolicy but avoids calling get_fingerprint() which uses MD5
    and fails in FIPS mode. It's appropriate for internal SFTP servers where host key verification
    is not critical.
    """

    def missing_host_key(self, client, hostname, key):
        """
        Accept the host key without computing fingerprints.

        Args:
            client: SSHClient instance
            hostname: The hostname of the server
            key: The server's host key
        """
        # Add the key without logging the fingerprint (which would use MD5)
        client._host_keys.add(hostname, key.get_name(), key)


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

    # Configure connection with FIPS-compliant host key policy
    # This automatically accepts unknown host keys without computing MD5 fingerprints
    conn = Connection(
        host=sftp_host,
        port=sftp_port,
        user=sftp_user,
        connect_kwargs={
            "password": sftp_password,
            "look_for_keys": False,  # Disable SSH key auth to avoid MD5 fingerprint in FIPS mode
            "allow_agent": False,  # Disable SSH agent to avoid MD5 fingerprint in FIPS mode
        },
    )
    # Set FIPS-compliant host key policy that doesn't use MD5
    conn.client.set_missing_host_key_policy(FIPSCompliantAutoAddPolicy())
    transfer = fabric.transfer.Transfer(connection=conn)

    ensure_target_dir(dest_dir_path, conn)

    with tempfile.NamedTemporaryFile(mode="w") as fp:
        output = metadata.to_json(doi_record_mapper=prepare_doi_record_for_ads_sftp)
        json.dump(output, fp)
        fp.flush()
        temp_file_path = os.path.join(tempfile.gettempdir(), fp.name)
        transfer.put(temp_file_path, dest_path)
