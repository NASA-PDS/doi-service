import os
import sys
from behave import *
from copy import deepcopy
from datetime import datetime
from enum import Enum
from lxml import etree
from io import StringIO

import logging

from pds_doi_core.input.exceptions import DuplicatedTitleDOIException, TitleDoesNotMatchProductTypeException, \
    UnexpectedDOIActionException, InputFormatException, WarningDOIException, CriticalDOIException
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.util.doi_xml_differ import DOIDiffer
from pds_doi_core.actions.draft import DOICoreActionDraft
from pds_doi_core.actions.reserve import DOICoreActionReserve
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_core.util.config_parser import DOIConfigUtil

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global flag to submit the DOI to OSTI or not after it has been built.
g_submit_flag = True
g_submit_flag = False 

def get_temporary_output_filename():
    return 'temp_doi_label.xml'

def save_doi_to_temporary_file(doi_label):
    # Save doi_label to disk so it can be compared to historical in next step.
    temporary_file_name = get_temporary_output_filename()
    temporary_file_ptr = open(temporary_file_name,"w+") 
    temporary_file_ptr.write(doi_label + "\n")
    temporary_file_ptr.close()
    return temporary_file_name

def draft_action_run(node_value,input_value):
    # Helper function to 'draft' a given input_value and write the DOI to a temporary file.
    # This file will be available for other validation functions.
    db_name = 'doi_temp.db'
    _action = DOICoreActionDraft(db_name=db_name)
    logger.info(f"input_value {input_value}")

    o_doi_label = _action.run(input=input_value,
                          node=node_value,
                          submitter='my_user@my_node.gov',force=True)
    # Save o_doi_label to disk so it can be compared to historical in next step
    logger.info(f"success input_value {input_value}")
    return save_doi_to_temporary_file(o_doi_label)

def reserve_action_run(node_value,input_value):
    # Helper function to 'reserve' a given input_value.
    logger.info(f"when node_value,input_value {node_value,input_value}")
    o_doi_label = None

    db_name = 'doi_temp.db'
    _action = DOICoreActionReserve(db_name=db_name)

    o_doi_label = _action.run(
                      input=input_value,
                      node=node_value, submitter='my_user@my_node.gov',
                      dry_run=True,force=True)

    return save_doi_to_temporary_file(o_doi_label)

def file_output_compare(output_file, ref_output_value):
    # Function compare two XML files created from 'draft' or 'reserve' actions.
    # Assumption(s): 
    #   1.  The name of the new XML file is defined in get_temporary_output_filename().
    #   2.  The name of the historical name is ref_output_value
    logger.info(f"output_file,ref_output_value {output_file},{ref_output_value}")

    o_fields_differ_list, o_values_differ_list, o_record_index_differ_list = DOIDiffer.doi_xml_differ(ref_output_value,
                                                                                                      output_file)


    logger.info(f'different fields are {o_fields_differ_list}')
    logger.info(f'o_fields_differ_list {o_fields_differ_list}')
    logger.info(f'o_values_differ_list {o_values_differ_list}')
    logger.info(f'o_record_index_differ_list {o_record_index_differ_list}')

    assert len(o_fields_differ_list) is 0

    return 1

def reserve_output_compare(output_file, ref_output_value):
    logger.info(f"output_file,ref_output_value {output_file},{ref_output_value}")
    # Use the same function file_output_compare() to compare a DOI (XML output) from the 'reserve' action.
    file_output_compare(output_file,ref_output_value)

@given('a valid PDS4 label at {input_value}')
def given_valid_action_input(context, input_value):
    logger.info(f"given {input_value}")
    context.input_value = input_value  # Don't forget to set the input_value in context to be available for other functions.

@given('an invalid PDS4 label at input_type,input_value {input_type},{input_value}')
def given_invalid_pds4(context, input_type, input_value):
    logger.info(f'an invalid PDS4 label at input_type,input_value {input_type},{input_value}')

@given('an invalid reserve PDS4 label at input_value {input_value}')
def given_invalid_reserve_pds4(context, input_value):
    logger.info(f'an invalid reserve PDS4 label at input_value {input_value}')
    context.input_value = input_value  # Don't forget to set the input_value in context to be available for other functions.

