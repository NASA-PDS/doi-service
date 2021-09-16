import os
from behave import *
from copy import deepcopy
from lxml import etree
import tempfile
import uuid


import logging

from pds_doi_service.core.input.exceptions import InputFormatException, CriticalDOIException
from pds_doi_service.core.util.doi_xml_differ import DOIDiffer
from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.outputs.osti.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.util.config_parser import DOIConfigUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag to submit the DOI to OSTI or not after it has been built.
g_submit_flag = True
g_submit_flag = False


def get_temporary_output_filename(extension='xml'):
    return os.path.join(tempfile.gettempdir(), f'{str(uuid.uuid4())}.{extension}')

def save_doi_to_temporary_file(doi_label):
    # Save doi_label to disk so it can be compared to reference in next step.
    temporary_file_name = get_temporary_output_filename()
    with open(temporary_file_name,"w+") as f:
        f.write(doi_label + "\n")
    return temporary_file_name

def replace_lidvid_in_file(input_file, lid, extension='csv'):
    input_value_with_random_lidvid = get_temporary_output_filename(extension=extension)
    with open(input_file, 'r') as f_in:
        with open(input_value_with_random_lidvid, 'w') as f_out:
            for line in f_in.readlines():
                f_out.write(line.replace('{{random_lid}}', lid))
    return input_value_with_random_lidvid

def draft_action_run(node_value,input_value, lid=None):
    # Helper function to 'draft' a given input_value and write the DOI to a temporary file.
    # This file will be available for other validation functions.
    db_name = 'doi_temp.db'
    _action = DOICoreActionDraft(db_name=db_name)
    logger.info(f"input_value {input_value}")

    if lid:
        input_value = replace_lidvid_in_file(input_value, lid, extension='xml')

    o_doi_label = _action.run(input=input_value,
                          node=node_value,
                          submitter='my_user@my_node.gov',force=True)
    # Save o_doi_label to disk so it can be compared to reference in next step
    logger.info(f"success input_value {input_value}")
    return save_doi_to_temporary_file(o_doi_label)


def reserve_action_run(node_value,input_value, lid=None):
    # Helper function to 'reserve' a given input_value.
    logger.info(f"when node_value,input_value {node_value,input_value}")

    db_name = 'doi_temp.db'
    _action = DOICoreActionReserve(db_name=db_name)

    if lid:
        input_value = replace_lidvid_in_file(input_value, lid, extension='csv')

    o_doi_label = _action.run(
                      input=input_value,
                      node=node_value, submitter='my_user@my_node.gov',
                      dry_run=True, force=True)

    return save_doi_to_temporary_file(o_doi_label)


def release_action_run(node_value, input_value):
    try:
        db_name = 'doi_temp.db'
        release_action = DOICoreActionRelease(db_name=db_name)
        released_doi_str = release_action.run(input=input_value, node=node_value,
                                              submitter='my_user@my_node.gov', force=True)
        return save_doi_to_temporary_file(released_doi_str)
    except Exception as e:
        raise


def file_output_compare(output_file, ref_output_value):
    # Function compare two XML files created from 'draft' or 'reserve' actions.
    # Assumption(s):
    #   1.  The name of the new XML file is defined in get_temporary_output_filename().
    #   2.  The name of the reference name is ref_output_value
    logger.info(f"output_file,ref_output_value {output_file},{ref_output_value}")

    o_fields_differ_list, o_values_differ_list, o_record_index_differ_list = DOIDiffer.doi_xml_differ(ref_output_value,
                                                                                                      output_file)

    logger.info(f'different fields are {o_fields_differ_list}')
    logger.info(f'o_fields_differ_list {o_fields_differ_list}')
    logger.info(f'o_values_differ_list {o_values_differ_list}')
    logger.info(f'o_record_index_differ_list {o_record_index_differ_list}')

    assert len(o_fields_differ_list) is 0

    return 1

@given('a valid input at {input_value}')
def given_valid_action_input(context, input_value):
    logger.info(f"given {input_value}")
    context.input_value = input_value  # Don't forget to set the input_value in context to be available for other functions.

@given('an invalid PDS4 label at {input_value}')
def given_invalid_pds4(context, input_value):
    logger.info(f'an invalid reserve PDS4 label at input_value {input_value}')
    context.input_value = input_value  # Don't forget to set the input_value in context to be available for other functions.

