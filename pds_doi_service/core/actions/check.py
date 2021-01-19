#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
========
check.py
========

Contains the definition for the Check action of the Core PDS DOI Service.
"""

import datetime
import json
import os
from copy import deepcopy
from datetime import date
from os.path import dirname, join

import pystache

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.emailer import Emailer
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.check')


class DOICoreActionCheck(DOICoreAction):
    _name = 'check'
    _description = ('Check DOI pending status at OSTI and update the local '
                    'database. Should be run regularly, for example in a '
                    'crontab.')
    _order = 30
    _run_arguments = ('submitter', 'email', 'attachment')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._list_obj = DOICoreActionList(db_name=db_name)
        self._emailer = Emailer()

        self._submitter = self._config.get('OTHER', 'emailer_sender')
        self._email = True
        self._attachment = True

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)

        action_parser.add_argument(
            '-e', '--email', required=False, action='store_true',
            help='If provided, the check action sends results to the default '
                 'recipients and pending DOI submitters'
        )
        action_parser.add_argument(
            '-a', '--attachment', required=False, action='store_true',
            help='If provided, the check action sends results as an email '
                 'attachment'
        )
        action_parser.add_argument(
            '-r', '--submitter', required=False, metavar='"my.email@node.gov"',
            help='The email address of the user to register as author of the '
                 'check action'
        )

    def _update_transaction_db_when_needed(self, pending_record):
        """
        Processes the result from the one 'check' query to OSTI server.

        If the status has changed from initial status, update the old record in
        the database and write a new record to the database and return DOI just
        updated.

        :param pending_record:
        :return: o_doi_updated:

        """
        doi_value = pending_record['doi']
        query_dict = {'doi': doi_value}
        doi_xml = DOIOstiWebClient().webclient_query_doi(
            self._config.get('OSTI', 'url'), query_dict,
            i_username=self._config.get('OSTI', 'user'),
            i_password=self._config.get('OSTI', 'password')
        )
        dois, _ = DOIOstiWebParser.response_get_parse_osti_xml(doi_xml)

        if dois:
            doi = dois[0]

            if doi.status != DoiStatus.Pending:
                # have an author for this automated action
                doi.submitter = self._submitter

                transaction_obj = self.m_transaction_builder.prepare_transaction(
                    pending_record['node_id'], pending_record['submitter'],
                    [doi], output_content=doi_xml
                )

                transaction_obj.log()
                pending_record['initial_status'] = pending_record['status']
                pending_record['status'] = doi.status
        else:
            logger.error(
                f"doi {pending_record['doi']} for lidvid "
                + f"{pending_record['lid']}::{pending_record['vid']} no found at OSTI"
            )

        return pending_record

    def _get_distinct_nodes_and_submitters(self, i_check_result):
        """
        Gets a list of distinct nodes and distinct submitters for each node from
        a list of metadata i_check_result.
        """
        o_distinct_info = {}

        for one_result in i_check_result:
            # Make lowercase to be consistent.
            node_id_key = one_result['node_id'].lower()

            # Create an empty list of 'distinct_submitters' to key node_id_key
            # if we haven't already.
            if node_id_key not in o_distinct_info:
                # Create an empty list of 'distinct_submitters' to key node_id_key.
                o_distinct_info[node_id_key] = {}
                o_distinct_info[node_id_key]['distinct_submitters'] = set()
                o_distinct_info[node_id_key]['distinct_records'] = []

            # Add the submitter to distinct_submitters for a particular node
            # if we haven't already.
            o_distinct_info[node_id_key]['distinct_submitters'].add(one_result['submitter'].lower())

            # Add each record to a particular node.
            o_distinct_info[node_id_key]['distinct_records'].append(one_result)

        return o_distinct_info

    def _prepare_attachment(self, i_dicts_per_submitter):
        """
        Prepares an attachment by converting i_dicts_per_submitter to a JSON
        text and returns the o_attachment_part as MIMEMultipart object.
        """
        # Only do the import if sending an attachment file along with the email.
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase

        # Convert a list of dict to JSON text to make it human readable.
        attachment_text = json.dumps(
            i_dicts_per_submitter,
            indent=4  # Make human read-able output with indentation of each key.
        )

        # Add current time to make file unique
        now_is = datetime.datetime.now().isoformat()
        o_attachment_filename = 'doi_status_attachment_on_' + now_is + '.txt'

        # Write the text to disk so the file can be sent as an attachment.
        with open(o_attachment_filename, 'w+') as file_ptr:
            file_ptr.write(attachment_text)

        o_attachment_part = MIMEMultipart()
        part = MIMEBase('application', 'text')
        part.add_header('Content-Disposition',
                        "attachment; filename= %s" % o_attachment_filename)
        part.set_payload(attachment_text)
        o_attachment_part.attach(part)

        # Must return the attachment filename so it can be deleted after the
        # email has been successfully sent.
        return o_attachment_filename, o_attachment_part

    def _prepare_email_entire_message(self, i_dicts_per_submitter):
        renderer = pystache.Renderer()
        today = date.today()

        # There is an 'Id' column in the email content so that field needs to be
        # built.
        # The field 'record_index' is to allow Pystache to print the record
        # number on the left most column.
        record_index = 0
        for doi_record in i_dicts_per_submitter:
            # Split '10.17189/21940' to get to 21940
            doi_record['id'] = doi_record['doi'].split('/')[1]
            doi_record['record_index'] = record_index + 1
            record_index += 1

        # Build the email first part containing: Date: 07/01/2020\n 3 records.
        header_dict = {
            'my_date': today.strftime("%m/%d/%Y"),
            'my_records_count': len(i_dicts_per_submitter)
        }
        email_part1_template = join(dirname(__file__), 'emailer_template_part_1-mustache.json')
        email_part_1 = renderer.render_path(email_part1_template, header_dict)

        # Build the email second part containing the table of DOIs with status
        # changed: "1  21940  Laboratory Shocked Feldspars Bundle  10.17189/21940  Pending  Reserved"
        email_part2_template = join(dirname(__file__), 'emailer_template_part_2-mustache.json')
        email_part_2 = renderer.render_path(email_part2_template,
                                            {'dois': i_dicts_per_submitter})

        o_email_entire_message = email_part_1 + "\n" + email_part_2
        logger.debug(f"o_email_entire_message {o_email_entire_message}")

        return o_email_entire_message

    def _send_email(self, to_send_attachment_flag, email_sender, final_receivers,
                    subject_field, email_entire_message, o_dicts_per_node):
        if not to_send_attachment_flag:
            # This sends a brief email message.
            self._emailer.sendmail(
                email_sender, final_receivers, subject_field, email_entire_message
            )
        else:
            # Try an alternative way to send the email so the attachment will be
            # viewable as an attachment in the email reader.
            # Only import if sending an attachment file along with the email.
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"] = email_sender
            msg["Subject"] = subject_field
            msg["To"] = final_receivers

            msg.set_content(email_entire_message)

            (attachment_filename,
             attachment_part) = self._prepare_attachment(o_dicts_per_node)

            # The attachment is now 'attached' in the msg object.
            msg.add_attachment(attachment_part)

            # Send the email with attachment file.
            self._emailer.send_message(msg)

            # Delete the temporary attached file.
            if os.path.isfile(attachment_filename):
                os.remove(attachment_filename)

    def _group_dois_updated_records_and_email(self, i_check_result,
                                              to_send_mail_flag=False,
                                              to_send_attachment_flag=False):
        """
        From all records in i_check_result, group a list of records per
        submitter and send an email of the status of metadata of DOIs with
        status changed to receivers.
        """
        logger.debug(f"to_send_mail_flag {to_send_mail_flag}")

        # Get configurations related to sending email.
        email_sender = self._config.get('OTHER', 'emailer_sender')
        email_receivers_field = self._config.get('OTHER', 'emailer_receivers')

        # The receivers can be a comma-delimited list of addresses.
        email_receivers_tokens = email_receivers_field.split(',')
        email_receivers = set()

        # Get distinct list of email addresses from email_receivers_field in
        # case they have duplicates.
        for email_receiver_token in email_receivers_tokens:
            email_receivers.add(email_receiver_token.lstrip().rstrip().lower())

        # Get distinct info from i_check_result
        # The distinct info is a dictionary containing distinct nodes as keys
        # and 'distinct_submitters', 'distinct_records' as values for each node.
        o_distinct_info = self._get_distinct_nodes_and_submitters(i_check_result)

        # For each node, e.g 'img','naif', get all records for that node and
        # send an email for all submitters of that node, along with the receivers.
        for node_key in list(o_distinct_info.keys()):
            # Build a list of unique recipients for the emailer.
            # Make a copy since we need a new email list for that node.
            final_receivers = deepcopy(email_receivers)

            # Add emails of all submitters for that node.
            final_receivers.union(
                o_distinct_info[node_key]['distinct_submitters']
            )

            now_is = datetime.datetime.now().isoformat()
            subject_field = f"DOI Submission Status Report For Node {node_key} On {now_is}"

            # Convert a list of dict to JSON text to make it human readable.
            dois_per_node = [
                element['doi']
                for element in o_distinct_info[node_key]['distinct_records']
            ]
            logger.debug(
                "NUM_RECORDS_PER_NODE_AND_SUBMITTERS "
                f"{node_key, dois_per_node, len(dois_per_node), o_distinct_info[node_key]['distinct_submitters']}"
            )

            # Prepare the email message using all the dictionaries (records
            # associated with that node).
            email_entire_message = self._prepare_email_entire_message(
                o_distinct_info[node_key]['distinct_records']
            )
            logger.debug(f"email_entire_message {email_entire_message}")

            # Finally, send the email with all status changed per node.
            # The report is for a particular node, e.g 'img' send to all submitters
            # for that node (along with other recipients in final_receivers)
            if to_send_mail_flag:
                self._send_email(
                    to_send_attachment_flag, email_sender, final_receivers,
                    subject_field, email_entire_message,
                    o_distinct_info[node_key]['distinct_records']
                )

    def run(self, **kwargs):
        """
        Queries the local database for latest Pending state records and checks
        the OSTI server for all the records with criteria specified in
        query_criterias, returning the results either in JSON or XML.

        Once the query is returned, every record is checked against its initial
        status and the status returned from OSTI. If the status has changed from
        initial, this function writes a new record to the database.

        All parameters are optional and may be useful for tests.

        """
        self.parse_arguments(kwargs)

        pending_state_list = []

        # Get the list of latest rows in database with status = 'Pending'.
        o_doi_list = self._list_obj.run(status=DoiStatus.Pending)

        if len(o_doi_list) > 0:
            pending_state_list = json.loads(o_doi_list)

            for pending_record in pending_state_list:
                logger.debug(f"pending_record {pending_record}")
                self._update_transaction_db_when_needed(pending_record)

            self._group_dois_updated_records_and_email(
                pending_state_list, self._email, self._attachment
            )

        # Return a list of DOIs updated or still in pending status.
        # List can be empty meaning no records have changed from 'Pending'
        # to something else.
        return pending_state_list

# end class DOICoreActionCheck(DOICoreAction):
