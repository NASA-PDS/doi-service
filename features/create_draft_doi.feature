Feature: create a draft OSTI DOI

  @non-regression
  Scenario Outline: Create a draft DOI from a valid PDS4 label <output_type>,<input_value>
    Given a valid PDS4 label at input_type,input_value <input_type>,<input_value>
    When create draft DOI at node_value,input_value,format <node_value>,<input_value>,<output_type>
    Then DOI label is created like <output_type>,<output_value>

    Examples: Valid PDS4 labels
      | input_type             | node_value |input_value                                                                                 | output_type | output_value                        |
      | bundle                 | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml                             | OSTI        | tests/data/valid_bundle_doi.xml     |
      | data collection        | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml               | OSTI        | tests/data/valid_datacoll_doi.xml   |
      | browse collection      | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml           | OSTI        | tests/data/valid_browsecoll_doi.xml |
      | calibration collection | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml | OSTI        | tests/data/valid_calibcoll_doi.xml  |
      | document collection    | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml       | OSTI        | tests/data/valid_docucoll_doi.xml   |


  Scenario Outline: an invalid PDS4 is submitted for DOI draft input_type,output_type <input_type>,<output_type>
    Given an invalid PDS4 label at input_type,input_value <input_type>,<input_value>
    When create draft DOI at node_value,input_value,format <node_value>,<input_value>,<output_type>
    Then an error report is generated as <error_report>,<input_value>

    Examples: Invalid PDS4 labels
      | input_type |node_value | input_value                   | output_type | error_report                      |
      | bundle     |img        | tests/data/invalid_bundle.xml | OSTI        | tests/data/draft_error_report.txt |



  Scenario Outline: Software results match historical draft transactions <transaction_dir>
    Given historical draft transaction <transaction_dir>
    When historical is drafted from node_value,input_subdir <node_value>,<input_subdir>
    Then produced osti record is similar to historical osti <output_value>

    Examples: historical draft transactions
      | transaction_dir                 | node_value | input_subdir                                                         | output_value |
      | ATMOS_mpf_irtf_Bundles_20200414 | atm        | ATMOS_mpf_irtf_Bundles_20200414/aaaSubmitted_by_ATMOS_active_2020414 | ATMOS_mpf_irtf_Bundles_20200414/aaaRegistered_by_EN_active_20200330/DOI_registered_all_records.xml |
