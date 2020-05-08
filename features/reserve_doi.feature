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

