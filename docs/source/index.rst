PDS DOI Service
===============

The Planetary Data System (PDS_) Digital Object Identifier (DOI_) Service
enable management of DOIs for PDS with the following operations: reserve,
draft, release, deactivate.

The PDS DOIs are registered through the `OSTI`_ infrastructure. OSTI registers
PDS DOI on `DataCite`_ infrastructure.

Currently, this service can be deployed as a python package
``pds-doi-service`` and is executed locally through a command line
``pds-doi-cmd`` or remotely through a web API server.


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   installation/index
   usage/index
   development/index
   support/index


.. _OSTI: https://www.osti.gov/data-services
.. _dataCite: https://datacite.org
.. _DOI: https://doi.org/
.. _PDS: https://pds.nasa.gov/
