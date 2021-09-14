🏃‍♀️ Usage
===========

.. toctree::


Overview
--------

A DOI (Digital Object Identifier) is a URI which is used to permanently identify a digital object: dataset or document.
The DOI is then used to cite the digital object, especially in scientific papers.

In the context of PDS, the DOIs follows this workflow:
- reserve: before a dataset is published in PDS, a DOI can be reserved so that the researchers working with the digital resource at early stage can cite it in their papers. This step is optional.
- draft: the metadata associated to the DOI is elaborated and validated.
- release: the offcial DOI is registered at `OSTI`_ and `dataCite`_.
- deactivate (To Be Done): although it is not supposed to happen, due to error in the release one might deactivate a  DOI.

The reserve, draft and release steps can be repeated multiple time to update a DOI metadata.

The inputs to the DOI creation are either PDS4 labels or ad hoc spreadsheets (for the reserve step).

The metadata managed with DOIs is meant to be preserved and traceable as it is used to permanently cite a digital resource.
For this reason all the transactions, creations, updates with the PDS DOI management system are registered in a database.

Currently the tool provided is activated with a command line and used by a PDS Engineering Node operator interacting with the Discipline Nodes.
A later version will provide a web API, a web UI and a cmd API client to enable Discipline Nodes to directly manage their DOIs.

Usage Information
-----------------

.. argparse::
   :module: pds_doi_service.core.actions
   :func: create_parser
   :prog: pds-doi-cmd


.. _OSTI: https://www.osti.gov/data-services
.. _dataCite: https://datacite.org
