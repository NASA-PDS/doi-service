#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

from lxml import etree
import requests

from pds_doi_core.util.cmd_parser import create_cmd_parser
from pds_doi_core.util.const import *

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.input.exeptions import InputFormatException
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.references.contributors import DOIContributorUtil
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.outputs.osti import create_osti_doi_record
from pds_doi_core.outputs.output_util import DOIOutputUtil

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
    m_doi_output_util = DOIOutputUtil()
    m_doi_pds4_label = DOIPDS4LabelUtil()


    def __init__(self):
        self._config = self.m_doi_config_util.get_config()



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
            exit(1)

        o_out_text = etree.tostring(doc, pretty_print=True)
        logger.debug(f'o_out_text {o_out_text}')
        logger.debug(f'doc {doc}')

        return o_reserved_flag,o_out_text

    def _process_reserve_action_xlsx(self, target_url, publisher_value, contributor_value, write_to_file_flag=True):
        # Function process a reserve action based on .xlsx ending.
        # Get the default configuration from external file.  Location may have to be absolute.
        xml_config_file = os.path.join('.','config','default_config.xml')
        logger.debug(f"xml_config_file {xml_config_file}")
        (dict_configlist, dict_fixedlist) = self.m_doi_config_util.get_config_file_metadata(xml_config_file)

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            app_base_path = os.path.abspath(os.path.curdir)
            dict_condition_data = {}

            dict_condition_data = self.m_doi_input_util.parse_sxls_file(app_base_path,
                                                                        target_url,
                                                                        dict_fixedlist,
                                                                        dict_configlist,
                                                                        dict_condition_data)

            (o_aggregated_tree,o_aggregated_filename,o_created_filelist) = self.m_doi_output_util.aggregate_reserve_osti_doi_from_dict(dict_configlist,dict_fixedlist,doi_directory_pathname,dict_condition_data,write_to_file_flag)

            o_doi_label = etree.tostring(o_aggregated_tree) 
            o_aggregated_DOI_content = o_doi_label.decode()
            o_num_files_created = len(o_created_filelist)
            logger.debug(f"o_num_files_created {o_num_files_created}")
            logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")
        except InputFormatException as e:
            logger.error(e)
            exit(1)

        return (o_num_files_created,etree.tostring(o_aggregated_tree))

    def _process_reserve_action_csv(self, target_url, publisher_value, contributor_value, write_to_file_flag=True):
        # Function process a reserve action based on .csv ending.

        # Get the default configuration from external file.  Location may have to be absolute.
        xml_config_file = os.path.join('.','config','default_config.xml')

        (dict_configlist, dict_fixedlist) = self.m_doi_config_util.get_config_file_metadata(xml_config_file)


        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            app_base_path = os.path.abspath(os.path.curdir)
            dict_condition_data = {}

            dict_condition_data = self.m_doi_input_util.parse_csv_file(app_base_path,
                                                                       target_url,
                                                                       dict_fixedlist,
                                                                       dict_configlist,
                                                                       dict_condition_data)

            (o_aggregated_tree,o_aggregated_filename,o_created_filelist) = self.m_doi_output_util.aggregate_reserve_osti_doi_from_dict(dict_configlist,dict_fixedlist,doi_directory_pathname,dict_condition_data,write_to_file_flag)

            o_doi_label = etree.tostring(o_aggregated_tree)  # The content of o_doi_label is now a series of bytes.
            o_aggregated_DOI_content = o_doi_label.decode()  # The content of o_aggregated_DOI_content is now text.
            o_num_files_created = len(o_created_filelist)
            logger.debug(f"o_num_files_created {o_num_files_created}")
            logger.debug(f"o_aggregated_DOI_content {o_aggregated_DOI_content}")
        except InputFormatException as e:
            logger.error(e)
            exit(1)

        return (o_num_files_created,etree.tostring(o_aggregated_tree))

    def reserve_doi_label(self, target_url, publisher_value, contributor_value, submit_label_flag=True, write_to_file_flag=True):
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
            (o_num_files_created, o_aggregated_DOI_content) = self._process_reserve_action_xlsx(target_url, publisher_value, contributor_value, write_to_file_flag)
            o_doi_label = o_aggregated_DOI_content

        elif target_url.endswith('.csv'):
            (o_num_files_created, o_aggregated_DOI_content) = self._process_reserve_action_csv(target_url, publisher_value, contributor_value, write_to_file_flag)
            o_doi_label = o_aggregated_DOI_content

        # Check to see if the given file has an attempt to process.
        else:
            logger.error(f"File type has not been implemented:target_url {target_url}")
            exit(1)

        (o_reserved_flag, o_out_text) = self._verify_osti_reserved_status(o_doi_label)

        # We can submit the content to OSTI if we wish.
        logger.debug(f"submit_label_flag {submit_label_flag}")
        if submit_label_flag:
            from pds_doi_core.cmd.pds_doi_client import DOIWebClient
            doi_web_client = DOIWebClient()
            doi_web_client.webclient_submit_existing_content(o_doi_label)

        # At this point, the o_out_text would contain tag "status = 'Reserved'" in each record tags.
        print("reserve_doi_label:","o_doi_label",o_doi_label)
        print("reserve_doi_label:","o_out_text",o_out_text)
        #exit(0)
        return o_out_text

    def create_doi_label(self, target_url, contributor_value):
        """
        Function receives a URI containing either XML or a local file and draft a Data Object Identifier (DOI).  
        :param target_url:
        :param contributor_value:
        :return: o_doi_label:
        """
        # check contributor
        doi_contributor_util = DOIContributorUtil(self._config.get('PDS4_DICTIONARY', 'url'),
                                                  self._config.get('PDS4_DICTIONARY', 'pds_node_identifier'))
        o_permissible_contributor_list = doi_contributor_util.get_permissible_values()
        if contributor_value not in o_permissible_contributor_list:
            logger.error(f"The value of given contributor is not valid: {contributor_value}")
            logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")
            exit(1)

        # parse input
        if not target_url.startswith('http'):
            xml_tree = etree.parse(target_url)
        else:
            response = requests.get(target_url)
            xml_tree = etree.fromstring(response.content)

        doi_fields = self.m_doi_pds4_label.get_doi_fields_from_pds4(xml_tree)
        doi_fields['publisher'] = self._config.get('OTHER', 'doi_publisher')
        doi_fields['contributor'] = contributor_value

        # generate output
        return create_osti_doi_record(doi_fields)


def main():
    parser = create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.action
    contributor_value = arguments.contributor.lstrip().rstrip()  # Remove any leading and trailing blanks.
    input_location = arguments.input

    logger.info(f"run_dir {os.getcwd()}")
    logger.info(f"publisher_value {DOI_CORE_CONST_PUBLISHER_VALUE}")
    logger.info(f"input_location {input_location}")
    logger.info(f"contributor_value['{contributor_value}']")

    doi_core_services = DOICoreServices()

    if action_type == 'draft':
        o_doi_label = doi_core_services.create_doi_label(input_location, contributor_value)
        logger.info(o_doi_label)

    elif action_type == 'reserve':
        o_doi_label = doi_core_services.reserve_doi_label(input_location, DOI_CORE_CONST_PUBLISHER_VALUE,
                                                        contributor_value, submit_label_flag=True)
        # By default, submit_label_flag=True if not specified.
        # By default, write_to_file_flag=True if not specified.
        logger.info(o_doi_label.decode())
    else:
        logger.error(f"Action {action_type} is not supported yet.")
        exit(1)


if __name__ == '__main__':
    main()
