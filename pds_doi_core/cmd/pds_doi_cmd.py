#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

from lxml import etree

from pds_doi_core.util.cmd_parser import create_cmd_parser
from pds_doi_core.util.const import *

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.input.validation_util import DOIValidatorUtil

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')
#logger.setLevel(logging.INFO)  # Comment this line once happy with the level of logging set in get_logger() function.
#logger.setLevel(logging.DEBUG)  # Comment this line once happy with the level of logging set in get_logger() function.
# Note that the get_logger() function may already set the level higher (e.g. DEBUG).  Here, we may reset
# to INFO if we don't want debug statements.

class DOICoreServices:
    m_doi_config_util = DOIConfigUtil()
    m_doi_input_util = DOIInputUtil()
    m_doi_pds4_label = DOIPDS4LabelUtil()
    m_doi_validator_util = DOIValidatorUtil()

    def _verify_osti_reserved_status(self,i_doi_label):
        # Function verify that all the status attribute in all records are indeed 'Reserved' as expected.
        o_reserved_flag = True
        o_out_text = None

        if i_doi_label is None:
            logger.error(f"The value of i_doi_label is none.  Will not continue.")
            exit(1)
        # If the type of i_doi_label remains as string, and starts with 'invalid', we had a bad time parsing.
        if str(type(i_doi_label)) == 'str' and i_doi_label.startswith('invalid'):
            logger.error(f"Cannot parse given target_url {target_url}")
            exit(1)

        # The parsing was successful, convert from bytes to string so we can build a tree.
        if isinstance(i_doi_label,bytes):
            xml_text = i_doi_label.decode()
        else:
            xml_text = i_doi_label.tostring()

        logger.info(f'type(i_doi_label) {type(i_doi_label)}')  # The type of i_doi_label is bytes
        logger.info(f'i_doi_label {i_doi_label}')  # The type of i_doi_label is bytes
        logger.info(f'xmlText {xml_text}')
        logger.info(f'type(xmlText) {type(xml_text)}')

        if isinstance(xml_text, bytes):
            doc = etree.fromstring(xml_text)
        else:
            doc = etree.fromstring(xml_text.encode())

        # Do a sanity check on the 'status' attribute for each record.  If not equal to 'Reserved' exit.
        my_root = doc.getroottree()
        num_reserved_statuses = 0
        num_record_records = 0
        for element in my_root.iter():
            if element.tag == 'record':
                num_record_records += 1
                my_record = my_root.xpath(element.tag)[0]
                if my_record.attrib['status'] == 'Reserved':
                    num_reserved_statuses += 1
                else:
                    logger.warning(f"Expected 'status' attribute to be 'Reserved'"
                                   f" but is not {my_record.attrib['status']}")
                    my_record.attrib['status'] = 'Reserved'
                    logger.warning("Reset status to 'Reserved'")
                    num_reserved_statuses += 1

        logger.debug(f"num_record_records,num_reserved_statuses {num_record_records} {num_reserved_statuses}")
        if num_record_records != num_reserved_statuses:
            logger.error(f"num_record_records is not the same as "
                         f"num_reserved_statuses {num_record_records} {num_reserved_statuses}")
            exit(0)

        o_out_text = etree.tostring(doc, pretty_print=True)
        logger.debug(f'o_out_text {o_out_text}')
        logger.debug(f'doc {doc}')

        return o_reserved_flag,o_out_text 

    def _process_reserve_action_csv(self, target_url, publisher_value, contributor_value):
        # Function process a reserve action based on .csv ending.

        # Get the default configuration from external file.  Location may have to be absolute.
        xml_config_file = os.path.join('.','config','default_config.xml')

        (dict_configlist, dict_fixedlist) = self.m_doi_config_util.get_config_file_metadata(xml_config_file)

        app_base_path = os.path.abspath(os.path.curdir)

        dict_condition_data = {}

        (o_num_files_created,
         o_aggregated_DOI_content) = self.m_doi_input_util.parse_csv_file(app_base_path,
                                                                      target_url,
                                                                      dict_fixedlist,
                                                                      dict_configlist,
                                                                      dict_condition_data)
        o_doi_label = o_aggregated_DOI_content
        logger.debug(f"o_num_files_created {o_num_files_created}")
        logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")
        return o_num_files_created,o_aggregated_DOI_content

    def reserve_doi_label(self, target_url, publisher_value, contributor_value):
        """
        Function receives a URI containing either XML, SXLS or CSV and create one or many labels to disk and submit these label(s) to OSTI.
        :param target_url:
        :param publisher_value:
        :param contributor_value:
        :return:
        """

        action_type = 'reserve_osti_label'
        o_doi_label = 'invalid action type:action_type ' + action_type

        logger.debug(f"target_url,action_type {target_url} {action_type}")

        if target_url.endswith('.xml'):
            o_doi_label = self.m_doi_pds4_label.parse_pds4_label_via_uri(target_url, publisher_value, contributor_value)

        elif target_url.endswith('.xlsx'):
            (o_num_files_created, o_aggregated_DOI_content) = self._process_reserve_action_xlsx(target_url, publisher_value, contributor_value)
            o_doi_label = o_aggregated_DOI_content

        elif target_url.endswith('.csv'):
            (o_num_files_created, o_aggregated_DOI_content) = self._process_reserve_action_csv(target_url, publisher_value, contributor_value)
            o_doi_label = o_aggregated_DOI_content

        # Check to see if the given file has an attempt to process.
        else:
            logger.error(f"File type has not been implemented:target_url {target_url}")
            exit(1)

        if o_doi_label is None:
            logger.error(f"The value of o_doi_label is none.  Will not continue.")
            exit(1)

        (o_reserved_flag, o_out_text) = self._verify_osti_reserved_status(o_doi_label)

    def _process_reserve_action_xlsx(self, target_url, publisher_value, contributor_value):
        # Function process a reserve action based on .xlsx ending.
        # Get the default configuration from external file.  Location may have to be absolute.
        xml_config_file = os.path.join('.','config','default_config.xml')

        logger.debug(f"xml_config_file {xml_config_file}")
        (dict_configlist, dict_fixedlist) = self.m_doi_config_util.get_config_file_metadata(xml_config_file)

        app_base_path = os.path.abspath(os.path.curdir)

        dict_condition_data = {}

        (o_num_files_created,
         o_aggregated_DOI_content) = self.m_doi_input_util.parse_sxls_file(app_base_path,
                                                                       target_url,
                                                                       dict_fixedlist,
                                                                       dict_configlist,
                                                                       dict_condition_data)
        o_doi_label = o_aggregated_DOI_content
        logger.debug(f"o_num_files_created {o_num_files_created}")
        logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")

        return o_num_files_created,o_aggregated_DOI_content

    def _process_reserve_action_csv(self, target_url, publisher_value, contributor_value):
        # Function process a reserve action based on .csv ending.

        # Get the default configuration from external file.  Location may have to be absolute.
        xml_config_file = os.path.join('.','config','default_config.xml')

        (dict_configlist, dict_fixedlist) = self.m_doi_config_util.get_config_file_metadata(xml_config_file)

        app_base_path = os.path.abspath(os.path.curdir)

        dict_condition_data = {}

        (o_num_files_created,
         o_aggregated_DOI_content) = self.m_doi_input_util.parse_csv_file(app_base_path,
                                                                      target_url,
                                                                      dict_fixedlist,
                                                                      dict_configlist,
                                                                      dict_condition_data)
        o_doi_label = o_aggregated_DOI_content
        logger.debug(f"o_num_files_created {o_num_files_created}")
        logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")
        return o_num_files_created,o_aggregated_DOI_content

    def reserve_doi_label(self, target_url, publisher_value, contributor_value):
        """
        Function receives a URI containing either XML, SXLS or CSV and create one or many labels to disk and submit these label(s) to OSTI.
        :param target_url:
        :param publisher_value:
        :param contributor_value:
        :return:
        """

        action_type = 'reserve_osti_label'
        o_doi_label = 'invalid action type:action_type ' + action_type

        logger.debug(f"target_url,action_type {target_url} {action_type}")

        if target_url.endswith('.xml'):
            o_doi_label = self.m_doi_pds4_label.parse_pds4_label_via_uri(target_url, publisher_value, contributor_value)

        elif target_url.endswith('.xlsx'):
            (o_num_files_created, o_aggregated_DOI_content) = self._process_reserve_action_xlsx(target_url, publisher_value, contributor_value)
            o_doi_label = o_aggregated_DOI_content

        elif target_url.endswith('.csv'):
            (o_num_files_created, o_aggregated_DOI_content) = self._process_reserve_action_csv(target_url, publisher_value, contributor_value)
            o_doi_label = o_aggregated_DOI_content

        # Check to see if the given file has an attempt to process.
        else:
            logger.error(f"File type has not been implemented:target_url {target_url}")
            exit(1)


        (o_reserved_flag, o_out_text) = self._verify_osti_reserved_status(o_doi_label)

        # The content would have been submitted already, we don't need to send it.

        # At this point, the o_out_text would contain tag "status = 'Reserved'" in each record tags.
        return o_out_text

    def create_doi_label(self, target_url, contributor_value):
        """
        Function receives a URI containing either XML or a local file and draft a Data Object Identifier (DOI).  
        :param target_url:
        :param contributor_value:
        :return: o_doi_label:
        """
        o_doi_label = None

        action_type = 'create_osti_label'
        publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE  # There is only one publisher of these DOI.
        o_contributor_is_valid_flag = False

        # Make sure the contributor is valid before proceeding.
        (o_contributor_is_valid_flag,
        o_permissible_contributor_list) = self.m_doi_validator_util.validate_contributor_value(
        DOI_CORE_CONST_PUBLISHER_URL, contributor_value)

        logger.info(f"o_contributor_is_valid_flag: {o_contributor_is_valid_flag}")
        logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")

        if not o_contributor_is_valid_flag:
            logger.error(f"The value of given contributor is not valid: {contributor_value}")
            logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")
            exit(0)

        o_doi_label = self.m_doi_pds4_label.parse_pds4_label_via_uri(target_url, publisher_value,
                                                                       contributor_value)
        logger.debug(f"o_doi_label {o_doi_label.decode()}")
        logger.debug(f"target_url,DOI_OBJECT_CREATED_SUCCESSFULLY {target_url}")
        if isinstance(o_doi_label,bytes):
            xml_text = o_doi_label.decode()
        else:
            xml_text = o_doi_label.tostring()

        return o_doi_label

def main():
    default_run_dir = os.path.join('.')

    run_dir = default_run_dir

    publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE

    parser = create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.action
    contributor_value = arguments.contributor.rstrip()  # Remove any leading and trailing blanks.
    input_location = arguments.input

    logger.info(f"run_dir {run_dir}")
    logger.info(f"publisher_value {publisher_value}")
    logger.info(f"input_location {input_location}")
    logger.info(f"contributor_value['{contributor_value}']")

    doi_core_services = DOICoreServices()

    if action_type == 'draft':
        o_doi_label = doi_core_services.create_doi_label(input_location, contributor_value)
        logger.info(o_doi_label.decode())

    elif action_type == 'reserve':
        o_doi_label = doi_core_services.reserve_doi_label(input_location, publisher_value, contributor_value)
        logger.info(o_doi_label.decode())

    else:
        logger.error(f"Action {action_type} is not supported yet.")
        exit(1)

if __name__ == '__main__':
    main()
