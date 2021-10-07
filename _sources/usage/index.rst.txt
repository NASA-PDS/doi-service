🏃‍♀️ Usage
===========

.. toctree::


Overview
--------

A DOI (Digital Object Identifier) is a URI which is used to permanently identify
a digital object, typically a dataset or document.
The DOI is then used to cite the digital object, especially in scientific papers.

In the context of PDS, publishing a new DOI follows this workflow:

    - `Reserve`: Before a dataset is published in PDS, a DOI is reserved so the
      researchers working with the digital resource can cite it at early stage.
    - `Draft`: The metadata associated to an existing DOI is elaborated and validated.
    - `Review`: Once all metadata has been properly associated to the DOI, the
      requester submits the DOI record for review to the PDS Engineering node.
    - `Release`: After the PDS Engineering node determines that the DOI record is
      filled out properly, the DOI and its metadata is officially registered at
      `DataCite`_ and made available for public discovery. If there any issues with
      the reviewed record, PDS Engineering node may move the record back to `Draft`
      status for correction by the original submitter.

The Draft and Release steps may be repeated multiple times to update the metadata
associated to the DOI.

Inputs to DOI creation (the Reserve step) are either PDS4 labels or ad-hoc
spreadsheets.

The metadata managed with DOIs is meant to be preserved and traceable, as it is
used to permanently cite a digital resource. For this reason, all transactions,
creations, and updates with the PDS DOI Service are registered in a local database.
This database is used to track submissions-in-progress and help ensure the proper
workflow (`Reserve` -> `Draft` -> `Review` -> `Release`) is enforced.

Currently, the service provides a command line tool for use by a PDS Engineering
Node operator interacting with the Discipline Nodes, as well as a web API and UI
to enable Discipline Nodes to directly manage their DOIs.

Command Line Usage Information
------------------------------

.. argparse::
   :module: pds_doi_service.core.actions.action
   :func: create_parser
   :prog: pds-doi-cmd


.. _OSTI: https://www.osti.gov/data-services
.. _DataCite: https://datacite.org
