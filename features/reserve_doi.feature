Feature: reserve a OSTI DOI
  @non-regression
  Scenario Outline: Reserve an OSTI DOI
    Given a valid PDS4 <input_type> label at url <url>
    When reserve DOI in OSTI format
    Then PDS4 <url> label is validated for DOI production
    Then OSTI DOI label is created
    Then The OSTI DOI label is valid
    Then The OSTI DOI is submitted to the OSTI server
    Examples: Valid PDS4 labels
      | input_type             | url                                                                                               |
      | bundle                 | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml                             |
      | data collection        | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml               |


  Scenario Outline: an invalid PDS4 <input_type> is submitted
    Given an invalid PDS4 <input_type> label at url <url>
    When reserve DOI in OSTI format
    Then an error report is generated
    Examples: Invalid PDS4 labels
      | input_type   | url                     |
      | bundle | tests/data/invalid_bundle.xml |

  Scenario Outline: Software results match historical reserve transactions <transaction_dir>
    Given historical transaction <transaction_dir>
    When historical <input> is reserved
    Then producted osti record is similar to historical osti <output_subdir>

    Examples: historical reserve transactions
      | transaction_dir                       | input                                                                  | output_subdir
      | ATMOS_reserve_Insight_Bundle_20200624 | aaaSubmitted_by_ATMOS_reserve_2020624/DOI_Requests_ATM-2020-06-30.xlsx | aaRegistered_by_EN


