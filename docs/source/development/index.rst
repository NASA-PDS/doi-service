👩‍💻 Development
=================

Quick start
-----------

Get the code, work on a new branch::

    git clone https://github.com/NASA-PDS/pds-doi-service.git
    git checkout -b "#<issue number>"

Create a virtual environment in ``venv`` using python 3.7 or later::

    python3 -m venv venv

Install dependencies::

    venv/bin/pip install --requirement requirements.txt

and make it ready for development::

    venv/bin/pip install --editable .

At this point, we will have the command line tools available in ``venv/bin``
as explained in usage.

.. note::
    "Activating" the virtual environment is deprecated, as per the Python
    philosophy of "explict > implicit". Instead, invoke the commands directly
    in ``venv/bin``


Testing
-------

The code base finally includes unit and integration tests. Once you've built
out, you can run the unit tests:

    venv/bin/pip install pytest
    venv/bin/pytest

You can run the integration tests with:

    venv/bin/behave


Making Releases
---------------

The release is done on GitHub and PyPI. This is implemented through the CI/CD framework using GitHub Actions_ on the master branch.


Contribute
----------

Fork the code from : https://github.com/NASA-PDS/pds-doi-service and then create a pull request when done.

.. _Actions: https://github.com/features/actions
