#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
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

from copy import deepcopy
from datetime import date
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from os.path import exists
from pkg_resources import resource_filename

import pystache

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.emailer import Emailer
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.actions.check')


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

        self.email_header_template_file = resource_filename(
            __name__, 'email_template_header.mustache'
        )

        self.email_body_template_file = resource_filename(
            __name__, 'email_template_body.txt'
        )

        # Make sure templates are where we expect them to be
        if (not exists(self.email_header_template_file)
                or not exists(self.email_body_template_file)):
            raise RuntimeError(
                f'Could not find one or more email templates needed by this action\n'
                f'Expected header template: {self.email_header_template_file}\n'
                f'Expected body template: {self.email_body_template_file}'
            )

        with open(self.email_body_template_file, 'r') as infile:
            self.email_body_template = infile.read().strip()

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)

        action_parser.add_argument(
            '-e', '--email', required=False, action='store_true',
            help='If provided, the check action sends results to the default '
                 'recipients and pending DOI submitters.'
        )
        action_parser.add_argument(
            '-a', '--attachment', required=False, action='store_true',
            help='If provided, the check action sends results as an email '
                 'attachment. Has no effect if --email is not also provided.'
        )
        action_parser.add_argument(
            '-s', '--submitter', required=False, metavar='"my.email@node.gov"',
            help='The email address of the user to register as author of the '
                 'check action.'
        )

    def _update_transaction_db(self, pending_record):
        """
        Processes the result from the one 'check' query to OSTI server.

        If the status has changed from initial status, update the old record in
        the database and write a new record to the database and return DOI just
        updated.

        """
        doi_value = pending_record['doi']
        lidvid = '::'.join([pending_record['lid'], pending_record['vid']])

        logger.info(
            'Checking OSTI release status for DOI %s (LIDVID %s)',
            doi_value, lidvid
        )

        query_dict = {'doi': doi_value}

        doi_xml = DOIOstiWebClient().webclient_query_doi(
            self._config.get('OSTI', 'url'), query_dict,
            i_username=self._config.get('OSTI', 'user'),
            i_password=self._config.get('OSTI', 'password')
        )
        dois, errors = DOIOstiWebParser.parse_osti_response_xml(doi_xml)

        if dois:
            # Should only ever be one entry returned
            doi = dois[0]

            if doi.status != DoiStatus.Pending:
                logger.info("DOI has changed from status %s to %s",
                            DoiStatus.Pending, doi.status)

                # Set the author for this action
                doi.submitter = self._submitter

                # Update the previous status we store in the transaction database
                doi.previous_status = DoiStatus.Pending

                # If there was an error submitting to OSTI, include the details.
                # Since we only check one DOI at a time, should be safe
                # to index by 0 here
                if errors:
                    doi.message = '\n'.join(errors[0])

                # Log the update to the DOI entry
                transaction_obj = self.m_transaction_builder.prepare_transaction(
                    pending_record['node_id'], pending_record['submitter'],
                    [doi], output_content=doi_xml
                )

                transaction_obj.log()
            else:
                logger.info('No change in %s status for DOI %s (LIDVID %s)',
                            DoiStatus.Pending, doi_value, lidvid)

            # Update the record we'll be using to populate the status email
            pending_record['previous_status'] = pending_record['status']
            pending_record['status'] = doi.status
            pending_record['lidvid'] = lidvid
            pending_record['message'] = doi.message

            # Remove some behind-the-scenes fields users shouldn't care about
            pending_record.pop('transaction_key', None)
            pending_record.pop('is_latest', None)
        else:
            logger.error(
                "No record for DOI %s (LIDVID %s) found at OSTI",
                pending_record['doi'], lidvid
            )

    def _get_distinct_nodes_and_submitters(self, i_check_result):
        """
        Gets a list of distinct nodes and distinct submitters for each node from
        a list of metadata i_check_result.
        """
        o_distinct_info = {}

        for one_result in i_check_result:
            # Make lowercase to be consistent.
            node_id_key = one_result['node_id'].lower()

            # Create an empty set of submitters and list of records keyed to
            # node_id_key if we haven't already.
            if node_id_key not in o_distinct_info:
                o_distinct_info[node_id_key] = {
                    'submitters': set(), 'records': list()
                }

            # Add the submitter to distinct_submitters for a particular node
            # if we haven't already.
            o_distinct_info[node_id_key]['submitters'].add(one_result['submitter'].lower())

            # Add each record to a particular node.
            o_distinct_info[node_id_key]['records'].append(one_result)

        return o_distinct_info

    def _prepare_attachment(self, i_dicts_per_submitter):
        """
        Prepares an attachment by converting i_dicts_per_submitter to a JSON
        text and returns the o_attachment_part as MIMEMultipart object.
        """
        # Convert a list of dict to JSON text to make it human readable.
        attachment_text = json.dumps(
            i_dicts_per_submitter,
            indent=4  # Make output human readable by indentation
        )

        # Add current time to make file unique
        now_is = datetime.datetime.now().strftime('%Y%m%d-%H%M')
        o_attachment_filename = f'doi_status_{now_is}.json'

        o_attachment_part = MIMEMultipart()
        part = MIMEBase('application', 'json')
        part.add_header('Content-Disposition',
                        f'attachment; filename={o_attachment_filename}')
        part.set_payload(attachment_text)
        o_attachment_part.attach(part)

        return o_attachment_part

    def _prepare_email_message(self, i_dicts_per_submitter):
        renderer = pystache.Renderer()
        today = date.today()

        # Build the email header containing date and number of records
        header_dict = {
            'my_date': today.strftime("%m/%d/%Y"),
            'my_records_count': len(i_dicts_per_submitter)
        }
        email_header = renderer.render_path(
            self.email_header_template_file, header_dict
        )

        # Build the email body containing the table of DOIs with status
        body_header = self.email_body_template.format(
            record_index='#', id='ID', title='Title', doi='DOI', lidvid='LIDVID',
            previous_status='Previous Status', status='Current Status'
        )
        body_divider = '-' * len(body_header)
        email_body = [body_header, body_divider]

        for index, record in enumerate(i_dicts_per_submitter):
            email_body.append(
                self.email_body_template.format(record_index=index + 1,
                                                id=record['doi'].split('/')[-1],
                                                **record)
            )

        email_body = '\n'.join(email_body)

        o_email_entire_message = "\n".join([email_header, email_body])
        logger.debug("o_email_entire_message:\n%s\n", o_email_entire_message)

        return o_email_entire_message

    def _send_email(self, email_sender, final_receivers, subject_field,
                    email_entire_message, o_dicts_per_node):
        if not self._attachment:
            # This sends a brief email message.
            self._emailer.sendmail(
                email_sender, final_receivers, subject_field, email_entire_message
            )
        else:
            # Try an alternative way to send the email so the attachment will be
            # viewable as an attachment in the email reader.
            msg = EmailMessage()
            msg["From"] = email_sender
            msg["Subject"] = subject_field
            msg["To"] = final_receivers

            msg.set_content(email_entire_message)

            attachment_part = self._prepare_attachment(o_dicts_per_node)

            # The attachment is now 'attached' in the msg object.
            msg.add_attachment(attachment_part)

            # Send the email with attachment file.
            self._emailer.send_message(msg)

    def _group_updated_doi_records_and_email(self, i_check_result):
        """
        From all records in i_check_result, group a list of records per
        submitter and send an email of the status of metadata of DOIs with
        status changed to receivers.
        """
        # Get configurations related to sending email.
        email_sender = self._config.get('OTHER', 'emailer_sender')
        email_receivers_field = self._config.get('OTHER', 'emailer_receivers')

        # The receivers can be a comma-delimited list of addresses.
        email_receivers_tokens = email_receivers_field.split(',')

        # Get distinct list of email addresses from email_receivers_field in
        # case they have duplicates.
        email_receivers = set(
            [email_receiver_token.strip().lower()
             for email_receiver_token in email_receivers_tokens]
        )

        # Ensure the submitter of this check action included if they're not already
        email_receivers.add(self._submitter)

        # Get distinct info from i_check_result
        # The distinct info is a dictionary containing distinct nodes as keys
        # with 'submitters' and 'records' as values for each node.
        o_distinct_info = self._get_distinct_nodes_and_submitters(i_check_result)

        # For each node, e.g 'img','naif', get all records for that node and
        # send an email for all submitters of that node, along with the receivers.
        for node_key in o_distinct_info:
            # Build a list of unique recipients for the emailer.
            # Make a copy since we need a new email list for that node.
            final_receivers = deepcopy(email_receivers)

            # Add emails of all submitters for that node.
            final_receivers |= o_distinct_info[node_key]['submitters']

            now_is = datetime.datetime.now().isoformat()
            subject_field = f"DOI Submission Status Report For Node {node_key} On {now_is}"

            # Convert a list of dict to JSON text to make it human readable.
            dois_per_node = [
                element['doi']
                for element in o_distinct_info[node_key]['records']
            ]
            logger.debug(
                "NUM_RECORDS_PER_NODE_AND_SUBMITTERS: %s,%s,%d,%s",
                node_key, dois_per_node, len(dois_per_node),
                o_distinct_info[node_key]['submitters']
            )

            # Prepare the email message using all the dictionaries (records
            # associated with that node).
            email_entire_message = self._prepare_email_message(
                o_distinct_info[node_key]['records']
            )

            # Finally, send the email with all status changed per node.
            # The report is for a particular node, e.g 'img' send to all submitters
            # for that node (along with other recipients in final_receivers)
            self._send_email(
                email_sender, final_receivers, subject_field,
                email_entire_message, o_distinct_info[node_key]['records']
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

        # Get the list of latest rows in database with status = 'Pending'.
        o_doi_list = self._list_obj.run(status=DoiStatus.Pending)
        pending_state_list = json.loads(o_doi_list)

        logger.info(f'Found %d %s record(s) to check', len(pending_state_list),
                    DoiStatus.Pending)

        if len(pending_state_list) > 0:
            for pending_record in pending_state_list:
                self._update_transaction_db(pending_record)

            if self._email:
                self._group_updated_doi_records_and_email(pending_state_list)

        # Return a list of DOIs updated or still in pending status.
        # List can be empty, meaning no records have changed from 'Pending'
        # to something else.
        return pending_state_list
