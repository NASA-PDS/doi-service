📦 Installation
===============

This section describes how to install the PDS DOI Service.

The service is compose by a command line tool and a web API (which enable to activate the command line remotelly or via a web UI)


Requirements
------------

Prior to installing this software, ensure your system meets the following
requirements:

•  Python_ 3.7 or above. Python 2 will absolutely *not* work.
•  ``libxml2`` version 2.9.2; later 2.9 versions are fine.  Run ``xml2-config
   --version`` to find out.

Consult your operating system instructions or system administrator to install
the required packages. For those without system administrator access and are
feeling anxious, you could try a local (home directory) Python_ 3 installation
using a Miniconda_ installation.


Doing the Installation
----------------------

This setion tells how to do the installation.

Install
^^^^^^^

The easiest way to install this software is to use Pip_, the Python Package
Installer. If you have Python on your system, you probably already have Pip;
you can run ``pip3 --help`` to check. Then run::

    pip3 install pds-doi-service

If you don't want the package dependencies to interfere with your local system
you can also use a `virtual environment`_  for your deployment.
To do so::

    mkdir -p $HOME/.virtualenvs
    python3 -m venv $HOME/.virtualenvs/pds-doi-service
    pip3 install pds-doi-service

At this point, the PDS DOI Service commands are available in
``$HOME/.virtualenvs/pds-doi-service/bin``.

.. note::
    "Activating" the virtual environment is deprecated, as per the Python
    philosophy of "explict > implicit". Instead, invoke the commands directly
    in ``$HOME/.virtualenvs/pds-doi-service/bin``



Configure
^^^^^^^^^
In the python installation directory, that you can find with command::

    python -c "import sys;print(sys.prefix)"

Create a file ``pds_doi_service.ini``.

You can override in this file any option set in the file ``pds_doi_service/core/util/conf.ini.default`` found in package.

If you want to create production DOIs update the OSTI API server url::

   [OSTI]
    url = https://www.osti.gov/iad2/api/records

You MUST set the OSTI service user and password to be able to reserve or release a DOI::

    [OSTI]
    user = <username>
    password = <password>

Ask the code to pds-operator@jpl.nasa.gov

The tool uses a local database and file system space to store transactions. The default location for these files is the sys.prefix, however it can be updated as follow in the configuration::

    [OTHER]
    transaction_dir = <directory absolute path>
    db_file = <database absolute path>/doi.db


You can also change the log level by changing the configuration::

    [OTHER]
    logging_level=DEBUG

Authorized values are DEBUG, INFO, ERROR... (see https://docs.python.org/3/library/logging.html#logging-levels)



Start using the command line tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can then run ``pds-doi-cmd --help`` to get a usage message and ensure
it's properly installed. You can go to the `usage`_ documentation for details.


..  note::

    The above commands will install last approved release.
    To install former releases, you can do:

    pip install pds-doi-core==<version>

    The released versions are listed on: https://pypi.org/project/pds-doi-core/#history

    If you want to use the latest unstable version, you can refer to the `development`_ documentation


Start the API server
^^^^^^^^^^^^^^^^^^^^

You can simply start the web API  service with command line ``pds-doi-api``.

You can explore the API documentation and test it from its UI: http://localhost:8080/PDS_APIs/pds_doi_api/0.1/ui/




Upgrade Software
----------------

To check and install an upgrade to the software, run the following command in your
virtual environment::

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
