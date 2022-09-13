import configparser
import os
import signal
import subprocess
import tempfile
import time
from email import message_from_bytes
from email.message import Message
from typing import Callable

from pds_doi_service.core.util.config_parser import DOIConfigUtil


def get_local_smtp_patched_config(self):
    """
    Return a modified default config that points to a local test smtp
    server for use with the email test
    """
    parser = configparser.ConfigParser()

    # default configuration
    conf_default = "conf.ini.default"
    conf_default_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir, "util", conf_default)
    )

    parser.read(conf_default_path)
    parser["OTHER"]["emailer_local_host"] = "localhost"
    parser["OTHER"]["emailer_port"] = "1025"

    parser = DOIConfigUtil._resolve_relative_path(parser)

    return parser


def capture_email(f: Callable[[], None], port: int = 1025) -> Message:
    """
    Stand up a transient smtpd server, capture the first message sent through it, and return that message
    :param f: a function which sends an email to the SMTP server
    :param port: the port on which the sending process attempts to connect to the SMTP server
    """
    with tempfile.TemporaryFile() as temp_file:
        # By default, all this server is does is echo email payloads to
        # standard out, so provide a temp file to capture it
        debug_email_proc = subprocess.Popen(
            ["python", "-u", "-m", "smtpd", "-n", "-c", "DebuggingServer", f"localhost:{port}"], stdout=temp_file
        )

        # Give the debug smtp server a chance to start listening
        time.sleep(1)

        try:
            # Run the check action and have it send an email w/ attachment
            f()
            # Read the raw email contents (payload) from the subprocess
            # into a string
            temp_file.seek(0)
            email_contents = temp_file.read()
            message = message_from_bytes(email_contents).get_payload()
        finally:
            # Send the debug smtp server a ctrl+C and wait for it to stop
            os.kill(debug_email_proc.pid, signal.SIGINT)
            debug_email_proc.wait()

        return message
