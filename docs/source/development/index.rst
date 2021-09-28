👩‍💻 Development
=================

Quick start
-----------

To obtain a copy of the code and work on a new branch::

    git clone https://github.com/NASA-PDS/pds-doi-service.git
    git checkout -b "<issue number>_<issue name>"

Create a virtual environment in ``venv`` using Python 3.9 or later::

    python3 -m venv venv

Install the package and its dependencies for development into the virtual environment::

    pip install --editable '.[dev]'

At this point, the command line tools are now available in ``venv/bin``
as explained in `usage`_.

.. note::
    "Activating" the virtual environment is deprecated, as per the Python
    philosophy of "explict > implicit". Instead, invoke the commands directly
    in ``venv/bin``


Testing
-------

The code base includes both unit and integration tests. Once you've installed
the service, you can run the unit tests with the following command:

    venv/bin/tox py39

You can run the integration tests with:

    venv/bin/behave


Making Releases
---------------

Releases are done on GitHub and PyPI. This is implemented through the CI/CD
framework using GitHub Actions_ on the ``main`` branch. To trigger a release
via the CI/CD framework, create a branch named ``release/<version number>``,
and push it to the GitHub origin (https://github.com/NASA-PDS/pds-doi-service.git)
to trigger the Actions_ framework for release, for example::

    git checkout -b release/1.2
    git push --set-upstream origin release/1.2

From there, the Actions_ framework will determine an appropriate patch version
number, tag and build a release, and push it to PyPI.

Contribute
----------

Clone the repo from : https://github.com/NASA-PDS/pds-doi-service and then
submit a pull request for your branch when complete. At least one PDS Engineering
Node developer must approve the request before it is merged.

.. _usage: ../usage/index.html
.. _Actions: https://github.com/features/actions
