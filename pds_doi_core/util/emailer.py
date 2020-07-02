#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

import smtplib

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

# Get the common logger and set the level for this file.
import logging

logger = get_logger('pds_doi_core.util.emailer')

class Emailer:
    # This class Emailer allows code in pds-doi-service module to send out an email for status of submitted DOIs or any other reasons.

    m_doi_config_util = DOIConfigUtil()
    m_localhost  = None
    m_email_port = None

    def __init__(self, arguments=None,db_name=None):
        self._config = self.m_doi_config_util.get_config()
        self.m_localhost  =      self._config.get('OTHER', 'emailer_local_host')
        self.m_email_port =  int(self._config.get('OTHER', 'emailer_port'))

    def sendmail(self, sender, receivers, subject, message_body):
        '''Function send out an email from sender to receivers using SMTP library using sendmail(). '''

        # An example email: 
        # 
        # Subject: DOI Submission Status Report On 2020-07-01T22:47:16.056184
        # From: Qui.T.Chau@jpl.nasa.gov
        # Date: Wed 7/1/2020 3:47 PM
        # To: Chau, Qui T (US 398F);pdsen-doi-test
        # Date: 07/01/2020
        # 3 records.
        # 
        # 
        # #  Id     Title                                  DOI           Initial_Status   Status
        # 1  21940  Laboratory Shocked Feldspars Bundle  10.17189/21940  Pending  Reserved
        # 2  21939  Laboratory Shocked Feldspars Bundle  10.17189/21939  Pending  Reserved
        # 3  21938  Laboratory Shocked Feldspars Bundle  10.17189/21938  Pending  Reserved

        # Build the output message using all parameters.
        # Note that this format below allows the email recipient to see the subject, sender, recipient(s) clearly as in the example email above:

        out_message = "From: " + sender + "\n" + "To: " + ','.join(receivers) + "\n" + "Subject: " + subject + "\n\n" + message_body

        try:
            smtpObj = smtplib.SMTP(self.m_localhost,self.m_email_port)
            smtpObj.sendmail(sender, receivers, out_message)
            logger.debug(f"Successfully sent email to {receivers}")
        except OSError:
            logger.error("OSError:Error: unable to send email")
            logger.debug(f"subject,message_body {subject,message_body}")
            logger.debug(f"{self.m_localhost,self.m_email_port}")
            logger.debug(f"sender,receivers {sender,receivers}")
        except Exception:
            logger.error("Exception:Error: unable to send email")
            logger.debug(f"subject,message_body {subject,message_body}")
            logger.debug(f"{self.m_localhost,self.m_email_port}")
            logger.debug(f"sender,receivers {sender,receivers}")
        return 1

    def send_message(self, message, sender=None, receivers=None):
        '''Function send out an email from sender to receivers using SMTP library using send_message() to allow attachment to be a link. '''

        # An example email: 
        # 
        # Subject: DOI Submission Status Report On 2020-07-01T22:47:16.056184
        # From: Qui.T.Chau@jpl.nasa.gov
        # Date: Wed 7/1/2020 3:47 PM
        # To: Chau, Qui T (US 398F);pdsen-doi-test
        # Date: 07/01/2020
        # 3 records.
        # 
        # 
        # #  Id     Title                                  DOI           Initial_Status   Status
        # 1  21940  Laboratory Shocked Feldspars Bundle  10.17189/21940  Pending  Reserved
        # 2  21939  Laboratory Shocked Feldspars Bundle  10.17189/21939  Pending  Reserved
        # 3  21938  Laboratory Shocked Feldspars Bundle  10.17189/21938  Pending  Reserved
        # 
        # with attachment as a clickable link.
        # 
        # [
        #     {
        #         "status": "Reserved",
        #         "update_date": 1593668833.016585,
        #         "submitter": "Qui.T.Chau@jpl.nasa.gov",
        #         "title": "Laboratory Shocked Feldspars Bundle",
        #         "type": "Collection",
        #         "subtype": "PDS4 Collection",
        #         "node_id": "img",
        #         "lid": "urn:nasa:pds:lab_shocked_feldspars",
        #         "vid": "1.0",
        #         "doi": "10.17189/21940",
        #         "release_date": null,
        #         "transaction_key": "./transaction_history/img/2020-06-15T18:42:45.653317",
        #         "is_latest": 1,
        #         "related_identifier": "urn:nasa:pds:lab_shocked_feldspars::1.0",
        #         "product_type": "Collection",
        #         "product_type_specific": "PDS4 Collection",
        #         "initial_status": "Pending",
        #         "id": "21940",
        #         "record_index": 1
        #     },
        #
        # The value message is already a Message object with the 'From' and 'To:' and 'Subject' already filled in.
        # Using the send_message allows the attachment to show up in the user's email program as a clickable item.

        try:
            smtpObj = smtplib.SMTP(self.m_localhost,self.m_email_port)
            smtpObj.send_message(message)
            logger.debug(f"Successfully sent email to {message['To']}")
        except OSError:
            logger.error("OSError:Error: unable to send email")
            logger.error("subject,message_body {msg['Subject'],msg.get_body('plain')}")
            logger.debug(f"{self.m_localhost,self.m_email_port}")
            logger.debug(f"sender,receivers {sender,receivers}")
        except Exception:
            logger.error("Exception:Error: unable to send email")
            logger.error("subject,message_body {msg['Subject'],msg.get_body('plain')}")
            logger.debug(f"{self.m_localhost,self.m_email_port}")
            logger.debug(f"sender,receivers {sender,receivers}")
        return 1