@given('random new lid')
def given_random_new_lid(context):
    context.random_lid = f'urn:nasa:pds:{uuid.uuid4()}'

@when('create draft DOI for node {node_value}')
def when_create_draft_impl(context, node_value):
    logger.info(f"when create DOI draft ")
    logger.info(f"input_value {context.input_value}")

    try:
        if not hasattr(context, 'output_files'):
            context.output_files = []
        new_draft_output = draft_action_run(node_value,
                                            context.input_value,
                                            lid=context.random_lid if hasattr(context, 'random_lid') else None)
        context.output_files.append(new_draft_output)

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
        if not hasattr(context, 'output_files'):
            context.output_files = []
        new_reserve_file = reserve_action_run(node_value,input_value)
        context.output_files.append(new_reserve_file)
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

@then('OSTI DOI label is created from {input_value} for node {node_value}')
def step_then_osti_doi_label_is_created_impl(context,node_value,input_value):
    logger.info(f"when context {context}")
    logger.info(f"when input_value {input_value}")

    try:
        if not hasattr(context, 'output_files'):
            context.output_files = []
        reserve_ouput_file = reserve_action_run(node_value,
                                                input_value,
                                                lid=context.random_lid if hasattr(context, 'random_lid') else None)
        context.output_files.append(reserve_ouput_file)
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

    # Fetch the content of payload_filename into memory and change the status from status="reserved_not_submitted"
    # to status="Reserved".
    payload_doc = etree.parse(context.output_files[0])
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
        doi, response_str = DOIOstiWebClient().submit_content(
            payload=etree.tostring(out_root)
        )
    else:
        logger.info(f"g_submit_flag is False")

@when('reference record is drafted for node {node_value} from {input_subdir}')
def when_reference_is_drafted_from_impl(context, node_value, input_subdir):
    input_dir = os.path.join(context.transaction_dir, input_subdir)
    if not hasattr(context, 'output_files'):
        context.output_files = []
    new_draft_file = draft_action_run(node_value,
                                      input_dir,
                                      lid=context.random_lid if hasattr(context, 'random_lid') else None)
    context.output_files.append(new_draft_file)

@given('reference transactions in {transaction_dir}')
def given_reference_dir_impl(context,transaction_dir):
    context.transaction_dir = transaction_dir

@when('reference record is reserved for node {node_value} with {input_value}')
def step_reference_is_reserved_at_input_impl(context, node_value, input_value):
    transaction_dir = context.transaction_dir
    input_dir = os.path.join(transaction_dir,input_value)
    if not hasattr(context, 'output_files'):
        context.output_files = []
    context.output_files.append(reserve_action_run(node_value,input_dir,
                                                   lid=context.random_lid if hasattr(context, 'random_lid') else None))

@then('produced osti record is similar to reference osti {ref_output_value}')
def step_produced_osti_record_is_similiar_to_reference_osti_impl(context, ref_output_value):
    if hasattr(context, 'transaction_dir'):
        ref_output_value = os.path.join(context.transaction_dir, ref_output_value)
        logger.info(f"context.transaction_dir {context.transaction_dir}")
    logger.info(f"context.output_files {context.output_files}")
    logger.info(f"ref_output_value {ref_output_value}")
    file_output_compare(context.output_files[0], ref_output_value)


@when('submit osti record for {node_value}')
def submit_osti_record(context, node_value):
    try:
        context.output_files[-1] = release_action_run(node_value, context.output_files[-1])
        logger.info(f'record in file {context.output_files[-1]} submitted from output index {len(context.output_files)}')
    except CriticalDOIException as e:
        context.exception_msg = str(e)

@then('lidvid already submitted exception is raised')
def step_lidvid_already_submitted_exception_is_raised(context):
    assert hasattr(context, 'exception_msg')
    logger.info(f'grab first created doi from file {context.output_files}')
    reserved_xml = etree.parse(context.output_files[0])
    reserved_doi = reserved_xml.xpath('/records/record/doi')[0].text

    excepted_exception_msg = f'There is already a DOI {reserved_doi} submitted for this lidvid {context.random_lid}::1.0 (status=Pending). You cannot submit a new DOI for the same lidvid.'
    logger.info(f'expected message {excepted_exception_msg}')
    logger.info(f'found msg is {context.exception_msg}')
    assert context.exception_msg == excepted_exception_msg
