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
from pds_doi_core.util.general_util import DOIGeneralUtil, get_logger
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.input.validation_util import DOIValidatorUtil
from pds_doi_core.cmd.DOIWebClient import DOIWebClient

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')
#logger.setLevel(logging.INFO)  # Comment this line once happy with the level of logging set in get_logger() function.
#logger.setLevel(logging.DEBUG)  # Comment this line once happy with the level of logging set in get_logger() function.
# Note that the get_logger() function may already set the level higher (e.g. DEBUG).  Here, we may reset
# to INFO if we don't want debug statements.

class DOICoreServices:
    m_doiConfigUtil = DOIConfigUtil()
    m_doiGeneralUtil = DOIGeneralUtil()
    m_doiInputUtil = DOIInputUtil()
    m_doiPDS4LabelUtil = DOIPDS4LabelUtil()
    m_doiValidatorUtil = DOIValidatorUtil()
    m_doiWebClient = DOIWebClient()

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

        file_is_parsed_flag = False

        if target_url.endswith('.xml'):
            o_doi_label = self.m_doiPDS4LabelUtil.parse_pds4_label_via_uri(target_url, publisher_value, contributor_value)

            file_is_parsed_flag = True

        if target_url.endswith('.xlsx'):
            xls_filepath = target_url
            # Get the default configuration from external file.  Location may have to be absolute.
            xml_config_file = os.path.join('.','config','default_config.xml')

            logger.debug(f"xml_config_file {xml_config_file}")
            (dict_configList, dict_fixedList) = self.m_doiConfigUtil.get_config_file_metadata(xml_config_file)

            app_base_path = os.path.abspath(os.path.curdir)

            dict_condition_data = {}

            (o_num_files_created,
             o_aggregated_DOI_content) = self.m_doiInputUtil.parse_sxls_file(app_base_path,
                                                                           xls_filepath,
                                                                           dict_fixedList=dict_fixedList,
                                                                           dict_configList=dict_configList,
                                                                           dict_ConditionData=dict_condition_data)
            o_doi_label = o_aggregated_DOI_content
            file_is_parsed_flag = True
            logger.debug(f"o_num_files_created {o_num_files_created}")
            logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")

        if target_url.endswith('.csv'):
            xls_filepath = target_url
            # Get the default configuration from external file.  Location may have to be absolute.
            xml_config_file = os.path.join('.','config','default_config.xml')

            (dict_configList, dict_fixedList) = self.m_doiConfigUtil.get_config_file_metadata(xml_config_file)

            app_base_path = os.path.abspath(os.path.curdir)

            dict_condition_data = {}

            (o_num_files_created,
             o_aggregated_DOI_content) = self.m_doiInputUtil.parse_csv_file(app_base_path,
                                                                          xls_filepath,
                                                                          dict_fixedList=dict_fixedList,
                                                                          dict_configList=dict_configList,
                                                                          dict_ConditionData=dict_condition_data)
            o_doi_label = o_aggregated_DOI_content
            file_is_parsed_flag = True
            logger.debug(f"o_num_files_created {o_num_files_created}")
            logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")

        # Check to see if the given file has an attempt to process.
        if not file_is_parsed_flag:
            logger.error(f"File type has not been implemented:target_url {target_url}")
            exit(0)

        if o_doi_label is None:
            logger.error(f"The value of o_doi_label is none.  Will not continue.")
            exit(0)

        # If the type of o_doi_label remains as string, and starts with 'invalid', we had a bad time parsing.
        if str(type(o_doi_label)) == 'str' and o_doi_label.startswith('invalid'):
            logger.error(f"Cannot parse given target_url {target_url}")
            exit(0)

        # The parsing was successful, convert from bytes to string so we can build a tree.
        xml_text = self.m_doiGeneralUtil.decode_bytes_to_string(o_doi_label)

        logger.info(f'type(o_doi_label) {type(o_doi_label)}')  # The type of o_doi_label is bytes
        logger.info(f'o_doi_label {o_doi_label}')  # The type of o_doi_label is bytes
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

        s_out_text = etree.tostring(doc, pretty_print=True)
        logger.debug(f's_out_text {s_out_text}')
        logger.debug(f'doc {doc}')

        # The content would have been submitted already, we don't need to send it.

        # At this point, the sOutText would contain tag "status = 'Reserved'" in each record tags.
        return s_out_text

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
        o_permissible_contributor_list) = self.m_doiValidatorUtil.ValidateContributorValue(
        DOI_CORE_CONST_PUBLISHER_URL, contributor_value)

        logger.info(f"o_contributor_is_valid_flag: {o_contributor_is_valid_flag}")
        logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")

        if not o_contributor_is_valid_flag:
            logger.error(f"The value of given contributor is not valid: {contributor_value}")
            logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")
            exit(0)

        type_is_valid = False
        o_doi_label = 'invalid action type:action_type ' + action_type

        if action_type == 'create_osti_label':
            o_doi_label = self.m_doiPDS4LabelUtil.parse_pds4_label_via_uri(target_url, publisher_value,
                                                                        contributor_value)
            type_is_valid = True

        if not type_is_valid:
            logger.error(o_doi_label)
            logger.info(f"action_type {action_type}")
            logger.info(f"target_url {target_url}")
            exit(0)

        logger.debug(f"o_doi_label {o_doi_label.decode()}")
        logger.debug(f"target_url,DOI_OBJECT_CREATED_SUCCESSFULLY {target_url}")

        return o_doi_label


def main():
    default_run_dir = os.path.join('.');
    default_target_url = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'

    # default_publisher_url  = 'https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON'
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

    doiCoreServices = DOICoreServices()

    if action_type == 'draft':
        o_doi_label = doiCoreServices.create_doi_label(input_location, contributor_value)
        logger.info(o_doi_label.decode())

    if action_type == 'reserve':
        o_doi_label = doiCoreServices.reserve_doi_label(input_location, publisher_value, contributor_value)
        type_is_valid = True
        logger.info(o_doi_label.decode())


if __name__ == '__main__':
    main()
