# PDS DOI Service
# Software Requirements and Design

* [Component Description](#component-description)
* [Use Cases](#use-cases)
* [Requirements](#requirements)
* [Design](#design)

## Component Description

The PDS Data Object Identifier (DOI) service is responsible for the management of [DOIs](https://www.doi.org/) for the Planetary Data System.

## Use Cases
### Generate DOI Object from PDS4 Label
1. A user posts a bundle bundle/collection/product PDS4 label to the service.
2. The service translates the metadata from the PDS4 label into the DOI/IAD Record Object
3. The service return the IAD record object

### User Submits DOI Object
1. A user posts a DOI/IAD Record object
2. The service verifies validity of the object
3. The service posts the object to the Tracking Service
   1. Alternatively, the service could post the object to a file staging area or just include in email
4. The service notifies Operator of DOI submission
   1. Alternatively, the service could send an email to Operator for manual vetting and submission.

### Operator Reserves DOI Object
1. The authenticated Operator submits a DOI object to the service for reserve DOI
2. The service validates the DOI object
3. The service submit the DOI object to the IAD Service and verifies return values
4. The service posts Reserved DOI information to Tracking Service and forwards response to Operator

### Operator Release DOI Object
1. The authenticated Operator submits a DOI object to the service for release DOI
2. The service validates the DOI object
3. The service submit the DOI object to the IAD Service and verifies return values
4. The service posts Released/Published DOI information to Tracking Service and forwards response to Operator

---

## Requirements

### Level 3 Requirements
The following PDS level 3 requirements are relevant to this service:

TBD

### Level 4 Requirements

TBD

### Level 5 Requirements
The level 5 requirements in PDS represent subsystem or componentrequirements at a detailed level. The following requirements pertain to this service:

### DOI Management
| ID | Requirement | Notes |
| -- | ----------- | ----------- |
| DOI.x | The software shall be capable of accepting a request to create a draft DOI. | |
| DOI.x | The software shall be capable of accepting a request to reserve a DOI. | |
| DOI.x | The software shall be capable of accepting a request to release a DOI. | |
| DOI.x | The software shall be capable of accepting a request to delete a DOI. | |
| DOI.x | The software shall be capable of accepting a request to update DOI metadata. | |
| DOI.x | The software shall be capable of batch processing >1 DOI requests. | |

### DOI Metadata
| ID | Requirement | Notes |
| -- | ----------- | ----------- |
| DOI.x | The software shall be capable of autonomously generating the minimum set of DOI metadata from PDS4 Collection, Bundle, Document products. | |
| DOI.x | The software shall validate a minimum set of metadata is provided when reserving, releasing, or updating a DOI. This minimum set of metadata will be defined by the PDS DOI Working Group. | | 
| DOI.x | The software shall validate the DOI metadata meets  is provided when reserving, releasing, or updating a DOI. | |

### DOI Interface Support
| ID | Requirement | Notes |
| -- | ----------- | ----------- |
| DOI.x | The software shall maintain a database of PDS DOIs and their current state. | Related to Tracking Service. |
| DOI.x | The software shall maintain the ability to manage DOIs through both [OSTI](https://www.osti.gov/iad2/docs) and [DataCite](https://support.datacite.org/docs/api). | Should support OSTI originally, but provide the ability to switch to DataCite (or other interface) in the future. |

---

## Architecture Overview

The following diagram gives a detailed view of the DOI Service within the context of the system:

![DOI Service Design](pds-doi-service-design.png)

The following is a more detailed breakdown of the DOI Service based on its functions:

---

## Detailed Design

### DOI Service

The DOI Service a RESTful web service that provides the ability to perform the following operations for PDS DOIs:
* Draft a DOI
* Reserve a DOI
* Release a DOI
* Retrieve a DOI
* Update a DOI
* Delete a DOI

---


#### Retrieve a DOI

![Retrieve DOI Activity Diagram](retrieve_activity.png)
---

#### Create / Draft a DOI

![Create DOI Activity Diagram](create_activity.png)
---

#### Reserve a DOI

TBD 
---

#### Release a DOI

TBD
---

#### Update a DOI

TBD
---

#### Delete a DOI

TBD
---

### Batch Processsing Service

Batch processing service interfaces with the DOI service, and is responsible for perform DOI operations across a large number of products using a pre-defined TBD CSV format for submitting batch metadata.

The batch system will then read in this CSV, and synchronously perform DOI Service operations on the set of product metadata.

---

### DOI Command-line Client

This client will be used to access the DOI Service from the command-line. All functions available through the DOI Service should be made available from this client interface.

---

### DOI Web Interface

TBD


© 2020 California Institute of Technology.
Government sponsorship acknowledged.


