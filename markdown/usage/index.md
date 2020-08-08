# 🏃‍♀️ Usage

## Overview

A DOI (Digital Object Identifier) is a URI which is used to permanently identify a digital object: dataset or document.
The DOI is then used to cite the digital object, especially in scientific papers.

In the context of PDS, the DOIs follows this workflow:
- reserve: before a dataset is published in PDS, a DOI can be reserved so that the researchers working with the digital resource at early stage can cite it in their papers. This step is optional.
- draft: the metadata associated to the DOI is elaborated and validated.
- release: the offcial DOI is registered at [OSTI](https://www.osti.gov/data-services) and [dataCite](https://datacite.org).
- deactivate (To Be Done): although it is not supposed to happen, due to error in the release one might deactivate a  DOI.

The reserve, draft and release steps can be repeated multiple time to update a DOI metadata.

The inputs to the DOI creation are either PDS4 labels or ad hoc spreadsheets (for the reserve step).

The metadata managed with DOIs is meant to be preserved and traceable as it is used to permanently cite a digital resource.
For this reason all the transactions, creations, updates with the PDS DOI management system are registered in a database.

Currently the tool provided is activated with a command line and used by a PDS Engineering Node operator interacting with the Discipline Nodes.
A later version will provide a web API, a web UI and a cmd API client to enable Discipline Nodes to directly manage their DOIs.

## Usage Information

PDS core command for DOI management. The available subcommands are:
reserve (create or update a DOI before the data is published),
draft (prepare a OSTI record from a PDS4 labels),
release (create or update a DOI on OSTI server),
check (check DOI pending status at OSTI),
list (extract doi descriptions with criteria),


```
usage: pds-doi-cmd [-h] {reserve,draft,release,check,list} ...
```

### Positional Arguments

### Sub-commands:

#### reserve

create a DOI for a unpublished dataset. The input is a spreadsheet or csv file

```
pds-doi-cmd reserve [-h] -n "img" -i input/DOI_Reserved_GEO_200318.csv -s
                    "my.email@node.gov"
```

##### Named Arguments

#### draft

create a draft of OSTI records, from PDS4 label or list of PDS4 labels input

```
pds-doi-cmd draft [-h] -n "img" -i input/bundle_in_with_contributors.xml -s
                  "my.email@node.gov" [-t osti]
```

##### Named Arguments

#### release

register a new DOI or update an existing DOI on OSTI server

```
pds-doi-cmd release [-h] -n "img" -i input/DOI_Update_GEO_200318.xml -s
                    "my.email@node.gov"
```

##### Named Arguments

#### check

check DOI status of pending DOIs at OSTI,email reports are sent to admins and submitters of the pending DOIswhen status is updated, the local transaction log is updated

```
pds-doi-cmd check [-h]
```

#### list

extract the submitted DOI from the local transaction log, with following selection criteria

```
pds-doi-cmd list [-h] [-n "img,eng"] [-doi 10.17189/21734]
                 [-lid urn:nasa:pds:lab_shocked_feldspars]
                 [-lidvid urn:nasa:pds:lab_shocked_feldspars::1.0]
                 [-start 2020-01-01T19:02:15.000000]
                 [-end 2020-12-311T23:59:00.000000] [-s "my.email@node.gov"]
                 [-f JSON]
```

##### Named Arguments
