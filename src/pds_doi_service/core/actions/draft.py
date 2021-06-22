#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
========
draft.py
========

Contains the definition for the Draft action of the Core PDS DOI Service.
"""

import copy
import glob
from os.path import exists, join

from lxml import etree

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import (UnknownNodeException,
                                                   DuplicatedTitleDOIException,
                                                   UnexpectedDOIActionException,
                                                   NoTransactionHistoryForLIDVIDException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   InputFormatException,
                                                   CriticalDOIException,
                                                   InvalidLIDVIDException,
                                                   collect_exception_classes_and_messages,
                                                   raise_or_warn_exceptions)
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.outputs.doi_validator import DOIValidator
from pds_doi_service.core.outputs.osti.osti_record import DOIOstiRecord
from pds_doi_service.core.outputs.osti.osti_validator import OSTIValidator
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOICoreActionDraft(DOICoreAction):
    _name = 'draft'
    _description = 'Prepare a draft DOI record from PDS4 labels'
    _order = 10
    _run_arguments = ('input', 'node', 'submitter', 'lidvid', 'force', 'keywords')

    DEFAULT_KEYWORDS = ['PDS', 'PDS4']
    """Default keywords added to each new draft request."""

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._osti_validator = OSTIValidator()
        self._list_obj = DOICoreActionList(db_name=db_name)

        self._input = None
        self._node = None
        self._submitter = None
        self._lidvid = None
        self._force = False
        self._target = None
        self._keywords = ''

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name,
            description='Create a draft DOI record, from existing PDS4 or DOI '
                        'labels'
        )

        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument(
            '-i', '--input', required=False,
            metavar='input/bundle_in_with_contributors.xml',
            help='An input PDS4/DOI label. May be a local path or an HTTP address '
                 'resolving to a label file. Multiple inputs may be provided '
                 'via comma-delimited list. Must be provided if --lidvid is not '
                 'specified.'
        )
        action_parser.add_argument(
            '-n', '--node', required=True,  metavar='"img"',
            help='The PDS Discipline Node in charge of the DOI. Authorized '
                 'values are: ' + ','.join(node_values)
        )
        action_parser.add_argument(
            '-s', '--submitter', required=True, metavar='"my.email@node.gov"',
            help='The email address to associate with the Draft record.'
        )
        action_parser.add_argument(
            '-l', '--lidvid', required=False,
            metavar='urn:nasa:pds:lab_shocked_feldspars::1.0',
            help='A LIDVID for an existing DOI record to move back to draft '
                 'status. Must be provided if --input is not specified.'
        )
        action_parser.add_argument(
            '-f', '--force', required=False, action='store_true',
            help='If provided, forces the action to proceed even if warnings are '
                 'encountered during submission of the draft record to the '
                 'database. Without this flag, any warnings encountered are '
                 'treated as fatal exceptions.',
        )
        action_parser.add_argument(
            '-k', '--keywords', required=False, metavar='"Image"', default='',
            help='Extra keywords to associate with the Draft record. Multiple '
                 'keywords must be separated by ",". Ignored when used with the '
                 '--lidvid option.'
        )
        action_parser.add_argument(
            '-t', '--target',  required=False, default='osti', metavar='osti',
            help='The target service provider to mint the DOI. Currently, only '
                 'the value "osti" is supported.'
        )

    def _set_lidvid_to_draft(self, lidvid):
        """
        Sets the status of the transaction record corresponding to the provided
        LIDVID back draft. This can be typical for records that do not advance
        past the review step.

        Parameters
        ----------
        lidvid : str
            The LIDVID associated to the record to set to draft.

        Returns
        -------
        doi_label : str
            The XML label for the provided LIDVID reflecting its draft status.

        Raises
        ------
        NoTransactionHistoryForLIDVIDException
            If an entry for the provided LIDVID exists in the transaction
            database, but no local transaction history can be found.

        """
        # Get the output label produced from the last transaction
        # with this LIDVID
        transaction_record = self._list_obj.transaction_for_lidvid(lidvid)

        # Make sure we can locate the output label associated with this
        # transaction
        transaction_location = transaction_record['transaction_key']
        label_files = glob.glob(join(transaction_location, 'output.*'))

        if not label_files or not exists(label_files[0]):
            raise NoTransactionHistoryForLIDVIDException(
                f'Could not find a DOI label associated with LIDVID {lidvid}. '
                'The database and transaction history location may be out of sync. '
                'Please try resubmitting the record in reserve or draft.'
            )

        label_file = label_files[0]

        # Label could contain entries for multiple LIDVIDs, so extract
        # just the one we care about
        lidvid_record, content_type = DOIOstiWebParser.get_record_for_lidvid(
            label_file, lidvid
        )

        # Format label into an in-memory DOI object
        dois, _ = DOIOstiWebParser.parse_dois_from_label(lidvid_record, content_type)

        doi = dois[0]

        # Update the status back to draft while noting the previous status
        doi.previous_status = doi.status
        doi.status = DoiStatus.Draft

        # Update the contributor
        doi.contributor = NodeUtil().get_node_long_name(self._node)

        # Re-commit transaction to official roll DOI back to draft status
        transaction = self.m_transaction_builder.prepare_transaction(
            self._node, self._submitter, doi, input_path=label_file,
            output_content_type=content_type
        )

        # Commit the transaction to the database
        transaction.log()

        # Return up-to-date output label
        return transaction.output_content

    def _draft_input_files(self, inputs):
        """
        Creates draft records for the list of input files/locations.

        Parameters
        ----------
        inputs : str
            Comma-delimited listing of the inputs to produce draft records for.
            These may be local paths to a file or directory, or remote URLs.

        Returns
        -------
        doi_label : str
            An XML DOI label containing the draft records for requested inputs.

        Raises
        ------
        CriticalDOIException
            If any errors occur during creation of the draft records.

        """
        try:
            # The value of input can be a list of names, or a directory.
            # Split them up and let the input util library handle determination
            # of each type
            list_of_inputs = inputs.split(',')

            # Filter out any empty strings from trailing commas
            list_of_inputs = list(
                filter(lambda input_file: len(input_file), list_of_inputs)
            )

            # OSTI XML schema uses 'records' as the root tag.
            o_doi_labels = etree.Element("records")

            # For each name found, transform the PDS4 label to an OSTI record,
            # then concatenate that record to o_doi_label to return.
            for input_file in list_of_inputs:
                doi_labels = self._run_single_file(
                    input_file, self._node, self._submitter, self._force,
                    self._keywords
                )

                # It is possible that doi_labels is empty if the file
                # is not a valid label.
                if not doi_labels:
                    continue

                # Concatenate each label to o_doi_labels to return.
                for doi_label in doi_labels:
                    doc = etree.fromstring(doi_label.encode())

                    # OSTI XML schema uses 'record' tag for each record.
                    for element in doc.findall('record'):
                        # Add the 'record' element
                        o_doi_labels.append(copy.copy(element))

            # Make the output nice by indenting it.
            etree.indent(o_doi_labels)

            return etree.tostring(o_doi_labels, pretty_print=True).decode()
        except UnknownNodeException as err:
            raise CriticalDOIException(str(err))

    def _add_extra_keywords(self, keywords, io_doi):
        """
        Adds any extra keywords to the already produced DOI object.
        """
        # Add in the default set of keywords.
        io_doi.keywords |= set(self.DEFAULT_KEYWORDS)

        # Add the node long name (contributor) as a keyword as well.
        io_doi.keywords.add(io_doi.contributor.lower())

        # The keywords are comma separated. The io_doi.keywords field is a set.
        if keywords:
            keyword_tokens = set(map(str.strip, keywords.split(',')))

            io_doi.keywords |= keyword_tokens

        return io_doi

    def _transform_label_into_osti_record(self, input_file, keywords):
        """
        Receives an input file and transforms it into an OSTI record.
        """
        input_util = DOIInputUtil(valid_extensions=['.json', '.xml'])

        o_dois = input_util.parse_dois_from_input_file(input_file)
        o_doi_labels = []

        for o_doi in o_dois:
            o_doi.publisher = self._config.get('OTHER', 'doi_publisher')
            o_doi.contributor = NodeUtil().get_node_long_name(self._node)

            # Add 'status' field so the ranking in the workflow can be determined.
            o_doi.status = DoiStatus.Draft

            # Add any default keywords or extra keywords provided by the user.
            self._add_extra_keywords(keywords, o_doi)

            # Generate the output OSTI record
            o_doi_label = DOIOstiRecord().create_doi_record(o_doi)

            o_doi_labels.append(o_doi_label)

        # Return the labels and a list 'o_dois' representing all individual
        # DOI's parsed.
        return o_doi_labels, o_dois

    def _run_single_file(self, input_file, node, submitter, force_flag, keywords):
        logger.info("Drafting input file %s", input_file)
        logger.debug("node,submitter,force_flag,keywords: %s,%s,%s,%s",
                     node, submitter, force_flag, keywords)

        exception_classes = []
        exception_messages = []

        i_doi_labels = None
        o_doi_labels = []
        doi_objs = None

        try:
            # Transform the input label to an OSTI record and list of Doi objects,
            # then validate each accordingly
            i_doi_labels, doi_objs = self._transform_label_into_osti_record(
                input_file, keywords
            )

            for doi_label in i_doi_labels:
                self._osti_validator.validate(doi_label, action=self._name)

            for doi_obj in doi_objs:
                self._doi_validator.validate(doi_obj)
        # Collect any exceptions/warnings for now and decide whether to
        # raise or log them later on
        except (DuplicatedTitleDOIException,
                InvalidLIDVIDException,
                UnexpectedDOIActionException,
                TitleDoesNotMatchProductTypeException) as err:
            (exception_classes,
             exception_messages) = collect_exception_classes_and_messages(
                err, exception_classes, exception_messages
            )
        # Propagate input format exceptions, force flag should not affect
        # these being raised and certain callers (such as the API) look
        # for this exception specifically
        except InputFormatException as err:
            raise err
        # Catch all other exceptions as errors
        except Exception as err:
            raise CriticalDOIException(err)

        # If there is at least one exception caught, either raise a
        # WarningDOIException or log a warning with all the messages,
        # depending on the the state of the force flag
        if len(exception_classes) > 0:
            raise_or_warn_exceptions(exception_classes, exception_messages,
                                     log=force_flag)

        if i_doi_labels and doi_objs:
            for doi_obj in doi_objs:
                # Use the service of TransactionBuilder to prepare all things
                # related to writing a transaction.
                transaction = self.m_transaction_builder.prepare_transaction(
                    node, submitter, doi_obj, input_path=input_file
                )

                # Commit the transaction to the database
                transaction.log()

                # Return the most up-to-date version of output label
                o_doi_labels.append(transaction.output_content)

        return o_doi_labels

    def run(self, **kwargs):
        """
        Receives a number of input label locations from which to create a
        draft Data Object Identifier (DOI). Each location may be a local directory
        or file path, or a remote HTTP address to the input XML PDS4 label file.

        Parameters
        ----------
        kwargs : dict
            Contains the arguments for the Draft action as parsed from the
            command-line.

        Raises
        ------
        ValueError
            If the provided arguments are invalid.

        """
        self.parse_arguments(kwargs)

        # Make sure we've been given something to work with
        if self._input is None and self._lidvid is None:
            raise ValueError('A value must be provided for either --input or '
                             '--lidvid when using the Draft action.')

        if self._lidvid:
            return self._set_lidvid_to_draft(self._lidvid)

        if self._input:
            return self._draft_input_files(self._input)
