#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
==========
emailer.py
==========

Utilities for sending email messages.
"""

import smtplib

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.util.emailer')


class Emailer:
    """
    Allows code in the pds-doi-service module to send out an email containing
    status of submitted DOIs.
    """

    def __init__(self):
        self._config = DOIConfigUtil().get_config()
        self.m_localhost = self._config.get('OTHER', 'emailer_local_host')
        self.m_email_port = int(self._config.get('OTHER', 'emailer_port'))

    def sendmail(self, sender, receivers, subject, message_body):
        """
        Sends out an email to receivers using smtplib.sendmail().

        Parameters
        ----------
        sender : str
            Sender's email address.
        receivers : list of str
            List of email recipients.
        subject : str
            Subject line for the email.
        message_body : str
            Email message body contents.

        """
        # Build the output message using all parameters.
        # Note that this format below allows the email recipient to see the
        # subject, sender, recipient(s) clearly
        out_message = (f"From: {sender}\n"
                       f"To: {','.join(receivers)}\n"
                       f"Subject: {subject}\n\n"
                       f"{message_body}")

        smtp = None

        try:
            smtp = smtplib.SMTP(self.m_localhost, self.m_email_port)
            smtp.sendmail(sender, receivers, out_message)
            logger.debug(f"Successfully sent email to receivers: {receivers}")
        except Exception as err:
            logger.error(f"Failed to send email, reason: {err}")
        finally:
            if smtp is not None:
                smtp.quit()

    def send_message(self, message):
        """
        Send an email using smtplib.send_message(), which allows attachments
        show up in the user's email program as a clickable link.

        Parameters
        ----------
        message : email.message.EmailMessage
            A message object with the 'From' and 'To:' and 'Subject' already
            filled in.

        """
        smtp = None

        try:
            smtp = smtplib.SMTP(self.m_localhost, self.m_email_port)
            smtp.send_message(message)
            logger.debug(f"Successfully sent email to {message['To']}")
        except Exception as err:
            logger.error(f"Failed to send email, reason: {err}")
        finally:
            if smtp is not None:
                smtp.quit()
