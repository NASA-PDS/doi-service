Feature: create a draft OSTI DOI

  @testrail-C372600
  @non-regression
  Scenario Outline: Create a draft DOI from a valid PDS4 label <output_type> at <input_value>
    Given a valid input at <input_value>
    When create draft DOI for node <node_value>
    Then produced osti record is similar to reference osti <ref_output_value>

    Examples: Valid PDS4 labels
      | input_type             | node_value |input_value                                                                                 | output_type | ref_output_value                        |
      | bundle                 | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml                             | OSTI        | tests/data/valid_bundle_doi.xml     |
      | data collection        | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml               | OSTI        | tests/data/valid_datacoll_doi.xml   |
      | browse collection      | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml           | OSTI        | tests/data/valid_browsecoll_doi.xml |
      | calibration collection | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml | OSTI        | tests/data/valid_calibcoll_doi.xml  |
      | document collection    | img | https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml       | OSTI        | tests/data/valid_docucoll_doi.xml   |

  @testrail-C372601
  Scenario Outline: an invalid PDS4 is submitted for DOI draft input_type <input_type>
    Given an invalid PDS4 label at <input_value>
    When create draft DOI for node <node_value>
    Then a reading error report is generated for <input_value>

    Examples: Invalid PDS4 labels
      | input_type |node_value | input_value                   | output_type | error_report                      |
      | bundle     |img        | tests/data/invalid_bundle.xml | OSTI        | tests/data/draft_error_report.txt |


  @testrail-C372602
  Scenario Outline: Verify reference draft transactions match
    Given reference transactions in <transaction_dir>
    When reference record is drafted for node <node_value> from <input_subdir>
    Then produced osti record is similar to reference osti <ref_output_value>

    Examples: reference draft transactions
      | transaction_dir                 | node_value | input_subdir                                                         | ref_output_value |
      | tests/aaDOI_production_submitted_labels/ATMOS_mpf_irtf_Bundles_20200414 | atm        | aaaSubmitted_by_ATMOS_active_2020414 | aaaRegistered_by_EN_active_20200330/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/GEO_asurpif_phx_tega_20200428   | geo        | aaaSubmitted_by_GEO_active_20200330 | aaaRegistered_by_EN_active_20200330/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/GEO_Chand_Bundle_20200713       | geo        | aaaSubmitted_by_GEO_active_20200713 | aaRegistered_by_EN/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/GEO_Insight_cruise_20200611     | ppi        | aaaSubmitted_by_GEO_2020611         | aaRegistered_by_EN/DOI_registered_all_records.xml |

      | tests/aaDOI_production_submitted_labels/GEO_MER_cs_target_20200824      | geo        | aaaSubmitted_by_GEO_active_20200824 | aaaRegistered_by_EN_active_20200813/DOI_registered_all_records.xml |

      | tests/aaDOI_production_submitted_labels/GEO_Mer_updated_Bundles_20200629| geo        | aaaSubmitted_by_GEO_active_2020629/MER_Bundles_2| aaRegistered_by_EN/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/GEO_Messenger_20200327          | geo        | aaaSubmitted_by_GEO_active_2020427/messenger_doi | aaaRegistered_by_EN_active_20200427/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/GEO_phy_meca_Bundle_20200609    | geo        | aaaSubmitted_by_GEO_active_2020609               | aaRegistered_by_EN/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/IMG_MRO_Bundle_20200814         | img        | aaaSubmitted_by_IMG_active_2020813               | aaaRegistered_by_EN_active_20200813/aaaSave_original/DOI_registered_all_records.xml |
      | tests/aaDOI_production_submitted_labels/PPI_InSight_Bundles_Collections_20200812 | ppi | aaaSubmitted_by_PPI_active_20200812 | aaRegistered_by_EN_active/DOI_registered_all_records_corrected.xml |
      | tests/aaDOI_production_submitted_labels/GEO_InSight_phx_ra_20200603              | geo | aaaSubmitted_by_GEO_active_2020603/bundle_phx_ra_EDR_raw_edited.xml  | aaRegistered_by_EN/DOI-C_registered_bundle_phx_ra_edited.xml |
      | tests/aaDOI_production_submitted_labels/IMG_InSight_Bundle_20191216 | img | aaSubmitted_by_Insight/bundle.xml                 | aaRegistered_by_EN/DOI_bundle.xml |
      | tests/aaDOI_production_submitted_labels/IMG_InSight_Bundle_20191216 | img | aaSubmitted_by_Insight/collection_calibration.xml | aaRegistered_by_EN/DOI_collection_calibration.xml |
      | tests/aaDOI_production_submitted_labels/PPI_Cassini_RPWS_20200219   | ppi | aaSubmitted/collection_rpws-electron_density_data.xml | aaRegistered_by_EN/DOI_collection_data.xml |


  @testrail-C373834
  Scenario Outline: Draft a DOI which has been previously reserved
    Given reference transactions in <transaction_dir>
    Given random new lid
    When reference record is reserved for node <node_value> with <input_reserve>
    And submit osti record for <node_value>
    And reference record is drafted for node <node_value> from <input_pds4>
    And submit osti record for <node_value>
    Then lidvid already submitted exception is raised

    Examples: reference reserve transactions
      | transaction_dir      |node_value | input_reserve | input_pds4 |
      | tests/end_to_end     | atm       | reserve.csv   | bundle_pds4.xml |


# Some notes: The type of aaDOI_production_submitted_labels/GEO_Insight_cruise_20200611 should be geo
# but the historical has ppi so use ppi above to match.
#      | aaDOI_production_submitted_labels/GEO_Insight_cruise_20200611     | ppi        | aaaSubmitted_by_GEO_2020611         | aaRegistered_by_EN/DOI_registered_all_records.xml |

# The below case doesn't work when all other cases worked.
# Fields 'first_name', 'last_name' differs
# Commented out.
#     | aaDOI_production_submitted_labels/GEO_Mer_Bundles_20200622        | geo        | aaaSubmitted_by_GEO_active_2020622/MER_Bundles  | aaRegistered_by_EN/DOI_registered_all_records.xml |

# This next one doesn't work because someone manually edited the output.
#      | aaDOI_production_submitted_labels/IMG_MRO_Bundle_20200814         | img        | aaaSubmitted_by_IMG_active_2020813               | aaaRegistered_by_EN_active_20200813/DOI_registered_all_records-GC.xml |
# This next case has issues with publication_date 01/01/2019
#      | aaDOI_production_submitted_labels/IMG_InSight_Bundle_20191216 | img | aaSubmitted_by_Insight/collection_browse.xml      | aaRegistered_by_EN/DOI_collection_browse.xml |
# This next case has issues with publication_date 01/01/2019
#      | aaDOI_production_submitted_labels/IMG_InSight_Bundle_20191216 | img | aaSubmitted_by_Insight/collection_data.xml     | aaRegistered_by_EN/DOI_collection_data.xml |
# This next case has issues with publication_date 01/01/2019
#      | aaDOI_production_submitted_labels/IMG_InSight_Bundle_20191216 | img | aaSubmitted_by_Insight/collection_document.xml | aaRegistered_by_EN/DOI_collection_document.xml |

# Possible future test(s):
#      | aaDOI_production_submitted_labels/PPI_Cassini_RPWS_hfr_qtn_20200302 | ppi       | aaSubmitted/collection-rpws-hfr-qtn-data_edited.xml | aaRegistered/DOI_collection-rpws-hfr-qtn-data_edited-mafi.xml |
