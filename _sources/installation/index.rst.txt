📦 Installation
===============

This section describes how to install the PDS DOI Service.


Requirements
------------

Prior to installing this software, ensure your system meets the following
requirements:

•  Python_ 3. This software requires Python 3; it will work with 3.6, 3.7, or
   3.8.  Python 2 will absolutely *not* work.
•  ``libxml2`` version 2.9.2; later 2.9 versions are fine.  Run ``xml2-config
   --version`` to find out.

Consult your operating system instructions or system administrator to install
the required packages. For those without system administrator access and are 
feeling anxious, you could try a local (home directory) Python_ 3 installation 
using a Miniconda_ installation.


Doing the Installation
----------------------

The easiest way to install this software is to use Pip_, the Python Package
Installer. If you have Python on your system, you probably already have Pip;
you can run ``pip3 --help`` to check. Then run::

    pip3 install pds-doi-core

If you don't want the package dependencies to interfere with your local system
you can also use a `virtual environment`_  for your deployment.
To do so::

    mkdir -p $HOME/.virtualenvs
    python3 -m venv $HOME/.virtualenvs/pds-deep-archive
    source $HOME/.virtualenvs/pds-deep-archive/bin/activate
    pip3 install pds.deeparchive


Update the configuration
^^^^^^^^^^^^^^^^^^^^^^^^
In the python installation directory, that you can find with command::

    python -c "import sys;print(sys.prefix)"

Create a file `pds-doi-core/conf.ini`

You can override in this file any option set in the file `pds-doi-core/conf.ini.default`

You MUST set the OSTI service user and password to be able to reserve or release a DOI::

    [OSTI]
    user = <username>
    password = <password>

Ask the code to pds-operator@jpl.nasa.gov






You can then run ``pds-doi-cmd --help`` to get a usage message and ensure
it's properly installed. You can go to the `usage`_ documentation for details.


..  note::

    The above commands will install last approved release.
    To install former releases, you can do:

    pip install pds-doi-core==<version>

    The released versions are listed on: https://pypi.org/project/pds-doi-core/#history

    If you want to use the latest unstable version, you can refer to the `development`_ documentation

Upgrade Software
----------------

To check and install an upgrade to the software, run the following command in your 
virtual environment::

  source $HOME/.virtualenvs/pds-deep-archive/bin/activate
  pip install pds-doi-core --upgrade


.. References:
.. _usage: ../usage/index.html
.. _development: ../development/index.html
.. _Pip: https://pip.pypa.io/en/stable/
.. _Python: https://www.python.org/
.. _`virtual environment`: https://docs.python.org/3/library/venv.html
.. _Buildout: http://www.buildout.org/
.. _Cheeseshop: https://pypi.org/
.. _Miniconda: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
