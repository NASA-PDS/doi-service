Feature: reserve a OSTI DOI
  @non-regression
  Scenario Outline: Reserve an OSTI DOI
    # The given for 'reserve' action cannot be shared with 'draft' action as they required different setup.
    Given a valid reserve PDS4 label at input_type,input_value <input_type>,<input_value>
    When reserve DOI in OSTI format at node_value,input_value <node_value>,<input_value>
    Then PDS4 label is validated for DOI production at input_value <input_value>
    Then OSTI DOI label is created at input_value,node_value <input_value>,<node_value>
    Then The OSTI DOI label is valid
    Then The OSTI DOI is submitted to the OSTI server
    Examples: Valid PDS4 labels
      | input_type   | node_value | input_value                       |
      | bundle       | img        | input/DOI_Reserved_GEO_200318.csv |


  Scenario Outline: an invalid PDS4 is submitted for <input_type>
    # The given for 'reserve' action cannot be shared with 'draft' action as they required different setup.
    Given an invalid reserve PDS4 label at input_type,input_value <input_type>,<input_value>
    When reserve DOI in OSTI format at node_value,input_value <node_value>,<input_value>
    # Use the same 'then' as 'draft' to share function.
    Then a reading error report is generated for <input_value> 
    Examples: Invalid PDS4 labels
      | input_type   | node_value | input_value                   | error_report  |
      | bundle       | img        | tests/data/invalid_bundle.xml | tests/data/reserve_error_report.txt |

  Scenario Outline: Software results match historical reserve transactions <transaction_dir>
    Given historical reserve transaction <transaction_dir>
    When historical is reserved at node_value,transaction_dir,input_value <node_value>,<transaction_dir>,<input_value>
    Then produced osti record is similar to historical osti <output_value>

    Examples: historical reserve transactions
      | transaction_dir                       |node_value | input_value                                                            | output_value |
      | input/ATMOS_reserve_Insight_Bundle_20200624 |atm        | aaaSubmitted_by_ATMOS_reserve_2020624/DOI_Requests_ATM-2020-06-30.xlsx | outputs/ATMOS_reserve_Insight_Bundle_20200624/aaaSubmitted_by_ATMOS_reserve_2020624/DOI_reserved_all_records.xml |
