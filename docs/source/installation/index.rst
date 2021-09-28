📦 Installation
===============

This section describes how to install the PDS DOI Service.

The service is composed of a command line tool (``pds-doi-cmd``) and a web API
(``pds-doi-api``) which provides an interface to the command line that may be
accessed remotely or via web UI.


Requirements
------------

Prior to installing this software, ensure your system meets the following
requirements:

•  Python_ 3.9 or above. Python 2 will absolutely *not* work.
•  ``libxml2`` version 2.9.2; later 2.9 versions are fine.  Run ``xml2-config
   --version`` to find out.

Consult your operating system instructions or system administrator to install
the required packages. For those without system administrator access, you
can use a local Python_ 3 installation using a `virtual environment`_
installation.


Installation Instructions
-------------------------

This section documents the installation procedure.

Installation
^^^^^^^^^^^^

The easiest way to install this software is to use Pip_, the Python Package
Installer. If you have Python on your system, you probably already have Pip;
you can run ``pip3 --help`` to check. Then run::

    pip3 install pds-doi-service

..  note::

    The above command will install latest approved release.
    To install a prior release, you can run::

        pip3 install pds-doi-service==<version>

    The released versions are listed on: https://pypi.org/project/pds-doi-service/#history

    If you want to use the latest unstable version, refer to the `development`_ documentation

If you don't want the package dependencies to interfere with your local system
you can use a `virtual environment`_  for your deployment.
To do so::

    mkdir -p $HOME/.venv
    python3 -m venv $HOME/.venv/pds-doi-service
    pip3 install pds-doi-service

At this point, the PDS DOI Service commands are available in
``$HOME/.venv/pds-doi-service/bin``.

.. note::
    "Activating" the virtual environment is deprecated, as per the Python
    philosophy of "explict > implicit". Instead, invoke the commands directly
    in ``$HOME/.venv/pds-doi-service/bin``


Configuration
^^^^^^^^^^^^^
The PDS DOI Service utilizes an INI file for its configuration. While there is a
default configuration file bundled with the service, it may be superseded by
a user-provided configuration within the installation directory.

To determine the appropriate location for a user configuration file, run the
following::

    python -c "import sys;print(sys.prefix)"

Within the directory returned, create a file named ``pds_doi_service.ini``.

In this file you can override any option set in the default configuration file
``pds_doi_service/core/util/conf.ini.default`` found within the package. An
example of this file may be found
`here <https://raw.githubusercontent.com/NASA-PDS/pds-doi-service/main/src/pds_doi_service/core/util/conf.ini.default>`_.

For example, if you want the service to create production DOIs, update the
DataCite server url::

   [DATACITE]
   url = https://api.datacite.org/dois

In order for the service to do any communication with the DataCite server, You
**MUST** set the appropriate username and password to be able to reserve or
release a DOI::

    [DATACITE]
    user = <username>
    password = <password>

Send a request to pds-operator@jpl.nasa.gov if proper credentials are needed.

The PDS DOI service uses a local database and file system space to store transactions.
The default location for these files is the installation location (``sys.prefix``),
however, it can be updated as follows in the configuration::

    [OTHER]
    transaction_dir = <directory absolute path>
    db_file = <database absolute path>/doi.db


You can also change the logging level by changing the configuration::

    [OTHER]
    logging_level = DEBUG

Authorized values are ``DEBUG``, ``INFO``, ``WARNING`` and ``ERROR`` (case-insensitive)...
(see https://docs.python.org/3/library/logging.html#logging-levels)


Running the service via command line tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once installed, you can run ``pds-doi-cmd --help`` to get a usage message and ensure
the service is properly installed. You can then consult the `usage`_ documentation
for more details.


Running the service via Web API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can start the web API service with command line ``pds-doi-api``.

You can explore the API documentation and test it using its built-in Swagger UI.
To access the test UI, navigate to http://localhost:8080/PDS_APIs/pds_doi_api/0.2/ui/
using a web-browser on the same machine that is running the API service.

..  note::

    In order to access the built-in Swagger UI, there must **not** be any value
    set for the ``OTHER.api_valid_referrers`` section of the INI config. To
    ensure the value is not set, add the following the user configuration file
    described in the Configuration section above::

        [OTHER]
        api_valid_referrers =


Upgrading the Service
---------------------

To check for and install an upgrade to the service, run the following command in
your virtual environment::

  pip install --upgrade pds-doi-service


.. References:
.. _usage: ../usage/index.html
.. _development: ../development/index.html
.. _Pip: https://pip.pypa.io/en/stable/
.. _Python: https://www.python.org/
.. _`virtual environment`: https://docs.python.org/3/library/venv.html
.. _Buildout: http://www.buildout.org/
.. _Cheeseshop: https://pypi.org/
.. _Miniconda: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
