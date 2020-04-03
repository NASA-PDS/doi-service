Feature: create a draft OSTI DOI

  @non-regression
  Scenario Outline: Create a draft <output_type> DOI from a valid PDS4 <input_value> label
    Given a valid PDS4 <input_type> label at url <input_value>
    When create draft DOI in <output_type> format
    Then PDS4 <input_value> label is validated for DOI production
    Then <output_type> DOI label is created like <output_value>
    Then The <output_type> DOI label is valid

    Examples: Valid PDS4 labels
      | input_type             | input_value                                                                                               | output_type | output_value                        |
      | bundle                 | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml                             | OSTI        | tests/data/valid_bundle_doi.xml     |
      | data collection        | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml               | OSTI        | tests/data/valid_datacoll_doi.xml   |
      | browse collection      | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml           | OSTI        | tests/data/valid_browsecoll_doi.xml |
      | calibration collection | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml | OSTI        | tests/data/valid_calibcoll_doi.xml  |
      | document collection    | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml       | OSTI        | tests/data/valid_docucoll_doi.xml   |


  Scenario Outline: an invalid PDS4 <input_type> is submitted for <output_type> DOI draft
    Given an invalid PDS4 <input_type> at <input_value>
    When create draft DOI in <output_type> format
    Then an error report is generated as <error_report>

    Examples: Invalid PDS4 labels
      | input_type | input_value                   | output_type | error_report                |
      | bundle     | tests/data/invalid_bundle.xml | OSTI        | tests/data/error_report.txt |






