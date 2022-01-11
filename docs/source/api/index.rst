️Command Line API
=================

This section contains details on the interfaces for the command line tools.

pds-doi-cmd
-----------

.. argparse::
   :module: pds_doi_service.core.actions.action
   :func: create_parser
   :prog: pds-doi-cmd

pds-doi-init
------------

.. argparse::
    :module: pds_doi_service.core.util.initialize_production_deployment
    :func: create_cmd_parser
    :prog: pds-doi-init

Swagger API
===========

This section contains details Swagger REST API implemented by ``pds-doi-api``.

.. raw:: html
    :file: ../_static/swagger.html


.. _Readme: https://github.com/NASA-PDS/doi-ui#readme
.. _DataCite: https://datacite.org
