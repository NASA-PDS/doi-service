from behave import *
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@given('a valid PDS4 {input_type} at url {input_value}')
def given_valid_input(context, input_type, input_value):
    logger.info(f"given {input_type} {input_value}")


@when(u'create draft DOI in {output_type} format')
def when_create_draft_impl(context, output_type):
    logger.info(f"when create DOI draft {output_type}")


@then(u'PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml label is validated for DOI production')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml label is validated for DOI production')


@then(u'OSTI DOI label is created like tests/data/valid_bundle_doi.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then OSTI DOI label is created like tests/data/valid_bundle_doi.xml')


@then(u'The OSTI DOI label is valid')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then The OSTI DOI label is valid')


@then(u'PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml label is validated for DOI production')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml label is validated for DOI production')


@then(u'OSTI DOI label is created like tests/data/valid_datacoll_doi.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then OSTI DOI label is created like tests/data/valid_datacoll_doi.xml')


@then(u'PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml label is validated for DOI production')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml label is validated for DOI production')


@then(u'OSTI DOI label is created like tests/data/valid_browsecoll_doi.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then OSTI DOI label is created like tests/data/valid_browsecoll_doi.xml')


@then(u'PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml label is validated for DOI production')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml label is validated for DOI production')


@then(u'OSTI DOI label is created like tests/data/valid_calibcoll_doi.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then OSTI DOI label is created like tests/data/valid_calibcoll_doi.xml')


@then(u'PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml label is validated for DOI production')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then PDS4 https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml label is validated for DOI production')


@then(u'OSTI DOI label is created like tests/data/valid_docucoll_doi.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then OSTI DOI label is created like tests/data/valid_docucoll_doi.xml')


@given(u'an invalid PDS4 bundle at tests/data/invalid_bundle.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given an invalid PDS4 bundle at tests/data/invalid_bundle.xml')


@then(u'an error report is generated as tests/data/error_report.txt')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then an error report is generated as tests/data/error_report.txt')


@when(u'reserve DOI in OSTI format')
def step_impl(context):
    raise NotImplementedError(u'STEP: When reserve DOI in OSTI format')


@then(u'OSTI DOI label is created')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then OSTI DOI label is created')


@then(u'The OSTI DOI is submitted to the OSTI server')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then The OSTI DOI is submitted to the OSTI server')


@given(u'an invalid PDS4 bundle label at url tests/data/invalid_bundle.xml')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given an invalid PDS4 bundle label at url tests/data/invalid_bundle.xml')


@then(u'an error report is generated')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then an error report is generated')

