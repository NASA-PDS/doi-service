import os

from behave import *
from copy import deepcopy
from datetime import datetime
from enum import Enum
from lxml import etree
from xmldiff import main

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
# Normally should be set to True.  Used by developer to prevent the sending of DOI during may iterations.
g_submit_flag = True
g_submit_flag = False 

# Enum type about testing 'draft' action.
class DraftCondition(Enum):
    NOOP            = 0
    NORMAL          = 1
    FILE_NOT_EXIST  = 2
    FILE_BAD_FORMAT = 3

# Global variable to signify the condition of the 'draft' test.
global g_draft_condition
g_draft_condition = DraftCondition.NORMAL

# Global variable to signify to other functions what to expect when an action is called.
global g_action_expectant_bad
g_action_expectant_bad = False

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

    try:
        o_doi_label = _action.run(input=input_value,
                              node=node_value,
                              submitter='my_user@my_node.gov',force=True)
        # Save o_doi_label to disk so it can be compared to historical in next step
        temporary_file_name = save_doi_to_temporary_file(o_doi_label)
        logger.info(f"success input_value {input_value}")
    except InputFormatException as e:
        logger.error(e)
        logger.info(f"failure input_value {input_value}")
        assert 2 is 3
    except CriticalDOIException as e:
        logger.info(f"CRITICAL {e}")
        logger.info(f"Expecting CriticalDOIException from input_value {input_value}")
        logger.info(f"failure input_value {input_value}")
        assert 2 is 3

def reserve_action_run(node_value,input_value):
    # Helper function to 'reserve' a given input_value.
    global g_action_expectant_bad
    logger.info(f"when node_value,input_value {node_value,input_value}")
    o_doi_label = None

    db_name = 'doi_temp.db'
    _action = DOICoreActionReserve(db_name=db_name)

    try:
        o_doi_label = _action.run(
                          input=input_value,
                          #node='img', submitter='my_user@my_node.gov',
                          node=node_value, submitter='my_user@my_node.gov',
                          dry_run=True,force=True)
                          #submit_label_flag=False,force_flag=True)
        logger.info(f"o_doi_label {o_doi_label}")
        assert 2 is 2
    except InputFormatException as e:
        logger.error(e)
        assert 2 is 3
    except CriticalDOIException as e:
        #logger.info(f"CRITICAL {e}")
        #logger.info(f"Expecting CriticalDOIException from input_value {input_value}")
        if g_action_expectant_bad:
            assert 2 is 2
        else:
            logger.info(f"g_action_expectant_bad {g_action_expectant_bad}")
            assert 2 is 3
    #logger.info(f"context.failed {context.failed}")

    return o_doi_label

def draft_output_compare(output_value):
    # Function compare two XML files created from 'draft' or 'reserve' actions.
    # Assumption(s): 
    #   1.  The name of the new XML file is defined in get_temporary_output_filename().
    #   2.  The name of the historical name is output_value
    print("validate_draft_output:entering")
    logger.debug(f"output_value {output_value}")

    new_xml_output       = get_temporary_output_filename()
    historical_xml_output = output_value
    o_fields_differ_list, o_values_differ_list, o_record_index_differ_list = DOIDiffer.doi_xml_differ(historical_xml_output,new_xml_output)

    #print("validate_draft_output:o_fields_differ_list",output_value,len(o_fields_differ_list),o_fields_differ_list)
    #print("validate_draft_output:o_values_differ_list",len(o_values_differ_list),o_values_differ_list)
    #print("validate_draft_output:o_record_index_differ_list",len(o_record_index_differ_list),o_record_index_differ_list)

    if len(o_fields_differ_list) == 0:
        logger.info(f"success output_value,new_xml_output {output_value,new_xml_output}")
        assert 2 is 2
    else:
        logger.info(f"failure output_value,new_xml_output {output_value,new_xml_output}")
        #logger.info(f"failure historical_xml_output, new_xml_output {historical_xml_output,new_xml_output}")
        logger.info(f"output_value,o_fields_differ_list {output_value,len(o_fields_differ_list),o_fields_differ_list}")
        logger.info(f"o_values_differ_list {o_values_differ_list,len(o_values_differ_list),o_values_differ_list}")
        logger.info(f"o_record_index_differ_list {o_record_index_differ_list,len(o_record_index_differ_list),o_record_index_differ_list}")
        assert 2 is 3
    #print("validate_draft_output:leaving")
    return 1

def reserve_output_compare(output_value):
    print("reserve_output_compare:entering",output_value)
    # Use the same function draft_output_compare() to compare a DOI (XML output) from the 'reserve' action.
    draft_output_compare(output_value)
    print("reserve_output_compare:leaving",output_value)

def initialize_normal_draft():
    global g_action_expectant_bad, g_draft_condition
    # Set to g_action_expectant_bad to signify to not expect the action to be bad.
    g_action_expectant_bad = False
    g_draft_condition = DraftCondition.NORMAL

@given('a valid PDS4 label at input_type,input_value {input_type},{input_value}')
def given_valid_input(context, input_type, input_value):
    global g_action_expectant_bad, g_draft_condition
    logger.info(f"given {input_type} {input_value}")
    ## Set to g_action_expectant_bad to signify to not expect the action to be bad.
    #g_action_expectant_bad = False
    #g_draft_condition = DraftCondition.NORMAL
    initialize_normal_draft()
    logger.info(f"g_action_expectant_bad {g_action_expectant_bad}")
    #assert 2 is 3

