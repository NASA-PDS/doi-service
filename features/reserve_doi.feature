Feature: reserve a OSTI DOI

  @testrail-C372603
  @non-regression
  Scenario Outline: Reserve an OSTI DOI with valid PDS4 label
    Given a valid input at <input_value>
    When reserve DOI in OSTI format at <node_value>
    Then produced osti record is similar to reference osti <ref_output_value>
    Examples: Valid reserve spreadsheets
      | input_type   | node_value | input_value                       | ref_output_value  |
      | bundle       | img        | input/DOI_Reserved_GEO_200318.csv | tests/reserve_ok/output.xml  |

  @testrail-C372604
  Scenario Outline: Reserve an OSTI DOI with an invalid PDS4 label
    Given an invalid PDS4 label at <input_value>
    When reserve DOI in OSTI format at <node_value>
    Then a reading error report is generated for <input_value>
    Examples: Invalid PDS4 labels
      | input_type   | node_value | input_value                   | error_report  |
      | bundle       | img        | tests/data/invalid_bundle.xml | tests/data/reserve_error_report.txt |

  @testrail-C372605
  Scenario Outline: Verify reference reserve transactions match
    Given reference transactions in <transaction_dir>
    When reference record is reserved for node <node_value> with <input_value>
    Then produced osti record is similar to reference osti <output_value>

    Examples: reference reserve transactions
      | transaction_dir                       |node_value | input_value                                                            | output_value |

      | tests/aaDOI_production_submitted_labels     | atm        | ATMOS_reserve_Insight_Bundle_20200624/aaaSubmitted_by_ATMOS_reserve_2020624/DOI_Requests_ATM-2020-06-30.xlsx | ATMOS_reserve_Insight_Bundle_20200624/aaRegistered_by_EN/DOI_reserved_all_records.xml |
      | tests/aaDOI_production_submitted_labels     | geo        | GEO_APXS_reserve_Bundle_20200710/aaaSubmitted_by_GEO_reserve_20200710/DOI_Reserved_template_20200709.xlsx | GEO_APXS_reserve_Bundle_20200710/aaRegistered_by_EN/DOI_reserved_all_records.xml |
      | tests/aaDOI_production_submitted_labels     | geo        | GEO_Apollo_Bundles_reserve_20200316/aaaSubmitted_by_GEO_reserve_20200316/DOI_GEO_Apollo_Reserved_Bundles_20200316.xlsx | GEO_Apollo_Bundles_reserve_20200316/aaaRegistered_by_EN_reserve_allrecords_20200416/DOI_reserved_all_records.xml |
      | tests/aaDOI_production_submitted_labels     | geo        | GEO_reserve_Bundle_20200706/aaaSubmitted_by_GEO_reserve_20200706/DOI_Reserved_template_20200702.xlsx | GEO_reserve_Bundle_20200706/aaRegistered_by_EN/DOI_reserved_all_records.xml |
      | tests/aaDOI_production_submitted_labels     | geo        | GEO_reserve_Lunar_Space_weather_20200730/aaaSubmitted_by_GEO_reserve_20200730/DOI_Reserved_template_20200729.xlsx | GEO_reserve_Lunar_Space_weather_20200730/aaRegistered_by_EN_reserve/DOI_reserved_all_records.xml |
      | tests/aaDOI_production_submitted_labels     | rms        | RINGS_Jupiter_occs_20200609/aaaSubmitted_by_RINGS_reserve_2020609/DOI_RMS_U-occs-Reserved-2020-06-08.xlsx | RINGS_Jupiter_occs_20200609/aaRegistered_by_EN/DOI_reserved_all_records.xml |


# Future tests:

#      | aaDOI_production_submitted_labels     | rms        | RINGS_reserve_VIMS_20200406/aaaSubmitted_by_RINGS_reserve_20200406/DOI_RMS_Cassini-Reserved-2020-03-31.xlsx | RINGS_reserve_VIMS_20200406/aaaRegistered_by_EN_reserve_20200316/DOI_reserved_cassini_vims_saturn_document_vims-browse-interpretation-key.xml |

#      | aaDOI_production_submitted_labels     | geo        | GEO_reserve_Contacr_Science_Target_20200810/aaaSubmitted_by_GEO_reserve_20200810/DOI_Reserved_template_20200810.xlsx | GEO_reserve_Contacr_Science_Target_20200810/aaRegistered_by_EN_reserve/DOI_reserved_all_records.xml |
#      | aaDOI_production_submitted_labels     | geo        | GEO_reserve_shocked_feldspar_20200330/aaaSubmitted_by_GEO_20200316/DOI_Reserved_GEO_200318_edited.xlsx | GEO_reserve_shocked_feldspar_20200330/aaaRegistered_by_EN_20200316/DOI_reserved_lab_shocked_feldspars.xml |
#      | aaDOI_production_submitted_labels     | rms        | RINGS_ocss_reserve_bundle_20200722/aaaSubmitted_by_RINGS_20200722/DOI_RMS_U-occs-Reserved-2020-07-22.xlsx | RINGS_ocss_reserve_bundle_20200722/aaRegistered_by_EN_20200722-1/DOI_reserved_all_records.xml |
#      | aaDOI_production_submitted_labels     | rms        | RINGS_reserve_Uranus_occ_20200428/aaaSubmitted_by_RINGS_active_2020513/DOI_RMS_U-occs-Reserved-2020-05-12_edited.xlsx | aaaRegistered_by_EN_active_20200514/DOI_reserved_all_records.xml |
#      | aaDOI_production_submitted_labels     | rms        | RINGS_reserve_VIMS_20200406/aaaSubmitted_by_RINGS_reserve_20200406/DOI_RMS_Cassini-Reserved-2020-03-31_edited.xlsx | RINGS_reserve_VIMS_20200406/aaaRegistered_by_EN_reserve_20200316/DOI_reserved_all_records.xml |
# This next doesn't compare due to "[Showalter #2], new:[Showalter #3]'
#      | aaDOI_production_submitted_labels     | rms        | RINGS_reserve_VIMS_20200406/aaaSubmitted_by_RINGS_reserve_20200406/DOI_RMS_Cassini-Reserved-2020-03-31_edited.xlsx | RINGS_reserve_VIMS_20200406/aaaRegistered_by_EN_reserve_20200316/DOI_reserved_cassini_vims_saturn_document_vims-browse-interpretation-key_edit.xml |
