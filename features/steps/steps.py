from behave import *
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@given('a valid PDS4 {input_type} at url {input_value}')
def given_valid_input(context, input_type, input_value):
    logger.info(f"given {input_type} {input_value}")


@given('an invalid PDS4 {input_type} at {input_value}')
def given_invalid_pds4(context, input_type, input_value):
    raise NotImplementedError(
        u'STEP: an invalid PDS4 {input_type} at {input_value}')


@when(u'create draft DOI in {output_type} format')
def when_create_draft_impl(context, output_type):
    logger.info(f"when create DOI draft {output_type}")


@then(u'{output_type} DOI label is created like {output_value}')
def then_validate_draft_output(context, output_type, output_value):
    raise NotImplementedError(
        u'{output_type} DOI label is created like {output_value}')


@then(u'an error report is generated as {error_report}')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then an error report is generated')