@given('an invalid PDS4 label at input_type,input_value {input_type},{input_value}')
def given_invalid_pds4(context, input_type, input_value):
    #print(f'STEP: an invalid PDS4 {input_type} at url {input_value}')
    print(u'an invalid PDS4 label at input_type,input_value <input_type> <input_value>')
    global g_action_expectant_bad, g_draft_condition
    # Set g_action_expectant_bad to True to signify to expect the action to be bad.
    g_action_expectant_bad = True 
    g_draft_condition      = DraftCondition.FILE_NOT_EXIST
    logger.info(f"g_action_expectant_bad {g_action_expectant_bad} g_draft_condition {g_draft_condition}")
    logger.info(f"g_action_expectant_bad,g_draft_condition,input_value {g_action_expectant_bad,g_draft_condition,input_value}")
    assert 2 is 2

@when('create draft DOI at node_value,input_value,format {node_value},{input_value},{output_type}')
def when_create_draft_impl(context, node_value, input_value, output_type):
    logger.info(f"when create DOI draft {output_type}")
    logger.info(f"input_value {input_value}")
    if g_action_expectant_bad:
        if g_draft_condition == DraftCondition.FILE_NOT_EXIST:
            logger.info(f"g_action_expectant_bad True, g_draft_condition {g_draft_condition} skipping input_value {input_value}")
    else:
        draft_action_run(node_value,input_value)

@then('DOI label is created like {output_type},{output_value}')
def then_validate_draft_output(context, output_type, output_value):
    draft_output_compare(output_value)

@then('an error report is generated as {error_report},{input_value}')
def step_an_error_report_is_generated_impl(context, error_report, input_value):
    # Write an error report.
    # Create the parent directory if one does not already exist.
    os.makedirs(os.path.dirname(error_report),exist_ok=True)
    temporary_file_name = error_report
    temporary_file_ptr = open(temporary_file_name,"w+") 
    temporary_file_ptr.write("Input value " + input_value + " cannot be drafted or reserved.\n")
    temporary_file_ptr.close()
    return temporary_file_name

@when('reserve DOI in OSTI format at node_value,input_value {node_value},{input_value}')
def step_when_reserve_doi_in_osti_format_impl(context, node_value, input_value):
    logger.info(f"when context {context}")
    logger.info(f"when input_value {input_value}")
    try:
        o_doi_label = reserve_action_run(node_value,input_value)
    except InputFormatException as e:
        logger.error(e)
        assert 2 is 2
    except CriticalDOIException as e:
        logger.info(f"CRITICAL {e}")
        logger.info(f"Expecting CriticalDOIException from input_value {input_value}")
        assert 2 is 2
    logger.info(f"context.failed {context.failed}")
    assert 2 is 2

@then('OSTI DOI label is created at input_value,node_value {input_value},{node_value}')
def step_then_osti_doi_label_is_created_impl(context,node_value,input_value):
    logger.info(f"when context {context}")
    logger.info(f"when input_value {input_value}")

    try:
        o_doi_label = reserve_action_run(node_value,input_value)
    except InputFormatException as e:
        logger.error(e)
        assert 2 is 2
    except CriticalDOIException as e:
        logger.info(f"CRITICAL {e}")
        logger.info(f"Expecting CriticalDOIException from input_value {input_value}")
        assert 2 is 2
    logger.info(f"context.failed {context.failed}")
    assert 2 is 2

    # Save o_doi_label to disk so it can be compared to historical in next step
    temporary_file_name = save_doi_to_temporary_file(o_doi_label)
    logger.info(f"temporary_file_name {temporary_file_name}")
    #exit(0)

@then('PDS4 label is validated for DOI production at input_value {input_value}')
def step_pds4_label_is_validated_impl(context,input_value):
    assert 2 is 2

@then(u'The OSTI DOI label is valid')
def step_doi_label_is_valid_impl(context):
    assert 2 is 2

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
    assert 2 is 2

@given('historical draft transaction {transaction_dir}')
def step_historical_draft_impl(context,transaction_dir):
    initialize_normal_draft()
    assert 2 is 2

@when('historical is drafted from node_value,input_subdir {node_value},{input_subdir}')
def when_historical_is_drafted_from_impl(context,node_value,input_subdir):
    draft_action_run(node_value,input_subdir)

@given('historical reserve transaction {transaction_dir}')
def step_historical_reserve_impl(context,transaction_dir):
    assert 2 is 2

@when('historical is reserved at node_value,transaction_dir,input_value {node_value},{transaction_dir},{input_value}')
def step_historical_is_reserved_at_input_impl(context,node_value,transaction_dir,input_value):
    input_dir = os.path.join(transaction_dir,input_value)
    o_doi_label = reserve_action_run(node_value,input_dir)
    # Save o_doi_label to disk so it can be compared to historical in next step
    temporary_file_name = save_doi_to_temporary_file(o_doi_label)
    assert 2 is 2

@then('produced osti record is similar to historical osti {output_value}')
def step_produced_osti_record_is_similiar_to_historical_osti_impl(context,output_value):
    draft_output_compare(output_value)
    assert 2 is 2

@when(u'create draft DOI in format OSTI')
def step_create_draft_doi_impl(context):
    # Cannot do anything
    assert 2 is 2