@when('create draft DOI for node {node_value} from {input_value}')
def when_create_draft_impl(context, node_value, input_value):
    logger.info(f"when create DOI draft ")
    logger.info(f"input_value {input_value}")

    try:
        context.output_file = draft_action_run(node_value,input_value)

    except CriticalDOIException as e:
        logger.info(str(e))
        context.exception_msg = str(e)

@then('a reading error report is generated for {input_value}')
def step_an_error_report_is_generated_impl(context, input_value):

    assert hasattr(context, 'exception_msg')
    assert context.exception_msg == f'Error reading file {input_value}'

@when('reserve DOI in OSTI format at {node_value}')
def step_when_reserve_doi_in_osti_format_impl(context, node_value):
    input_value = context.input_value
    logger.info(f"when context {context}")
    logger.info(f"when input_value {input_value}")
    try:
        context.output_file = reserve_action_run(node_value,input_value)
    except InputFormatException as e:
        # Save the error message to context.exception_msg so the function step_an_error_report_is_generated_impl has something to check
        logger.info(f"Expecting InputFormatException from input_value {input_value}")
        context.exception_msg = str(e)
        logger.error(e)
    except CriticalDOIException as e:
        logger.info(f"CRITICAL {e}")
        logger.info(f"Expecting CriticalDOIException from input_value {input_value}")
        logger.info(str(e))
        # Save the error message to context.exception_msg so the function step_an_error_report_is_generated_impl has something to check
        context.exception_msg = str(e)
    logger.info(f"context.failed {context.failed}")

@then('OSTI DOI label is created at input_value,node_value {input_value},{node_value}')
def step_then_osti_doi_label_is_created_impl(context,node_value,input_value):
    logger.info(f"when context {context}")
    logger.info(f"when input_value {input_value}")

    try:
        context.output_file = reserve_action_run(node_value,input_value)
    except InputFormatException as e:
        logger.error(e)
    except CriticalDOIException as e:
        logger.info(f"CRITICAL {e}")
        logger.info(f"Expecting CriticalDOIException from input_value {input_value}")
    logger.info(f"context.failed {context.failed}")

@then(u'The OSTI DOI is submitted to the OSTI server')
def step_doi_label_is_submitted_impl(context):
    doi_config_util = DOIConfigUtil()
    m_config = doi_config_util.get_config()

    payload_filename = get_temporary_output_filename()

    # Fetch the content of payload_filename into memory and change the status from status="reserved_not_submitted"
    # to status="Reserved".

    payload_doc = etree.parse(payload_filename)
    payload_root = payload_doc.getroot()

    # Make a new root with modified 'status' attribute to 'Reserved'
    out_root = etree.Element("records")
    for element in payload_root.iter():
        if element.tag == 'record':
            new_element = deepcopy(element)
            new_element.attrib['status'] = 'Reserved'
            out_root.append(new_element)
    etree.indent(out_root,space="    ")

    # The payload is now ready to be submitted to OSTI.
    if g_submit_flag:
        (dois, response_str) = DOIOstiWebClient().webclient_submit_existing_content(etree.tostring(out_root),
                                   i_url=m_config.get('OSTI', 'url'),
                                   i_username=m_config.get('OSTI','user'),
                                   i_password=m_config.get('OSTI','password'))
    else:
        logger.info(f"g_submit_flag is False")

@when('historical is drafted for node {node_value} from {input_subdir}')
def when_historical_is_drafted_from_impl(context,node_value,input_subdir):
    input_dir = os.path.join(context.transaction_dir, input_subdir)
    context.output_file = draft_action_run(node_value, input_dir)

@given('historical transaction {transaction_dir}')
def step_historical_impl(context,transaction_dir):
    context.transaction_dir = transaction_dir

@when('historical is reserved with node {node_value} with {input_value}')
def step_historical_is_reserved_at_input_impl(context,node_value,input_value):
    transaction_dir = context.transaction_dir
    input_dir = os.path.join(transaction_dir,input_value)
    context.output_file = reserve_action_run(node_value,input_dir)

@then('produced osti record is similar to reference osti {ref_output_value}')
def step_produced_osti_record_is_similiar_to_reference_osti_impl(context,ref_output_value):
    if hasattr(context, 'transaction_dir'):
        ref_output_value = os.path.join(context.transaction_dir, ref_output_value)
        logger.info(f"context.transaction_dir {context.transaction_dir}")
    logger.info(f"context.output_file {context.output_file}")
    logger.info(f"ref_output_value {ref_output_value}")
    reserve_output_compare(context.output_file, ref_output_value)
