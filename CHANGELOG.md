# Changelog

## [2.3.2](https://github.com/NASA-PDS/doi-service/tree/2.3.2) (2022-09-22)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.4.0-dev...2.3.2)

**Other closed issues:**

- Correct pandas pip pin. [\#370](https://github.com/NASA-PDS/doi-service/issues/370)

## [v2.4.0-dev](https://github.com/NASA-PDS/doi-service/tree/v2.4.0-dev) (2022-09-21)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.3.2...v2.4.0-dev)

## [v2.3.2](https://github.com/NASA-PDS/doi-service/tree/v2.3.2) (2022-09-21)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/release/2.3.2...v2.3.2)

**Other closed issues:**

- Update version spec to indicate Pandas 1.4.4 in setup.cfg [\#369](https://github.com/NASA-PDS/doi-service/issues/369)

## [release/2.3.2](https://github.com/NASA-PDS/doi-service/tree/release/2.3.2) (2022-09-21)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.3.1...release/2.3.2)

## [v2.3.1](https://github.com/NASA-PDS/doi-service/tree/v2.3.1) (2022-09-21)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/release/2.3.1...v2.3.1)

**Defects:**

- Unit tests for reserve.py and input\_util.py due to unpinned pandas dependency [\#368](https://github.com/NASA-PDS/doi-service/issues/368)

## [release/2.3.1](https://github.com/NASA-PDS/doi-service/tree/release/2.3.1) (2022-09-20)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/release/2.3.0...release/2.3.1)

## [release/2.3.0](https://github.com/NASA-PDS/doi-service/tree/release/2.3.0) (2022-09-19)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.2.1...release/2.3.0)

**Requirements:**

- As a DOI user, I would like to know the copyright for PDS data [\#335](https://github.com/NASA-PDS/doi-service/issues/335)
- As a DOI user, I would like to know the licensing information PDS data [\#224](https://github.com/NASA-PDS/doi-service/issues/224)

**Improvements:**

- As a publisher, I want to be notified when a new DOI has been minted or significant update to the metadata [\#283](https://github.com/NASA-PDS/doi-service/issues/283)

**Defects:**

- \#349 merged with failing unit tests [\#362](https://github.com/NASA-PDS/doi-service/issues/362) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- dataCite reserve error on title [\#350](https://github.com/NASA-PDS/doi-service/issues/350) [[s.critical](https://github.com/NASA-PDS/doi-service/labels/s.critical)]
- DOI-service application inaccurately reports LID as being invalid [\#336](https://github.com/NASA-PDS/doi-service/issues/336) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- Implement COGNITO token verification in the doi-service API [\#348](https://github.com/NASA-PDS/doi-service/issues/348)
- Tag and deploy new release per \#331 [\#342](https://github.com/NASA-PDS/doi-service/issues/342)
- SBN DOI records that are incompatible with EN system [\#316](https://github.com/NASA-PDS/doi-service/issues/316)
- Add licensing information to DOI metadata for new DOIs [\#225](https://github.com/NASA-PDS/doi-service/issues/225)

## [v2.2.1](https://github.com/NASA-PDS/doi-service/tree/v2.2.1) (2022-07-27)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.2.0...v2.2.1)

**Requirements:**

- As a user, I want to release a DOI with a label that does not contain the DOI [\#344](https://github.com/NASA-PDS/doi-service/issues/344)
- The software shall validate the DOI metadata when reserving, releasing, or updating a DOI. [\#13](https://github.com/NASA-PDS/doi-service/issues/13)
- The software shall release a DOI \(making it findable\). [\#7](https://github.com/NASA-PDS/doi-service/issues/7)

**Defects:**

- Fix broken build [\#341](https://github.com/NASA-PDS/doi-service/issues/341) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- doi sync failing for SBN-PSI DOIs [\#331](https://github.com/NASA-PDS/doi-service/issues/331) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- Valid PDS4 xml input is converted into an invalid json that fails internal datacite validator [\#328](https://github.com/NASA-PDS/doi-service/issues/328) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)] [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]

**Other closed issues:**

- Develop script to sync DOIs to registry [\#249](https://github.com/NASA-PDS/doi-service/issues/249)

## [v2.2.0](https://github.com/NASA-PDS/doi-service/tree/v2.2.0) (2022-04-14)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.1.3...v2.2.0)

**Requirements:**

- Add Radio Science to set of possible nodes [\#317](https://github.com/NASA-PDS/doi-service/issues/317)
- The software shall maintain the ability to manage DOIs through DataCite. [\#16](https://github.com/NASA-PDS/doi-service/issues/16)

**Defects:**

- Fix issues related to integration with Web UI [\#326](https://github.com/NASA-PDS/doi-service/issues/326) [[s.critical](https://github.com/NASA-PDS/doi-service/labels/s.critical)]
- Deprecate VCO and Akatsuki DOIs [\#324](https://github.com/NASA-PDS/doi-service/issues/324) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- deactivate registered cassini doi 10.17189/1517823 [\#321](https://github.com/NASA-PDS/doi-service/issues/321) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- Corruption in local database with invalid JSON [\#318](https://github.com/NASA-PDS/doi-service/issues/318) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- Test DOIs are showing up in pds-gamma DOI search now linked from operations Citing PDS Data page [\#310](https://github.com/NASA-PDS/doi-service/issues/310) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- Develop script to sync SBN DOIs with DOI Service [\#312](https://github.com/NASA-PDS/doi-service/issues/312)

## [v2.1.3](https://github.com/NASA-PDS/doi-service/tree/v2.1.3) (2022-02-01)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.1.2...v2.1.3)

## [v2.1.2](https://github.com/NASA-PDS/doi-service/tree/v2.1.2) (2022-01-13)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.1.1...v2.1.2)

**Requirements:**

- As a PDS Operator, I want to perform a bulk update of a specific field across many DOI records [\#257](https://github.com/NASA-PDS/doi-service/issues/257)
- As an operator, I want one place to go for all DOI Service / API / UI documentation [\#202](https://github.com/NASA-PDS/doi-service/issues/202)
- As an operator, I want to know how to deploy and use the API from the Sphinx documentation [\#201](https://github.com/NASA-PDS/doi-service/issues/201)

**Improvements:**

- Update all past DOIs for consistent metadata [\#294](https://github.com/NASA-PDS/doi-service/issues/294)
- Improve upon application security for write access [\#231](https://github.com/NASA-PDS/doi-service/issues/231)

**Defects:**

- Document need to be update after adding the update argument [\#313](https://github.com/NASA-PDS/doi-service/issues/313) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- --no-review argument has potential to be confused with -n \(node ID\) argument [\#305](https://github.com/NASA-PDS/doi-service/issues/305) [[s.low](https://github.com/NASA-PDS/doi-service/labels/s.low)]
- identifiers vs alternateIdentifiers appear disconnected from current DataCite schema [\#303](https://github.com/NASA-PDS/doi-service/issues/303) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]

**Other closed issues:**

- Develop DOI documentation for PDS Operator [\#256](https://github.com/NASA-PDS/doi-service/issues/256)

## [v2.1.1](https://github.com/NASA-PDS/doi-service/tree/v2.1.1) (2021-12-07)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.1.0...v2.1.1)

**Requirements:**

- Update default values to sync with SBN documentation [\#295](https://github.com/NASA-PDS/doi-service/issues/295)
- As a user, I want to search dois without case sensitiveness [\#223](https://github.com/NASA-PDS/doi-service/issues/223)

**Improvements:**

- As a user, I want to obtain json label format from a list command query [\#289](https://github.com/NASA-PDS/doi-service/issues/289)

**Defects:**

- DOI Service does not assign adequate permissions to transaction database/history [\#299](https://github.com/NASA-PDS/doi-service/issues/299) [[s.low](https://github.com/NASA-PDS/doi-service/labels/s.low)]
- Spreadsheet parsers do not handle blank rows gracefully [\#291](https://github.com/NASA-PDS/doi-service/issues/291) [[s.low](https://github.com/NASA-PDS/doi-service/labels/s.low)]
- Default keywords/subjects are not always added to DOI records [\#273](https://github.com/NASA-PDS/doi-service/issues/273) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

## [v2.1.0](https://github.com/NASA-PDS/doi-service/tree/v2.1.0) (2021-11-03)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.0.1...v2.1.0)

**Requirements:**

- As a user, I want a simplified DOI lifecycle workflow [\#286](https://github.com/NASA-PDS/doi-service/issues/286)
- As a user, I want to update the bundle/collection metadata associated with a DOI for accumulating data sets [\#279](https://github.com/NASA-PDS/doi-service/issues/279)
- As a user, I want to update the LIDVID associated with a DOI  [\#278](https://github.com/NASA-PDS/doi-service/issues/278)

**Improvements:**

- Improved parsing support for DataCite JSON format [\#274](https://github.com/NASA-PDS/doi-service/issues/274)
- Add new alternateIdentifier to match SBN schema [\#102](https://github.com/NASA-PDS/doi-service/issues/102)

**Defects:**

- doi-service does not connect to dataCite [\#264](https://github.com/NASA-PDS/doi-service/issues/264) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- Test out and document how to upgrade the service [\#255](https://github.com/NASA-PDS/doi-service/issues/255)
- Remove Versioneer [\#250](https://github.com/NASA-PDS/doi-service/issues/250)

## [v2.0.1](https://github.com/NASA-PDS/doi-service/tree/v2.0.1) (2021-10-11)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v2.0.0...v2.0.1)

**Improvements:**

- Improve spreadsheet parser error handling [\#260](https://github.com/NASA-PDS/doi-service/issues/260)

**Defects:**

- DOI Service does not properly handle input files with UTF-8 BOM [\#267](https://github.com/NASA-PDS/doi-service/issues/267)
- DOI Service should be generating landing page URL when none is provided [\#266](https://github.com/NASA-PDS/doi-service/issues/266)
- Release action does not check for assigned DOI before submission to DataCite [\#262](https://github.com/NASA-PDS/doi-service/issues/262)
- Query to DataCite does not properly support pagination [\#261](https://github.com/NASA-PDS/doi-service/issues/261)
- Spreadsheet parser does not validate/sanitize format of expected header row [\#259](https://github.com/NASA-PDS/doi-service/issues/259) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- Spreadsheet parser does not validate parsed contents of rows [\#258](https://github.com/NASA-PDS/doi-service/issues/258) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- Remove test and other transaction log data from public pypi distro [\#214](https://github.com/NASA-PDS/doi-service/issues/214) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- As a user, I want to have the latest documentation on https://nasa-pds.github.io/pds-doi-service/ for version 2.0 [\#253](https://github.com/NASA-PDS/doi-service/issues/253)

## [v2.0.0](https://github.com/NASA-PDS/doi-service/tree/v2.0.0) (2021-09-27)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v0.3.1...v2.0.0)

**Requirements:**

- As the PDS, I want to mint DOIs through DataCite [\#103](https://github.com/NASA-PDS/doi-service/issues/103)

**Improvements:**

- Port from pystache to jinja2 [\#242](https://github.com/NASA-PDS/doi-service/issues/242)
- As a user, I want to see the PDS3 ids as they originally are [\#229](https://github.com/NASA-PDS/doi-service/issues/229)
- review the full doi workflow and make it smooth for eng operators/users [\#145](https://github.com/NASA-PDS/doi-service/issues/145)

**Defects:**

- Fix test failure with flask\_testing module [\#247](https://github.com/NASA-PDS/doi-service/issues/247) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- As an operator, I want to sync our local database with DataCite metadata [\#239](https://github.com/NASA-PDS/doi-service/issues/239)
- As an Administrator, I want to toggle the DOI service provider via the INI config [\#237](https://github.com/NASA-PDS/doi-service/issues/237)
- Create Validator class for DataCite JSON Labels [\#236](https://github.com/NASA-PDS/doi-service/issues/236)
- Deploy point build of DOI service and UI [\#90](https://github.com/NASA-PDS/doi-service/issues/90)
- Dev beta testing with API [\#87](https://github.com/NASA-PDS/doi-service/issues/87)

## [v0.3.1](https://github.com/NASA-PDS/doi-service/tree/v0.3.1) (2021-08-04)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v1.1.1...v0.3.1)

**Requirements:**

- As an admistrator of the application,  I want to restrict access to API by specific referrer [\#228](https://github.com/NASA-PDS/doi-service/issues/228)
- As a user, I want to use the API with ids containing a slash \(/\) [\#198](https://github.com/NASA-PDS/doi-service/issues/198)
- As a SA, I want the operational deployment of the service to be secure [\#187](https://github.com/NASA-PDS/doi-service/issues/187)
- As an operator, I want to update DOI metadata through DataCite [\#175](https://github.com/NASA-PDS/doi-service/issues/175)
- As an operator, I want to release a DOI through DataCite [\#174](https://github.com/NASA-PDS/doi-service/issues/174)
- As an operator, I want query for one or more minted DOIs from DataCite [\#172](https://github.com/NASA-PDS/doi-service/issues/172)
- As an operator, I want to reserve a DOI through DataCite [\#171](https://github.com/NASA-PDS/doi-service/issues/171)

**Improvements:**

- Update DOI service for handling existing DOIs acceptance criteria per \#175 [\#227](https://github.com/NASA-PDS/doi-service/issues/227)

**Defects:**

- CI does not work on main branch for dev release [\#220](https://github.com/NASA-PDS/doi-service/issues/220)
- pytest does not work [\#219](https://github.com/NASA-PDS/doi-service/issues/219) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- Release OSTI command line does not work in one case [\#218](https://github.com/NASA-PDS/doi-service/issues/218) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- The issue \#140 does not work as expected [\#208](https://github.com/NASA-PDS/doi-service/issues/208) [[s.low](https://github.com/NASA-PDS/doi-service/labels/s.low)]
- When installing the pds-doi-service from scratch I had an error with Flask version compatibility [\#199](https://github.com/NASA-PDS/doi-service/issues/199) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]

**Other closed issues:**

- Refactoring to have OSTI as a "module" [\#204](https://github.com/NASA-PDS/doi-service/issues/204)
- Retrofit pds-doi-service to use pds python template [\#209](https://github.com/NASA-PDS/doi-service/issues/209)

## [v1.1.1](https://github.com/NASA-PDS/doi-service/tree/v1.1.1) (2021-05-27)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v1.1.0...v1.1.1)

**Requirements:**

- As a user, I want the application to support the history of PDS's DOIs, especially the one created for PDS3 products [\#192](https://github.com/NASA-PDS/doi-service/issues/192)
- As an API user, I want to always have an update date for the DOIs [\#184](https://github.com/NASA-PDS/doi-service/issues/184)
- As a user of the API, I want to see the DOI's title when I go GET /dois request [\#183](https://github.com/NASA-PDS/doi-service/issues/183)
- As an API user I want to filter on PDS3 Data Set IDs with wildcards [\#180](https://github.com/NASA-PDS/doi-service/issues/180)

**Improvements:**

- Dockerize API Service [\#163](https://github.com/NASA-PDS/doi-service/issues/163)

**Defects:**

- API accepts Reserve submissions with invalid LIDVIDs [\#191](https://github.com/NASA-PDS/doi-service/issues/191) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- As a user, I want to make sure I can not override existing DOI with new LIDVID [\#188](https://github.com/NASA-PDS/doi-service/issues/188) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- As a product owner, I want to test the service with historical PDS DOIs [\#189](https://github.com/NASA-PDS/doi-service/issues/189)

## [v1.1.0](https://github.com/NASA-PDS/doi-service/tree/v1.1.0) (2021-04-13)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/v1.0.1...v1.1.0)

**Requirements:**

- As an API user I want to filter on lidvids with wildcards [\#177](https://github.com/NASA-PDS/doi-service/issues/177)
- As a user, I want to see the lidvid of my DOIs in the email report [\#167](https://github.com/NASA-PDS/doi-service/issues/167)

**Improvements:**

- Add service to API for update of the status of records with OSTI \(check sub command\) [\#165](https://github.com/NASA-PDS/doi-service/issues/165)
- Implement Application Server to wrap Flask service [\#162](https://github.com/NASA-PDS/doi-service/issues/162)
- When a pds4 label or osti can not be parsed generate error 400 in API [\#157](https://github.com/NASA-PDS/doi-service/issues/157)
- API POST /dois should accept DOI OSTI format in payload [\#148](https://github.com/NASA-PDS/doi-service/issues/148)
- enable filter by status in sub-action 'pds-doi-cmd list' [\#144](https://github.com/NASA-PDS/doi-service/issues/144)
- Update submission to OSTI to handle the removal of a field from the OSTI metadata [\#140](https://github.com/NASA-PDS/doi-service/issues/140)
- Update API to deactivate 'release' end point, create a 'submit' end-point [\#135](https://github.com/NASA-PDS/doi-service/issues/135)
- Update draft action with new option --lidvid to change from review to draft the status of a DOI [\#134](https://github.com/NASA-PDS/doi-service/issues/134)
- Update status management in code with Enumeration [\#132](https://github.com/NASA-PDS/doi-service/issues/132)
- Update DOI UI and Service with new workflow for operational deployment [\#125](https://github.com/NASA-PDS/doi-service/issues/125)
- Develop User Access / Management Strategy [\#91](https://github.com/NASA-PDS/doi-service/issues/91)
- validate the submitted OSTI record against a schema [\#56](https://github.com/NASA-PDS/doi-service/issues/56)
- API Implementation for DOI Service [\#52](https://github.com/NASA-PDS/doi-service/issues/52)

**Defects:**

- site\_url error when we submit on OSTI test server [\#168](https://github.com/NASA-PDS/doi-service/issues/168)
- The url /dois/{lidvid} should still return XML in the record attribute [\#159](https://github.com/NASA-PDS/doi-service/issues/159) [[s.critical](https://github.com/NASA-PDS/doi-service/labels/s.critical)]
- draft OSTI label [\#154](https://github.com/NASA-PDS/doi-service/issues/154) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- when doing draft with warnings \(e.g. duplicated title\) the -f option does not help [\#150](https://github.com/NASA-PDS/doi-service/issues/150) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- when release command keywords are broken with encoded characters [\#143](https://github.com/NASA-PDS/doi-service/issues/143) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- api does not ignore '/' at the end of url [\#141](https://github.com/NASA-PDS/doi-service/issues/141) [[s.low](https://github.com/NASA-PDS/doi-service/labels/s.low)]
- xlsx file extension for reserve not supported [\#138](https://github.com/NASA-PDS/doi-service/issues/138) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- 'pds-doi-cmd draft' chokes on a legit Product\_Document [\#129](https://github.com/NASA-PDS/doi-service/issues/129) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- command pds-doi-cmd list returns update date in timestamp instead of iso8601 [\#128](https://github.com/NASA-PDS/doi-service/issues/128) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- update\_date management [\#127](https://github.com/NASA-PDS/doi-service/issues/127) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- get /dois/{lidvid} [\#126](https://github.com/NASA-PDS/doi-service/issues/126) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]
- the sqllite database should be created at the same location, whereever the command are launched from [\#122](https://github.com/NASA-PDS/doi-service/issues/122) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- Raise a specific exception when the OSTI server is not reachable [\#119](https://github.com/NASA-PDS/doi-service/issues/119) [[s.medium](https://github.com/NASA-PDS/doi-service/labels/s.medium)]

**Other closed issues:**

- Analyze/Test the dataCite API for dataCite [\#170](https://github.com/NASA-PDS/doi-service/issues/170)
- Update release action with --no-review option, make 'with review' default behavior [\#133](https://github.com/NASA-PDS/doi-service/issues/133)
- Document the security requirements for operational installation of DOI Service [\#124](https://github.com/NASA-PDS/doi-service/issues/124)

## [v1.0.1](https://github.com/NASA-PDS/doi-service/tree/v1.0.1) (2020-11-24)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/1.0.0...v1.0.1)

**Improvements:**

- Extraction of the OSTI XML in /dois?... GET requests [\#116](https://github.com/NASA-PDS/doi-service/issues/116)
- Draft action: read the doi from the pds4 label [\#114](https://github.com/NASA-PDS/doi-service/issues/114)
- Be explicit in the install documentation about the test/prod osti server configuration [\#98](https://github.com/NASA-PDS/doi-service/issues/98)

**Defects:**

- GET /dois must support empty vid field [\#121](https://github.com/NASA-PDS/doi-service/issues/121) [[s.high](https://github.com/NASA-PDS/doi-service/labels/s.high)]
- configuration files are not well deployed [\#115](https://github.com/NASA-PDS/doi-service/issues/115)
- Be more specific about the supported python version or extend tests [\#92](https://github.com/NASA-PDS/doi-service/issues/92)

**Other closed issues:**

- Add force argument to the /dois POST function [\#113](https://github.com/NASA-PDS/doi-service/issues/113)
- allow to post PDS4 labels in the payload \(for draft\) [\#107](https://github.com/NASA-PDS/doi-service/issues/107)
- Add exception name in the error messages [\#106](https://github.com/NASA-PDS/doi-service/issues/106)
- Complete get DOIS criterias with the arguments proposed in command line [\#105](https://github.com/NASA-PDS/doi-service/issues/105)
- Add GET DOI to the API [\#100](https://github.com/NASA-PDS/doi-service/issues/100)
- Develop API specification in SwaggerHub [\#80](https://github.com/NASA-PDS/doi-service/issues/80)
- Add Release DOI function to API [\#79](https://github.com/NASA-PDS/doi-service/issues/79)
- Add POST Reserve xslx/csv DOI function to API [\#78](https://github.com/NASA-PDS/doi-service/issues/78)
- Add POST PDS4 or  OSTI DOI label to API [\#77](https://github.com/NASA-PDS/doi-service/issues/77)
- Mock web UI for DOI management  [\#67](https://github.com/NASA-PDS/doi-service/issues/67)
- Add Status / Query component to API [\#38](https://github.com/NASA-PDS/doi-service/issues/38)

## [1.0.0](https://github.com/NASA-PDS/doi-service/tree/1.0.0) (2020-10-13)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/0.0.3...1.0.0)

**Improvements:**

- Update to use pds round-up github action [\#94](https://github.com/NASA-PDS/doi-service/issues/94)
- Write procedure documentation [\#83](https://github.com/NASA-PDS/doi-service/issues/83)
- End to end behave test [\#82](https://github.com/NASA-PDS/doi-service/issues/82)
- initialize production deployment with pre-existing dois [\#71](https://github.com/NASA-PDS/doi-service/issues/71)
- add check to ensure landing page is online prior to DOI release [\#70](https://github.com/NASA-PDS/doi-service/issues/70)
- Revise DOI Service Requirements [\#65](https://github.com/NASA-PDS/doi-service/issues/65)
- Add configuration documentation [\#60](https://github.com/NASA-PDS/doi-service/issues/60)
- create full\_name when first/last name cannot be parsed [\#58](https://github.com/NASA-PDS/doi-service/issues/58)
- Perform benchmark tests between original prototype software and new system [\#44](https://github.com/NASA-PDS/doi-service/issues/44)
- Update documentation for operational installation and usage [\#42](https://github.com/NASA-PDS/doi-service/issues/42)
- Develop simple regression test suite for deployment [\#41](https://github.com/NASA-PDS/doi-service/issues/41)
- Develop DOI metadata automated validation component [\#18](https://github.com/NASA-PDS/doi-service/issues/18)

**Defects:**

- node is not provided as contributor in the reserve records [\#72](https://github.com/NASA-PDS/doi-service/issues/72)
- Update default DOI metadata according to changes in requirements [\#55](https://github.com/NASA-PDS/doi-service/issues/55)

**Other closed issues:**

- Revise requirements to ensure scope is being met [\#64](https://github.com/NASA-PDS/doi-service/issues/64)
- Develop DOI Service Scope [\#63](https://github.com/NASA-PDS/doi-service/issues/63)
- Develop operational documentation and test suite [\#40](https://github.com/NASA-PDS/doi-service/issues/40)

## [0.0.3](https://github.com/NASA-PDS/doi-service/tree/0.0.3) (2020-07-31)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/0.0.2...0.0.3)

## [0.0.2](https://github.com/NASA-PDS/doi-service/tree/0.0.2) (2020-07-31)

[Full Changelog](https://github.com/NASA-PDS/doi-service/compare/cc08fcdce4414bec5d83e1187998538152391642...0.0.2)

**Improvements:**

- Implement the command line and parser to release a doi [\#46](https://github.com/NASA-PDS/doi-service/issues/46)
- Develop Pending DOI Handler component for iteratively querying OSTI for DOI status until status change [\#33](https://github.com/NASA-PDS/doi-service/issues/33)
- Develop Status / Query capability for querying database and return JSON [\#32](https://github.com/NASA-PDS/doi-service/issues/32)
- Develop maintain internal database of DOI requests [\#31](https://github.com/NASA-PDS/doi-service/issues/31)
- Develop ability to maintain a transaction log database [\#29](https://github.com/NASA-PDS/doi-service/issues/29)
- Re-organize and clean-up code to meet coding standards [\#28](https://github.com/NASA-PDS/doi-service/issues/28)
- Develop DOI Status / Query component [\#27](https://github.com/NASA-PDS/doi-service/issues/27)
- Implement initial DOI database and management [\#26](https://github.com/NASA-PDS/doi-service/issues/26)
- DOI Batch Processing capability [\#25](https://github.com/NASA-PDS/doi-service/issues/25)
- Update Released DOI capability [\#24](https://github.com/NASA-PDS/doi-service/issues/24)
- Release DOI capability [\#22](https://github.com/NASA-PDS/doi-service/issues/22)
- Reserve a DOI capability [\#21](https://github.com/NASA-PDS/doi-service/issues/21)
- Develop draft PDS Policy for Assigning DOIs [\#20](https://github.com/NASA-PDS/doi-service/issues/20)
- Design REST API and JSON response [\#19](https://github.com/NASA-PDS/doi-service/issues/19)
- Develop Status / Query API and component for OSTI status of a DOI [\#4](https://github.com/NASA-PDS/doi-service/issues/4)
- Create / Draft a DOI object capability [\#2](https://github.com/NASA-PDS/doi-service/issues/2)

**Other closed issues:**

- document requirements and tests [\#3](https://github.com/NASA-PDS/doi-service/issues/3)
- Develop initial requirements and design for DOI Service [\#1](https://github.com/NASA-PDS/doi-service/issues/1)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
